# -*- coding: utf-8 -*-

import os
from flask_uploads import TEXT

# app设置；app configures
DATABASE = os.path.join(os.getcwd(), 'data', 'clippings.db')
SECRET_KEY = 'development_key'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'backup_file')
JSONFILE_FOLDER = os.path.join(os.getcwd(), 'data', 'json')
COVERPIC_FOLDER = os.path.join(os.getcwd(), 'data', 'pics')
ALLOWED_EXTENSIONS = set(['txt'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# flask-uploads 扩展设置；flask-uploads extension configures
UPLOADED_CLIPSTXT_DEST = UPLOAD_FOLDER
UPLOADED_CLIPSTXT_ALLOW = TEXT
