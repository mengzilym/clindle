# -*- coding: utf-8 -*-
"""
Clindle
-------
A kindle clippings management application.
Copyright: (C) 2017 by Liu Yameng.
License: BSD, see LICENSE for more details.
"""

import os
import json
import math
import sqlite3
import sys
from datetime import datetime
from pypinyin import lazy_pinyin
from flask import Flask, flash, abort, g, redirect, render_template, \
    request, session, url_for
from werkzeug.utils import secure_filename
from flask_uploads import UploadSet, TEXT, configure_uploads, \
    patch_request_class, UploadNotAllowed
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from kindle_parser import ClipsParser
# from config import *


app = Flask(__name__)

app.config.from_pyfile('config.py')
# 或许需要加载独立的、根据环境而变化的配置文件
app.config.from_envvar('FLASK_SETTINGS', silent=True)


# 数据库操作函数
def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """如果当前应用上下文没有数据库连接，
    则打开一个新的数据库连接。"""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
        return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """在request结束的时候再次close数据库连接"""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# 初始化数据库
def init_db():
    """根据数据库的schema创建数据库。"""
    conn = get_db()
    with app.open_resource('schema.sql', 'r') as f:
        conn.cursor().executescript(f.read())
    conn.commit()


@app.cli.command('initdb')
def initdb_comd():
    """初始化数据库"""
    init_db()


# 创建upload set并注册配置
clipstxt = UploadSet('clipstxt', TEXT)
configure_uploads(app, clipstxt)
# 限制文件大小，同 MAX_CONTENT_LENGTH
patch_request_class(app, None)


# 设置flask_wtf上传表单
class UploadForm(FlaskForm):
    clipsfile = FileField(validators=[
        FileRequired('wtf:请选择文件'),
        FileAllowed(clipstxt, 'wtf:出错，请检查上传文件格式。')])
    submit = SubmitField('上传')


@app.errorhandler(413)
def entity_too_large(error):
    flash('File size are too large!')
    return redirect(url_for('index')), 413


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# utilities
# 将‘标注’存储至数据库
def save2db(clips):
    """将解析得到的clips字典对象，保存到数据库中。
    每次重新上传'My Clippings.txt'时，重新创建数据库里的表。
    问题：如果要“获取封面”，可以考虑建立一个缓存文件夹，缓存之前已经获取到的封面图片
    """
    error = None
    conn = get_db()
    cur = conn.cursor()

    with app.open_resource('schema.sql', 'r') as f:
        cur.executescript(f.read())

    def _titles():
        for title in clips.keys():
            yield (title,)
    try:
        # 将书籍名称存入Books表中
        cur.executemany('insert into Books(title) values(?);', _titles())
        # Insert values into Clips, Notes, Marks tables.
        for title, clipsofonebook in clips.items():
            cur.execute('select id from Books where title = ?;', (title,))
            bookid = cur.fetchone()[0]
            notes = {}
            for clip in clipsofonebook.values():
                # save '标注' clips to Clips table.
                # warning: the 'content' of '标注' can be 'null' :<
                if clip['type'] == '标注':
                    cur.execute(
                        'insert into Clips values(null, ?, ?, ?, ?, ?);',
                        (clip['pos'], clip['index_pos'], clip['time'],
                         clip['content'], bookid))
                # save '书签' clips to Marks table.
                elif clip['type'] == '书签':
                    cur.execute(
                        'insert into Marks values(null, ?, ?, ?, ?);',
                        (clip['pos'], clip['index_pos'], clip['time'], bookid))
                else:
                    notes[clip['time']] = clip
            # save '笔记' clips to Notes table.
            if notes:
                for t, clip in notes.items():
                    cur.execute('select id from Clips where time = ?;', (t,))
                    clipid = cur.fetchone()[0]
                    cur.execute(
                        'insert into Notes values(null, ?, ?, ?, ?, ?);',
                        (clip['pos'], clip['time'], clip['content'],
                         bookid, clipid))
    except sqlite3.Error:
        conn.rollback()
        error = ('Failed to save data to database :(')
    conn.commit()
    conn.close()
    return error


