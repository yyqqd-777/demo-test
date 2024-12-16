from flask import Flask, render_template, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 最大文件限制

# 确保上传文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS files
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         filename TEXT NOT NULL,
         original_filename TEXT NOT NULL,
         description TEXT,
         category TEXT,
         upload_date DATETIME,
         file_path TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM files ORDER BY upload_date DESC')
    files = c.fetchall()
    conn.close()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            description = request.form.get('description', '')
            category = request.form.get('category', '')
            
            # 生成唯一文件名
            unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # 保存文件
            file.save(file_path)
            
            # 保存到数据库
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO files (filename, original_filename, description, category, upload_date, file_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (unique_filename, filename, description, category, datetime.now(), file_path))
            conn.commit()
            conn.close()
            
            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/download/<int:file_id>')
def download(file_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT file_path, original_filename FROM files WHERE id = ?', (file_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return send_file(result[0], as_attachment=True, download_name=result[1])
    return "文件未找到", 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)