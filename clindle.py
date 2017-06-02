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
from datetime import datetime
from pypinyin import lazy_pinyin
from flask import Flask, request, session, redirect, url_for, abort, \
     render_template, flash
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


@app.route('/')
def index():
    # 临时性解决方式 -- not lasting --
    jsonfiles = os.listdir(app.config['JSONFILE_FOLDER'])
    jsonfiles.remove('.gitkeep')
    if jsonfiles:
        jsonname = jsonfiles[0]
        jsonfile = os.path.join(app.config['JSONFILE_FOLDER'], jsonname)
        with open(jsonfile, 'r') as f:
            book_clips = json.load(f)
            books = list(book_clips.keys())
    else:
        books = None

    form = UploadForm()
    return render_template('index.html', books=books, form=form, jsonname=jsonname)


@app.errorhandler(413)
def entity_too_large(error):
    flash('File size are too large!')
    return redirect(url_for('index')), 413

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
    Call the parsing function and save parsed content to json file and database.
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
            kindleparser.parse()
            flash('文件上传成功。')
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
