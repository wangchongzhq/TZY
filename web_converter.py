#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_converter.py

具有Web界面的M3U/TXT双向转换器
支持 M3U ↔ TXT 双向转换
"""

import os
import sys
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime

# 导入现有的M3U转换器类
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from convert_m3u_to_txt import M3UConverter

# Flask应用初始化
app = Flask(__name__)

# 配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 最大上传大小
app.config['ALLOWED_EXTENSIONS'] = {'m3u', 'm3a', 'txt'}  # 支持M3U/M3A/TXT文件

# 创建必要的目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return render_template('index.html', error='未选择文件')
    
    file = request.files['file']
    
    # 检查文件名是否为空
    if file.filename == '':
        return render_template('index.html', error='未选择文件')
    
    # 获取转换方向
    direction = request.form.get('direction', 'm3u_to_txt')
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return render_template('index.html', error='只允许上传M3U/M3A/TXT格式的文件')
    
    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        # 上传文件使用时间戳避免冲突，但输出文件名保持原名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        # 根据转换方向生成输出文件名 - 保持原文件名，只改变扩展名
        name_without_ext = os.path.splitext(filename)[0]
        if direction == 'm3u_to_txt':
            output_filename = f"{name_without_ext}.txt"
            conversion_type = 'M3U → TXT'
        else:  # txt_to_m3u
            output_filename = f"{name_without_ext}.m3u"
            conversion_type = 'TXT → M3U'
        
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # 执行转换
        converter = M3UConverter()
        if direction == 'm3u_to_txt':
            success = converter.convert_m3u_to_txt(upload_path, output_path)
        else:  # txt_to_m3u
            success = converter.convert_txt_to_m3u(upload_path, output_path)
        
        if success:
            # 返回转换成功的页面，包含下载链接
            return render_template('index.html', success=True, output_filename=output_filename, 
                                 conversion_type=conversion_type, direction=direction)
        else:
            return render_template('index.html', error='转换失败，请检查文件格式')
            
    except Exception as e:
        return render_template('index.html', error=f'转换过程中发生错误：{str(e)}')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
