import os, sqlite3,hashlib,qrcode
from flask import Flask, request, redirect, url_for, abort, send_from_directory,g,session,render_template
from werkzeug import secure_filename
import xls2ics,config
from tools import randstr
"""
import logging  
import logging.config  
import xls2ics

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger('root')
"""

ALLOWED_EXTENSIONS = set(['xls','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object('config')

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        
        if file and allowed_file(file.filename):
            
            
            xls_dict = {
                    'campus':request.form['area'],\
                    'term_season':request.form['term_season'],\
                    'term_year':request.form['term_year']}

            file_content = file.read()
            md5 = calMd5(file_content,xls_dict)
            print(md5)
            
            cursor = g.db.cursor()
            cursor.execute('select md5 from files_info where md5=?',(md5,))
            md5_exists = cursor.fetchall()
            url = ''
            
            if not md5_exists:
                
                cal = handleXls(file_content,xls_dict)
                title = cal.getTitle()
                url = randstr(10, url_safe=True)
                with open(os.path.join(app.config['UPLOAD_FOLDER'], md5),'w',encoding='utf-8') as f:
                    f.writelines(cal.getIcs())
                cursor.execute('insert into files_info (md5,title,url) values (?,?,?)',(md5,title,url))
                g.db.commit()
            else:
                cursor.execute('select url from files_info where md5=?',(md5,))
                url = cursor.fetchall()[0][0]
            
            qr = qrcode.make(url_for('gtics',uuid=url, _external=True,))
            qr_id = secure_filename(randstr(13,url_safe=True) + '.png')
            qr_path = os.path.join(app.config['QR_FOLDER'],qr_id)
            session['qr_path'] = qr_path
            qr.save(qr_path)
            
            return redirect('/',code=302)
        else:
            return '请重新选择文件格式'
    elif request.method == 'GET':
        if 'qr_path' in session:
            return render_template('qr.html',qr_path = session['qr_path'])
        else:
            return render_template('index.html')
    return 'hello'
    
@app.route('/reupload')
def reupload():
    if 'qr_parh' in session:
        session.pop('qr_path',None)
    return redirect(url_for('index'))

@app.route('/ics')
def gtics(**kw):
        url = request.args.get('uuid')
        print(url)
        cursor = g.db.cursor()
        cursor.execute('select md5 from files_info where url=?',(url,))
        md5 = cursor.fetchall()[0][0]
        print(md5)
        return send_from_directory(app.config['UPLOAD_FOLDER'], md5)
    


@app.route('/img/<id>')
def showqr(id):
    id = secure_filename(id)
    return send_from_directory(app.config['QR_FOLDER'],id)

@app.route('/finish_upload<filename>')
def finish_upload(filename):
	return ('finish_upload '+ filename)






@app.before_request
def before_request():
    get_db()
 
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def calMd5(file,xls_dict):
    '''计算文件及其附加参数的md5 
        输入文件二进制以及其他参数
        返回md5值(str)
    '''
    user_str = ''
    for i in xls_dict:
        user_str += str(i)
    md5 = hashlib.md5()
    md5.update(file)
    md5.update(user_str.encode('utf-8'))
    return md5.hexdigest()

def handleXls(file, xls_dict):
    '''输入文件二进制
        返回ics对象
    '''
    
    
    cal = xls2ics.XlsParser(xls_content=file)
    cal.campus = xls_dict['campus']
    
    '''#TODO
    cal.term_season = xls_dict['term_season']
    cal.term_year = xls_dict['term_year']
    '''
    return cal


#数据库基础函数
def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db(): #初始化数据库，人工执行
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

if __name__ == '__main__':
	app.run()
