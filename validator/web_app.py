#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具 - Web界面
"""

import os
import tempfile
import logging
import threading
import base64
from flask import Flask, request, render_template_string, send_file, flash
from flask_socketio import SocketIO, emit
from iptv_validator import IPTVValidator, validate_file

# 配置日志记录
logging.basicConfig(
    filename='web_validation.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'iptv_validator_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB文件大小限制

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

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
    <title>IPTV直播源验证工具</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        h1 {
            color: #495057;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }
        
        /* 标签页样式 */
        .tab {
            display: flex;
            background: linear-gradient(135deg, #667eea 0%, #8e9bef 100%);
            border-bottom: 2px solid #e9ecef;
        }
        
        .tab button {
            flex: 1;
            background-color: inherit;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 18px 20px;
            transition: all 0.3s ease;
            color: white;
            font-size: 16px;
            font-weight: 500;
        }
        
        .tab button:hover {
            background-color: #e9ecef;
            color: #667eea;
        }
        
        .tab button.active {
            background-color: white;
            color: #495057;
            font-weight: 700;
            border-bottom: 3px solid #667eea;
        }
        
        /* 表单内容样式 */
        .tabcontent {
            display: none;
            padding: 30px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #495057;
            font-size: 14px;
        }
        
        input[type="file"], input[type="text"], textarea {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 14px;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }
        
        input[type="file"]:focus, input[type="text"]:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        textarea {
            resize: vertical;
            height: 150px;
            line-height: 1.6;
        }
        
        /* 按钮样式 */
        button {
            background: linear-gradient(135deg, #667eea 0%, #8e9bef 100%);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        
        /* 结果样式 */
        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 8px;
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        
        .error {
            background-color: #fff5f5;
            border-left-color: #e53e3e;
        }
        
        .success {
            background-color: #f0fff4;
            border-left-color: #38a169;
        }
        
        .download-link {
            display: inline-block;
            margin-top: 15px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(56, 161, 105, 0.3);
        }
        
        .download-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(56, 161, 105, 0.4);
        }
        
        /* 表格样式 */
        .table-container {
            overflow-x: auto;
            margin-top: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            max-height: 400px;
            overflow-y: auto;
        }
        
        .results-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        
        .results-table th, .results-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }
        
        .results-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        
        .results-table tbody tr {
            transition: background-color 0.3s ease;
        }
        
        .results-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        .results-table tbody tr:nth-child(even) {
            background-color: #fafbfc;
        }
        
        /* 状态样式 */
        .valid {
            color: #38a169;
            font-weight: 600;
        }
        
        .invalid {
            color: #e53e3e;
            font-weight: 600;
        }
        
        .resolution {
            font-family: 'Courier New', monospace;
            color: #667eea;
            font-weight: 600;
        }
        
        /* 链接样式 */
        a {
            color: #667eea;
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            h1 {
                font-size: 2em;
                margin-bottom: 20px;
            }
            
            .tab button {
                padding: 15px 10px;
                font-size: 14px;
            }
            
            .tabcontent {
                padding: 20px;
            }
            
            .results-table th, .results-table td {
                padding: 10px 8px;
                font-size: 13px;
            }
        }
        
        /* 加载动画 */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* 进度条样式 */
        .progress-container {
            margin: 25px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            color: #495057;
        }
        
        /* 进度统计样式 */
        .progress-stats {
            margin-top: 15px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        /* 控制按钮样式 */
        .control-buttons {
            display: flex;
            gap: 15px;
            margin-top: 25px;
            flex-wrap: wrap;
        }

        /* 实时状态样式 */
        .real-time-status {
            margin-top: 15px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .status-item {
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }
        
        .status-label {
            font-weight: 600;
            color: #495057;
        }
        
        .status-value {
            color: #667eea;
        }
    </style>
</head>
<body>
    <h1>直播源有效性验证工具</h1>
    <div class="container">
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'FileUpload')">文件上传</button>
            <button class="tablinks" onclick="openTab(event, 'UrlInput')">URL输入</button>
            <button class="tablinks" onclick="openTab(event, 'WebSource')">互联网直播源文件</button>
        </div>

        <!-- 文件上传标签页 -->
        <div id="FileUpload" class="tabcontent" style="display: block;">
            <form id="file-upload-form">
                <div class="form-group">
                    <label for="file">选择直播源文件 (.m3u, .m3u8, .txt)</label>
                    <input type="file" id="file" name="file" accept=".m3u,.m3u8,.txt" required>
                </div>
                <div class="form-group">
                    <label for="workers">并发工作线程数</label>
                    <input type="number" id="workers" name="workers" value="20" min="1" max="100">
                </div>
                <div class="form-group">
                    <label for="timeout">超时时间（秒）</label>
                    <input type="number" id="timeout" name="timeout" value="5" min="1" max="60">
                </div>
                <div class="control-buttons">
                    <button type="button" id="start-btn1" onclick="startFileValidation()">开始验证</button>
                    <button type="button" id="stop-btn1" onclick="stopValidation()" disabled>停止</button>
                    <button type="button" onclick="clearList()">清空列表</button>

                </div>
            </form>
        </div>

        <!-- URL输入标签页 -->
        <div id="UrlInput" class="tabcontent">
            <form id="url-input-form">
                <div class="form-group">
                    <label for="urls">输入直播源URL（每行一个）</label>
                    <textarea id="urls" name="urls" placeholder="频道名称1,http://example.com/stream1.m3u8\n频道名称2,http://example.com/stream2.m3u8"></textarea>
                </div>
                <div class="form-group">
                    <label for="category">分类名称</label>
                    <input type="text" id="category" name="category" value="默认分类">
                </div>
                <div class="form-group">
                    <label for="workers2">并发工作线程数</label>
                    <input type="number" id="workers2" name="workers2" value="20" min="1" max="100">
                </div>
                <div class="form-group">
                    <label for="timeout2">超时时间（秒）</label>
                    <input type="number" id="timeout2" name="timeout2" value="5" min="1" max="60">
                </div>
                <div class="control-buttons">
                    <button type="button" id="start-btn2" onclick="startUrlValidation()">开始验证</button>
                    <button type="button" id="stop-btn2" onclick="stopValidation()" disabled>停止</button>
                    <button type="button" onclick="clearList()">清空列表</button>

                </div>
            </form>
        </div>

        <!-- 互联网直播源文件标签页 -->
        <div id="WebSource" class="tabcontent">
            <form id="web-source-form">
                <div class="form-group">
                    <label for="source_url">输入互联网直播源文件URL (.m3u, .m3u8, .txt)</label>
                    <input type="text" id="source_url" name="source_url" placeholder="http://example.com/live_channels.m3u">
                </div>
                <div class="form-group">
                    <label for="workers3">并发工作线程数</label>
                    <input type="number" id="workers3" name="workers3" value="20" min="1" max="100">
                </div>
                <div class="form-group">
                    <label for="timeout3">超时时间（秒）</label>
                    <input type="number" id="timeout3" name="timeout3" value="5" min="1" max="60">
                </div>
                <div class="control-buttons">
                    <button type="button" id="start-btn3" onclick="startWebSourceValidation()">开始验证</button>
                    <button type="button" id="stop-btn3" onclick="stopValidation()" disabled>停止</button>
                    <button type="button" onclick="clearList()">清空列表</button>

                </div>
            </form>
        </div>

        <!-- 进度显示区域 -->
        <div id="progress-container" style="display: none; padding: 30px;">
            <div class="progress-container">
                <h3>验证进度</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-info">
                    <span id="progress-percentage">0%</span>
                    <span id="progress-stats">0/0 频道</span>
                </div>
                <div class="progress-stats">
                    <div class="status-item">
                        <span class="status-label">有效频道:</span>
                        <span id="valid-count">0</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">无效频道:</span>
                        <span id="invalid-count">0</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">超时频道:</span>
                        <span id="timeout-count">0</span>
                    </div>
                </div>
                <div class="real-time-status">
                    <div class="status-item">
                        <span class="status-label">当前频道:</span>
                        <span id="current-channel">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">线程号:</span>
                        <span id="thread-id">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">有效性:</span>
                        <span id="channel-validity">-</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">分辨率:</span>
                        <span id="channel-resolution">-</span>
                    </div>
                </div>
            </div>

            <!-- 实时结果表格 -->
            <div class="table-container">
                <table class="results-table">
                    <tr>
                        <th>频道名称</th>
                        <th>播放地址</th>
                        <th>线程号</th>
                        <th>有效性</th>
                        <th>视频宽</th>
                        <th>视频高</th>
                    </tr>
                    <tbody id="results-table-body">
                    </tbody>
                </table>
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="result {{ category }}">{{ message|safe }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <!-- Socket.IO客户端库 -->
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        // 初始化Socket.io连接
        const socket = io();
        
        // 连接事件
        socket.on('connection_established', function(data) {
            console.log('WebSocket连接已建立:', data.message);
        });
        
        // 标签页切换函数
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
        
        // 读取文件为Base64
        function readFileAsBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }
        
        // 文件上传验证
        async function startFileValidation() {
            const fileInput = document.getElementById('file');
            const workers = document.getElementById('workers').value;
            const timeout = document.getElementById('timeout').value;
            
            if (!fileInput.files.length) {
                alert('请选择文件');
                return;
            }
            
            const file = fileInput.files[0];
            const fileContent = await readFileAsBase64(file);
            const extension = '.' + file.name.split('.').pop();
            
            startValidation('file', { file_data: { content: fileContent, extension } }, workers, timeout);
        }
        
        // URL输入验证
        function startUrlValidation() {
            const urlsText = document.getElementById('urls').value;
            const category = document.getElementById('category').value;
            const workers = document.getElementById('workers2').value;
            const timeout = document.getElementById('timeout2').value;
            
            if (!urlsText.trim()) {
                alert('请输入URL');
                return;
            }
            
            startValidation('url', { urls: urlsText, category }, workers, timeout);
        }
        
        // 互联网直播源验证
        function startWebSourceValidation() {
            const sourceUrl = document.getElementById('source_url').value;
            const workers = document.getElementById('workers3').value;
            const timeout = document.getElementById('timeout3').value;
            
            if (!sourceUrl.trim()) {
                alert('请输入互联网直播源文件URL');
                return;
            }
            
            startValidation('network', { url: sourceUrl }, workers, timeout);
        }
        
        // 通用开始验证函数
        function startValidation(type, data, workers, timeout) {
            // 显示进度区域
            document.getElementById('progress-container').style.display = 'block';
            // 清空结果表格
            document.getElementById('results-table-body').innerHTML = '';
            
            // 重置进度统计计数器
            validCount = 0;
            invalidCount = 0;
            timeoutCount = 0;
            
            // 重置统计显示
            document.getElementById('valid-count').textContent = '0';
            document.getElementById('invalid-count').textContent = '0';
            document.getElementById('timeout-count').textContent = '0';
            
            // 发送验证请求
            socket.emit('start_validation', {
                type: type,
                ...data,
                workers: parseInt(workers) || 20,
                timeout: parseInt(timeout) || 5
            });
        }
        
        // 验证开始事件
        socket.on('validation_started', function(data) {
            console.log('验证开始:', data.message);
        });
        
        // 进度统计计数器
        let validCount = 0;
        let invalidCount = 0;
        let timeoutCount = 0;
        
        // 进度更新事件
        socket.on('validation_progress', function(data) {
            console.log('进度更新:', data);
            
            // 更新进度条
            const progressFill = document.querySelector('.progress-fill');
            const progressPercentage = document.getElementById('progress-percentage');
            const progressStats = document.getElementById('progress-stats');
            
            progressFill.style.width = data.progress + '%';
            progressPercentage.textContent = data.progress + '%';
            progressStats.textContent = `${data.processed}/${data.total_channels} 频道`;
            
            // 更新实时状态
            if (data.channel) {
                const currentChannel = document.getElementById('current-channel');
                const threadId = document.getElementById('thread-id');
                const channelValidity = document.getElementById('channel-validity');
                const channelResolution = document.getElementById('channel-resolution');
                
                currentChannel.textContent = data.channel.name;
                threadId.textContent = data.channel.thread_id;
                
                // 更新有效性状态
                if (data.channel.status === 'timeout') {
                    channelValidity.textContent = '超时';
                    channelValidity.className = 'invalid';
                    timeoutCount++;
                } else {
                    channelValidity.textContent = data.channel.valid ? '有效' : '无效';
                    channelValidity.className = data.channel.valid ? 'valid' : 'invalid';
                    if (data.channel.valid) {
                        validCount++;
                    } else {
                        invalidCount++;
                    }
                }
                
                channelResolution.textContent = data.channel.resolution || '未检测到';
                
                // 更新进度统计
                document.getElementById('valid-count').textContent = validCount;
                document.getElementById('invalid-count').textContent = invalidCount;
                document.getElementById('timeout-count').textContent = timeoutCount;
                
                // 添加到结果表格
                addResultToTable(data.channel);
            }
        });
        
        // 验证完成事件
        socket.on('validation_completed', function(data) {
            console.log('验证完成:', data);
            
            // 显示完成信息
            const message = `验证完成！总频道数: ${data.total_channels}, 有效频道数: ${data.valid_channels}`;
            const downloadLink = `<a href="/download/${data.output_file}" class="download-link">下载有效直播源文件</a>`;
            
            // 创建完成提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            resultDiv.innerHTML = `<p>${message}</p>${downloadLink}`;
            container.appendChild(resultDiv);
        });
        
        // 验证错误事件
        socket.on('validation_error', function(data) {
            console.error('验证错误:', data);
            
            // 创建错误提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result error';
            resultDiv.innerHTML = `<p>${data.message}</p>`;
            container.appendChild(resultDiv);
        });
        
        // 添加结果到表格
        function addResultToTable(result) {
            const tbody = document.getElementById('results-table-body');
            const row = document.createElement('tr');
            
            const nameCell = document.createElement('td');
            nameCell.textContent = result.name;
            
            const urlCell = document.createElement('td');
            const urlLink = document.createElement('a');
            urlLink.href = result.url;
            urlLink.target = '_blank';
            urlLink.textContent = result.url;
            urlCell.appendChild(urlLink);
            
            const threadIdCell = document.createElement('td');
            threadIdCell.textContent = result.thread_id;
            
            const validCell = document.createElement('td');
            validCell.textContent = result.valid ? '有效' : '无效';
            validCell.className = result.valid ? 'valid' : 'invalid';
            
            // 拆分分辨率为视频宽和视频高
            let width = '未检测到';
            let height = '未检测到';
            if (result.resolution) {
                const resolutionParts = result.resolution.split('*');
                if (resolutionParts.length === 2) {
                    width = resolutionParts[0];
                    height = resolutionParts[1];
                }
            }
            
            const widthCell = document.createElement('td');
            widthCell.textContent = width;
            
            const heightCell = document.createElement('td');
            heightCell.textContent = height;
            
            row.appendChild(nameCell);
            row.appendChild(urlCell);
            row.appendChild(threadIdCell);
            row.appendChild(validCell);
            row.appendChild(widthCell);
            row.appendChild(heightCell);
            
            tbody.appendChild(row);
            
            // 滚动到表格底部
            tbody.scrollTop = tbody.scrollHeight;
        }
    </script>
</body>
</html>
'''

# 进度回调函数
def validation_progress_callback(data):
    """用于实时发送验证进度的回调函数"""
    socketio.emit('validation_progress', data)

@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    emit('connection_established', {'message': '已连接到服务器'})

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    app.logger.info('WebSocket连接已断开')

@socketio.on('start_validation')
def start_validation(data):
    """启动验证过程"""
    emit('validation_started', {'message': '验证过程已开始'})
    
    try:
        # 获取参数
        workers = data.get('workers', 20)
        timeout = data.get('timeout', 5)
        
        # 根据验证类型处理
        if data.get('type') == 'file':
            # 处理文件验证
            file_data = data.get('file_data')
            if not file_data:
                emit('validation_error', {'message': '文件数据为空'})
                return
                
            # 创建临时文件
            file_bytes = base64.b64decode(file_data['content'])
            temp_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex() + file_data['extension'])
            with open(temp_path, 'wb') as f:
                f.write(file_bytes)
                
            # 确保output目录存在
            if not os.path.exists('output'):
                os.makedirs('output')
                app.logger.debug("已创建output目录")
                
            # 执行验证
            validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout)
            valid_channels = validator.validate_channels(progress_callback=validation_progress_callback)
            
            # 生成输出文件
            output_file = os.path.basename(validator.generate_output_files())
            
            # 清理临时文件
            os.remove(temp_path)
            
            emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file
            })
            
        elif data.get('type') == 'url':
            # 处理URL验证
            urls = data.get('urls')
            category = data.get('category', '默认分类')
            if not urls:
                emit('validation_error', {'message': 'URL列表为空'})
                return
                
            # 创建临时文件
            temp_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex() + '.m3u')
            with open(temp_path, 'wb') as temp:
                temp.write(b'#EXTM3U\n')
                for line in urls.strip().split('\n'):
                    line = line.strip()
                    if line and ',' in line:
                        name, url = line.split(',', 1)
                        temp.write(f'#EXTINF:-1 group-title="{category}",{name.strip()}\n{url.strip()}\n'.encode('utf-8'))
                
            # 执行验证
            validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout)
            valid_channels = validator.validate_channels(progress_callback=validation_progress_callback)
            
            # 生成输出文件
            output_file = os.path.basename(validator.generate_output_files())
            
            # 清理临时文件
            os.remove(temp_path)
            
            emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file
            })
            
        elif data.get('type') == 'network':
            # 处理网络源验证
            url = data.get('url')
            if not url:
                emit('validation_error', {'message': '网络源URL为空'})
                return
                
            # 执行验证
            validator = IPTVValidator(url, max_workers=workers, timeout=timeout)
            valid_channels = validator.validate_channels(progress_callback=validation_progress_callback)
            
            # 生成输出文件
            output_file = os.path.basename(validator.generate_output_files())
            
            emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file
            })
            
    except Exception as e:
        app.logger.error(f'验证过程出错: {str(e)}')
        emit('validation_error', {'message': f'验证过程出错: {str(e)}'})

@app.route('/', methods=['GET', 'POST'])
def index():
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
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')