# collation function
def collate_pinyin(t1, t2):
    """working with 'order by' in sql statement,
    making it possible to order by chinese characters.
    """
    py_t1 = ''.join(lazy_pinyin(t1))
    py_t2 = ''.join(lazy_pinyin(t2))
    if py_t1 == py_t2:
        return 0
    elif py_t1 < py_t2:
        return -1
    else:
        return 1


# 视图函数 view functions
@app.route('/', defaults={'page': 1})
@app.route('/page/<int:page>')
def index(page):
    conn = get_db()
    cur = conn.cursor()
    conn.create_collation('pinyin', collate_pinyin)

    # pagination
    # use "try" expression in case there are no tables at all
    # before uploading text document.
    try:
        # get the count of books
        cur.execute('select count(title) from Books;')
        book_count = cur.fetchone()[0]
        # number of pagination
        page_count = math.ceil(book_count / app.config['PER_PAGE'])
        if page not in range(1, page_count + 1):
            abort(404)
    except sqlite3.Error:
        page_count = 0
        if page != 1:
            abort(404)

    # get only fixed number of records as specified by 'PER_PAGE' from database
    try:
        cur.execute(
            'select id, title from Books '
            'order by title collate pinyin limit ? offset ?;',
            (app.config['PER_PAGE'], app.config['PER_PAGE'] * (page - 1)))
        books = cur.fetchall()
    except sqlite3.Error:
        books = {}

    form = UploadForm()
    return render_template('index.html', books=books, form=form,
                           page=page, page_count=page_count)


@app.route('/book/<int:book_id>')
def show_clips(book_id):
    """return clips/notes/marks of one book.
    """
    conn = get_db()
    cur = conn.cursor()
    # get clips and associated notes.
    cur.execute(
        'select c.pos, c.time, c.content as clipcnt, n.content as notecnt '
        'from Clips as c left join Notes as n '
        'on c.id = n.clipid '
        'where c.bookid = ? order by indexpos;',
        (book_id,))
    clips = cur.fetchall()
    cur.execute('select title from Books where id = ?;', (book_id,))
    title = cur.fetchone()
    if title:
        title = title[0]
    else:
        abort(404)
    # get marks if any.
    cur.execute(
        'select pos, time from Marks where bookid = ? order by indexpos;',
        (book_id,))
    marks = cur.fetchall()

    return render_template('bookclips.html', clips=clips,
                           title=title, marks=marks)


# ------File upload------
# --使用flask-uploads扩展上传文件--
@app.route('/upload', methods=['POST'])
def upload():
    """
    上传'My Clippings.txt'文档，根据日期重命名，
    并保存至本地'backup_file'文件夹；
    调用解析函数，将解析内容存入json文件和数据库；然后刷新索引页面。
    Upload 'My Clippings.txt' file, rename according to datetime,
    and save to local 'backup_file' folder.
    Use parsing function and save parsed content to json file and database.
    Then refresh the webpage.
    """
    form = UploadForm()
    if form.validate_on_submit():
        try:
            f = form.clipsfile.data
            # 使用pypinyin将中文转换为拼音字母
            f_name = secure_filename(''.join(lazy_pinyin(f.filename)))
            # 根据日期&时间重命名文件
            f_rename = ''.join(
                [datetime.now().strftime('%Y%m%d_%H%M%S_'), f_name])
            filename = clipstxt.save(f, name=f_rename)
            kindleparser = ClipsParser(filename)
            clips = kindleparser.parse()
            error = save2db(clips)
            if error:
                flash('Upload success. But:<br> {}'.format(error))
            else:
                flash('Upload success.')
        except UploadNotAllowed:
            # 经过上面form.validate_on_submit()，下面这两句应该不会执行了
            flash('出错：UploadNotAllowed。<br>请检查文件格式是否正确。')
            return redirect(url_for('index'))
    else:
        for error in form.clipsfile.errors:
            flash(error)
    return redirect(url_for('index'))


# 获取书籍封面
# Get book covers.
# todo: 多线程
@app.route('/api/getcover')
def get_cover():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(
        debug=True,
        port=5000
    )
