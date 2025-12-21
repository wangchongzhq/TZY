#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具 - Web界面
"""

import os
import tempfile
from flask import Flask, request, render_template_string, send_file, flash
from iptv_validator import IPTVValidator, validate_file

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'iptv_validator_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB文件大小限制

# 支持的文件类型
ALLOWED_EXTENSIONS = {'m3u', 'm3u8', 'txt'}

# 检查文件类型是否被允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Web界面模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>直播源有效性验证工具</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="file"], input[type="text"], select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            resize: vertical;
            height: 150px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            background-color: #f0f8ff;
            border-radius: 4px;
            border-left: 5px solid #008080;
        }
        .error {
            background-color: #ffebee;
            border-left-color: #f44336;
        }
        .success {
            background-color: #e8f5e9;
            border-left-color: #4CAF50;
        }
        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 15px;
            background-color: #2196F3;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .download-link:hover {
            background-color: #0b7dda;
        }
        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            margin-bottom: 20px;
        }
        .tab button {
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            color: #333;
            margin-right: 0;
        }
        .tab button:hover {
            background-color: #ddd;
        }
        .tab button.active {
            background-color: #ccc;
        }
        .tabcontent {
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
        }
    </style>
</head>
<body>
    <h1>直播源有效性验证工具</h1>
    <div class="container">
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'FileUpload')">文件上传</button>
            <button class="tablinks" onclick="openTab(event, 'UrlInput')">URL输入</button>
        </div>

        <!-- 文件上传标签页 -->
        <div id="FileUpload" class="tabcontent" style="display: block;">
            <form method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="file">选择直播源文件 (.m3u, .m3u8, .txt)</label>
                    <input type="file" id="file" name="file" accept=".m3u,.m3u8,.txt" required>
                </div>
                <div class="form-group">
                    <label for="workers">并发工作线程数</label>
                    <input type="text" id="workers" name="workers" value="20">
                </div>
                <div class="form-group">
                    <label for="timeout">超时时间（秒）</label>
                    <input type="text" id="timeout" name="timeout" value="5">
                </div>
                <button type="submit" name="upload">开始验证</button>
            </form>
        </div>

        <!-- URL输入标签页 -->
        <div id="UrlInput" class="tabcontent">
            <form method="post">
                <div class="form-group">
                    <label for="urls">输入直播源URL（每行一个）</label>
                    <textarea id="urls" name="urls" placeholder="频道名称1,http://example.com/stream1.m3u8
频道名称2,http://example.com/stream2.m3u8"></textarea>
                </div>
                <div class="form-group">
                    <label for="category">分类名称</label>
                    <input type="text" id="category" name="category" value="默认分类">
                </div>
                <div class="form-group">
                    <label for="workers2">并发工作线程数</label>
                    <input type="text" id="workers2" name="workers2" value="20">
                </div>
                <div class="form-group">
                    <label for="timeout2">超时时间（秒）</label>
                    <input type="text" id="timeout2" name="timeout2" value="5">
                </div>
                <button type="submit" name="validate_urls">开始验证</button>
            </form>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="result {{ category }}">{{ message|safe }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tabcontent");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
            }
            tablinks = document.getElementsByClassName("tablinks");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # 处理文件上传
            if 'upload' in request.form:
                file = request.files['file']
                if file and allowed_file(file.filename):
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(file.filename)[1], delete=False) as temp:
                        file.save(temp.name)
                        temp_path = temp.name
                    
                    try:
                        # 获取参数
                        workers = int(request.form.get('workers', 20))
                        timeout = int(request.form.get('timeout', 5))
                        
                        # 生成输出文件路径到output目录
                        output_filename = os.path.join('output', f"{os.path.splitext(os.path.basename(file.filename))[0]}_valid{os.path.splitext(file.filename)[1]}")
                        
                        # 验证文件
                        output_file = validate_file(temp_path, output_filename, max_workers=workers, timeout=timeout)
                        
                        if output_file:
                            # 生成下载链接
                            flash(f'验证完成！有效频道数: {sum(1 for line in open(output_file) if not line.startswith("#") and line.strip())}', 'success')
                            flash(f'<a href="/download/{os.path.basename(output_file)}" class="download-link">下载有效直播源文件</a>', 'success')
                        else:
                            flash('没有找到有效的直播源', 'error')
                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                else:
                    flash('不支持的文件格式，请上传.m3u、.m3u8或.txt文件', 'error')
            
            # 处理URL输入
            elif 'validate_urls' in request.form:
                urls_text = request.form.get('urls', '')
                category = request.form.get('category', '默认分类')
                workers = int(request.form.get('workers2', 20))
                timeout = int(request.form.get('timeout2', 5))
                
                if not urls_text.strip():
                    flash('请输入直播源URL', 'error')
                else:
                    # 创建临时M3U文件
                    with tempfile.NamedTemporaryFile(suffix='.m3u', delete=False) as temp:
                        temp.write(b'#EXTM3U\n')
                        for line in urls_text.strip().split('\n'):
                            line = line.strip()
                            if line and ',' in line:
                                name, url = line.split(',', 1)
                                temp.write(f'#EXTINF:-1 group-title="{category}",{name.strip()}\n{url.strip()}\n'.encode('utf-8'))
                        temp_path = temp.name
                    
                    try:
                        # 生成输出文件路径到output目录
                        output_filename = os.path.join('output', 'custom_urls_valid.m3u')
                        
                        # 验证文件
                        output_file = validate_file(temp_path, output_filename, max_workers=workers, timeout=timeout)
                        
                        if output_file:
                            # 生成下载链接
                            flash(f'验证完成！有效频道数: {sum(1 for line in open(output_file) if not line.startswith("#") and line.strip())}', 'success')
                            flash(f'<a href="/download/{os.path.basename(output_file)}" class="download-link">下载有效直播源文件</a>', 'success')
                        else:
                            flash('没有找到有效的直播源', 'error')
                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
        
        except Exception as e:
            flash(f'验证过程中发生错误: {str(e)}', 'error')
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/download/<filename>')
def download_file(filename):
    # 确保只允许下载验证工具生成的有效文件
    safe_filename = os.path.basename(filename)  # 防止路径遍历攻击
    file_path = os.path.join('output', safe_filename)
    if os.path.exists(file_path) and (file_path.endswith('_valid.m3u') or file_path.endswith('_valid.txt')):
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    else:
        flash('文件不存在或不允许下载', 'error')
        return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # 确保输出目录存在
    if not os.path.exists('output'):
        os.makedirs('output')
    
    # 启动Web服务
    app.run(debug=True, port=5000, host='0.0.0.0')
