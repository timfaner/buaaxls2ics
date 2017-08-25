import os
from flask import Flask, request, redirect, url_for
from werkzeug import secure_filename

import logging  
import logging.config  
import xls2ics

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger('root')

UPLOAD_FOLDER = '/Users/TimFan/Desktop'
ALLOWED_EXTENSIONS = set(['xls','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def uploaded_file():
    if request.method == 'POST':
        file = request.files['file']
        area = request.form['area']
        print(area)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)


            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('finish_upload',
                        filename=filename))
        else:
            return '请重新选择文件格式'
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
    <p><input type=file name=file>
    <select name="area">
    <option value="shahe">沙河</option>
    <option value="xueyuanlu">学院路</option>
    </select>
    <input type=submit value=Upload>
    </form>
'''

@app.route('/finish_upload<filename>')
def finish_upload(filename):
	return ('finish_upload '+ filename)


if __name__ == '__main__':
	app.run(debug=True,host='0.0.0.0')
