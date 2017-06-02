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
from kindle_parser import ClipsParser


app = Flask(__name__)

app.config.from_pyfile('config.py')
app.config.from_envvar('CLINDLE_SETTING', silent=True)


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
    return render_template('index.html', books=books, jsonname=jsonname)


@app.errorhandler(413)
def entity_too_large(error):
    flash('File size are too large!')
    return redirect(url_for('index')), 413

# ------File upload------
# --原生方法实现文件上传--


# 判断文件格式是否允许
def ext_allowed(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/upload', methods=['POST'])
def upload():
    """
    上传'My Clippings.txt'文档，根据日期重命名，
    并保存至本地'backup_file'文件夹；
    调用解析函数，将解析内容存入数据库和json文件；然后刷新索引页面。
    Upload 'My Clippings.txt' file, rename according to datetime,
    and save to local 'backup_file' folder.
    Call the parsing function and save parsed content to database and jsonfile.
    Then refresh the webpage.
    """
    if request.method == 'POST' and 'txt_file' in request.files:
        f = request.files['txt_file']
        # if user submit without selecting a file,
        # browser will submit an empty part without filename.
        if f.filename == '':
            flash('请选择要上传的文件。')
            return redirect(url_for('index'))
        if f and ext_allowed(f.filename):
            # 使用pypinyin将中文转换为拼音字母
            f_name = secure_filename(''.join(lazy_pinyin(f.filename)))
            # 根据日期&时间重命名文件
            f_rename = ''.join(
                [datetime.now().strftime('%Y%m%d_%H%M%S_'), f_name])
            f_path = os.path.join(app.config['UPLOAD_FOLDER'], f_rename)
            f.save(f_path)
            flash('文件上传成功。')
            return redirect(url_for('index'))
        elif not ext_allowed(f.filename):
            flash('文件格式不支持！')
            return redirect(url_for('index'))
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
