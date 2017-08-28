#coding:utf8
from tools import randstr


DATABASE = 'db/user.db'       # 数据库文件位置
DEBUG = True                  # 调试模式
SECRET_KEY = randstr(15)      # 会话密钥
UPLOAD_FOLDER = './SavedIcs'
QR_FOLDER = 'img/'
HOST = '0.0.0.0'
SERVER_DOMAIN_NAME = 'app.lovecrislovetim.com/'
