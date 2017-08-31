import os, sqlite3,hashlib,json
from flask import Flask, request, redirect, url_for, abort, send_from_directory,g,session,render_template,make_response
from werkzeug import secure_filename
import xls2ics,config
from tools import randstr
import qrcode



app = Flask(__name__)
app.config.from_object('config')

if not app.debug:
    import logging  
    import logging.config  
    logging.config.fileConfig('logging_config.ini')
    logger = logging.getLogger('root')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('cover.html')
    
    if 'qr_path' in session:
        return render_template('qr.html',qr_path = session['qr_path'])
    else:
        return render_template('index.html')



@app.route('/process',methods=['GET','POST'])
def process():
    if request.method == 'POST':
        file = request.files['file']
        
        if file :
            xls_dict = {
                    'campus':request.form['area'],\
                    'term_season':'fail',\
                    'term_year':'2017'}

            file_content = file.read()
            md5 = calMd5(file_content,xls_dict)
           
            
            cursor = g.db.cursor()
            cursor.execute('select md5 from files_info where md5=?',(md5,))
            md5_exists = cursor.fetchall()

            url = ''
            errorcode = 0
            title = ''
            if not md5_exists:
                try:
                    cal = handleXls(file_content,xls_dict,md5)
                    title = cal.getTitle()
                    url = randstr(10, url_safe=True)
                    
                    with open(os.path.join(app.config['UPLOAD_FOLDER'], md5),'w',encoding='utf-8') as f:
                        try:
                            f.writelines(cal.getIcs())
                        except Exception as e:
                            app.logger.error("ics saved failed")
                            raise e
                    cursor.execute('insert into files_info (md5,title,url) values (?,?,?)',(md5,title,url))
                    g.db.commit()
                except Exception as e:
                    app.logger.error(e)
                    errorcode = 1
                
            else:
                app.logger.info('file {} search in db'.format(md5))
                cursor.execute('select url,title from files_info where md5=?',(md5,))
                content = cursor.fetchall()
                url = content[0][0]
                title = content[0][1]
            
            qr = qrcode.make(url_for('scan_result',uuid=url, _external=True,))
            qr_id = secure_filename(randstr(13,url_safe=True) + '.png')

            ics_path = url_for('getit',uuid=url, _external=True,)
            qr_path = os.path.join(app.config['QR_FOLDER'],qr_id)
            session['qr_path'] = qr_path
            try:
                qr.save(qr_path)
            except Exception as e:
                app.logger.error("Qr img saved failed")
                raise e
            res = dict(errorcode= errorcode, qr_path= qr_path,ics_path=ics_path, title=title)
            response=make_response(json.dumps(res))
            response.headers['Content-Type']='application/json'
            return response
        else:
            abort(403)
    else:
        abort(404)



@app.route('/reupload')
def reupload():
    if 'qr_parh' in session:
        session.pop('qr_path',None)
    return redirect(url_for('index'))

@app.route('/getit')
def getit(**kw):
    url = request.args.get('uuid')
    print(url)
    cursor = g.db.cursor()
    cursor.execute('select md5,title from files_info where url=?',(url,))
    content = cursor.fetchall()
    if not content:
        abort(404)
    md5 = content[0][0]
    title = content[0][1] + '.ics'
    print(md5)
    response = make_response(send_from_directory(\
    app.config['UPLOAD_FOLDER'], md5,  \
    as_attachment=True, \
    attachment_filename=title))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(title.encode().decode('latin-1'))
    return response

@app.route('/ics')
def scan_result(**kw):
    url = request.args.get('uuid')
    return render_template('scan.html',url=url)

@app.route('/static/<id>')
def static_server(id):
    return send_from_directory(app.config['STATIC_FOLDER'],id)

@app.route('/img/<id>')
def showqr(id):
    id = secure_filename(id)
    return send_from_directory(app.config['QR_FOLDER'],id)


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

def handleXls(file, xls_dict,md5):
    '''输入文件二进制
        返回ics对象
    '''
    
    
    cal = xls2ics.XlsParser(xls_content=file,uid=md5)
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
    app.run('0.0.0.0')
    