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

# 初始化SocketIO，增加消息缓冲区大小以支持大文件
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    max_http_buffer_size=100 * 1024 * 1024,  # 100MB for large file uploads
    ping_timeout=60,
    ping_interval=25
)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'m3u', 'm3u8', 'txt', 'json'}

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
            margin-bottom: 15px;
            font-size: 1.5em;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .container {
            max-width: 1000px;
            width: 100%;
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
            padding: 12px 15px;
            transition: all 0.3s ease;
            color: white;
            font-size: 14px;
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
            padding: 15px;
        }
        
        .form-group {
            margin-bottom: 20px;
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
        
        /* 表单行样式 - 用于将多个表单组放在同一行 */
        .form-row {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .form-row .form-group {
            flex: 1;
            margin-bottom: 0;
        }
        
        /* 按钮样式 */
        button {
            background: linear-gradient(135deg, #667eea 0%, #8e9bef 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
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
            margin-top: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            max-height: 360px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
        }
        
        .results-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        
        .results-table th, .results-table td {
            padding: 6px 8px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
            font-size: 12px;
            white-space: nowrap;
        }

        /* 为URL列添加截断效果 */
        .results-table td:nth-child(2) {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .results-table td:nth-child(2) a {
            display: inline-block;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .results-table th {
            background: #343a40;
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 13px;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 1;
        }
        
        .results-table tbody tr {
            transition: background-color 0.2s ease;
        }
        
        .results-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        /* 状态样式 */
        .valid {
            color: green;
            font-weight: 600;
        }
        
        .invalid {
            /* 移除红色标记 */
            font-weight: 600;
        }
        
        .timeout {
            color: #ff8c00;
            font-weight: 600;
        }
        
        .resolution {
            font-family: 'Courier New', monospace;
            color: #667eea;
            font-weight: 600;
        }
        
        /* 进度统计样式 */
        .progress-stats {
            margin-top: 15px;
            padding: 12px 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            border: 1px solid #e9ecef;
        }
        
        .progress-stats .status-item {
            display: inline-block;
            margin-right: 20px;
        }
        
        .status-label {
            font-weight: 600;
            color: #495057;
        }
        
        /* 实时状态样式 */
        .real-time-status {
            margin-top: 15px;
            padding: 12px 15px;
            background-color: #f8f9fa;
            border-radius: 8px;
            font-size: 13px;
            border: 1px solid #e9ecef;
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
            margin: 15px 0;
            padding: 12px;
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
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        /* 控制按钮样式 */
        .control-buttons {
            display: flex;
            gap: 12px;
            margin-top: 15px;
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
                    <label for="file">选择直播源文件 (.m3u, .m3u8, .txt, .json)</label>
                    <input type="file" id="file" name="file" accept=".m3u,.m3u8,.txt,.json" required>
                </div>
                <div class="form-row" style="align-items: flex-end; gap: 15px;">
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="workers">并发工作线程数</label>
                        <input type="number" id="workers" name="workers" value="20" min="1" max="100">
                    </div>
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="timeout">超时时间（秒）</label>
                        <input type="number" id="timeout" name="timeout" value="5" min="1" max="60">
                    </div>
                    <div style="flex: 1;"></div>
                    <div style="display: flex; gap: 10px;">
                        <button type="button" id="start-btn1" onclick="startFileValidation()">开始验证</button>
                        <button type="button" id="stop-btn1" onclick="stopValidation()" disabled>停止</button>
                        <button type="button" onclick="clearList()">清空列表</button>
                    </div>
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
                <div class="form-row" style="align-items: flex-end; gap: 15px;">
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="workers2">并发工作线程数</label>
                        <input type="number" id="workers2" name="workers2" value="20" min="1" max="100">
                    </div>
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="timeout2">超时时间（秒）</label>
                        <input type="number" id="timeout2" name="timeout2" value="5" min="1" max="60">
                    </div>
                    <div style="flex: 1;"></div>
                    <div style="display: flex; gap: 10px;">
                        <button type="button" id="start-btn2" onclick="startUrlValidation()">开始验证</button>
                        <button type="button" id="stop-btn2" onclick="stopValidation()" disabled>停止</button>
                        <button type="button" onclick="clearList()">清空列表</button>
                    </div>
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
                <div class="form-row" style="align-items: flex-end; gap: 15px;">
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="workers3">并发工作线程数</label>
                        <input type="number" id="workers3" name="workers3" value="20" min="1" max="100">
                    </div>
                    <div class="form-group" style="flex: 0 0 150px;">
                        <label for="timeout3">超时时间（秒）</label>
                        <input type="number" id="timeout3" name="timeout3" value="5" min="1" max="60">
                    </div>
                    <div style="flex: 1;"></div>
                    <div style="display: flex; gap: 10px;">
                        <button type="button" id="start-btn3" onclick="startWebSourceValidation()">开始验证</button>
                        <button type="button" id="stop-btn3" onclick="stopValidation()" disabled>停止</button>
                        <button type="button" onclick="clearList()">清空列表</button>
                    </div>
                </div>
            </form>
        </div>

        <!-- 进度显示区域 -->
        <div id="progress-container" style="display: none; padding: 20px;">
            <!-- 实时结果表格 -->
            <div class="table-container">
                <table class="results-table">
                    <tr>
                        <th>频道名称</th>
                        <th>播放地址</th>
                        <th>有效性</th>
                        <th>视频宽</th>
                        <th>视频高</th>
                    </tr>
                    <tbody id="results-table-body">
                    </tbody>
                </table>
            </div>

            <!-- 底部进度统计部分 -->
            <div id="reading-progress-container" class="progress-container" style="display: none;">
                <h3>读取进度</h3>
                <div class="progress-bar">
                    <div id="reading-progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-info">
                    <span id="reading-progress-percentage">0%</span>
                    <span id="reading-progress-stats">0/0 频道</span>
                </div>
            </div>
            <div id="external-url-progress-container" class="progress-container" style="display: none;">
                <h3>外部URL处理进度</h3>
                <div class="progress-bar">
                    <div id="external-url-progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-info">
                    <span id="external-url-progress-percentage">0%</span>
                    <span id="external-url-progress-stats">0/0 外部URL</span>
                </div>
            </div>
            <div id="validation-progress-container" class="progress-container" style="display: none;">
                <h3>验证进度</h3>
                <div class="progress-bar">
                    <div id="validation-progress-fill" class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-info">
                    <span id="validation-progress-percentage">0%</span>
                    <span id="validation-progress-stats">0/0 频道</span>
                </div>
                <div class="progress-stats">
                    <div class="status-item">
                        <span class="status-label">有效频道:</span>
                        <span id="valid-count">0</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">分辨率有效频道:</span>
                        <span id="resolution-valid-count">0</span>
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
        const socket = io(window.location.origin);
        
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
            
            startValidation('file', { file_data: { content: fileContent, extension, filename: file.name } }, workers, timeout);
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
            // 停止可能正在进行的验证
            stopValidation();
            // 清空结果表格
            document.getElementById('results-table-body').innerHTML = '';
            
            // 清除现有的结果消息
            const existingResults = document.querySelectorAll('.result');
            existingResults.forEach(div => div.remove());
            
            // 重置所有进度条
            document.getElementById('reading-progress-fill').style.width = '0%';
            document.getElementById('reading-progress-percentage').textContent = '0%';
            document.getElementById('reading-progress-stats').textContent = '0/0 频道';
            
            document.getElementById('validation-progress-fill').style.width = '0%';
            document.getElementById('validation-progress-percentage').textContent = '0%';
            document.getElementById('validation-progress-stats').textContent = '0/0 频道';
            
            // 重置进度统计计数器
            validCount = 0;
            resolutionValidCount = 0;
            invalidCount = 0;
            timeoutCount = 0;
            
            // 重置统计显示
            document.getElementById('valid-count').textContent = '0';
            document.getElementById('resolution-valid-count').textContent = '0';
            document.getElementById('invalid-count').textContent = '0';
            document.getElementById('timeout-count').textContent = '0';
            
            // 禁用所有开始按钮，启用所有停止按钮
            document.getElementById('start-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('start-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('start-btn3').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn1').removeAttribute('disabled');
            document.getElementById('stop-btn2').removeAttribute('disabled');
            document.getElementById('stop-btn3').removeAttribute('disabled');
            
            // 生成唯一验证ID
            const validation_id = Date.now().toString() + Math.floor(Math.random() * 1000).toString();
            
            // 发送验证请求
            socket.emit('start_validation', {
                type: type,
                ...data,
                workers: parseInt(workers) || 20,
                timeout: parseInt(timeout) || 5,
                validation_id: validation_id
            });
            
            // 保存当前验证ID
            currentValidationId = validation_id;
        }
        
        // 停止验证函数
        function stopValidation() {
            // 发送停止验证请求
            socket.emit('stop_validation');
            
            // 禁用停止按钮
            document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
        }
        
        // 清空列表函数
        function clearList() {
            // 清空结果表格
            document.getElementById('results-table-body').innerHTML = '';
            
            // 重置进度统计
            validCount = 0;
            resolutionValidCount = 0;
            invalidCount = 0;
            timeoutCount = 0;
            
            // 更新统计显示
            document.getElementById('valid-count').textContent = '0';
            document.getElementById('resolution-valid-count').textContent = '0';
            document.getElementById('invalid-count').textContent = '0';
            document.getElementById('timeout-count').textContent = '0';
            
            // 隐藏进度区域
            document.getElementById('progress-container').style.display = 'none';
        }
        
        // 验证开始事件
        socket.on('validation_started', function(data) {
            console.log('验证开始:', data.message);
            // 显示进度区域
            document.getElementById('progress-container').style.display = 'block';
            // 默认显示读取阶段进度
            document.getElementById('reading-progress-container').style.display = 'block';
            document.getElementById('external-url-progress-container').style.display = 'none';
            document.getElementById('validation-progress-container').style.display = 'none';
        });
        
        // 进度统计计数器
        let validCount = 0;
        let resolutionValidCount = 0;
        let invalidCount = 0;
        let timeoutCount = 0;
        
        // 当前验证会话ID
        let currentValidationId = null;
        
        // 进度更新事件
        socket.on('validation_progress', function(data) {
            console.log('进度更新:', data);
            
            // 检查验证ID是否匹配当前验证会话
            // 如果data中没有validation_id，也应该接受（向后兼容）
            if (data.validation_id && currentValidationId && data.validation_id !== currentValidationId) {
                console.log('忽略不属于当前验证会话的进度更新');
                return;
            }
            
            // 根据阶段更新不同的进度条
            if (data.stage === 'parsing' || data.stage === 'reading') {
                // 读取阶段进度
                document.getElementById('reading-progress-container').style.display = 'block';
                document.getElementById('external-url-progress-container').style.display = 'none';
                document.getElementById('validation-progress-container').style.display = 'none';
                
                const progressFill = document.getElementById('reading-progress-fill');
                const progressPercentage = document.getElementById('reading-progress-percentage');
                const progressStats = document.getElementById('reading-progress-stats');
                
                progressFill.style.width = data.progress + '%';
                progressPercentage.textContent = data.progress + '%';
                progressStats.textContent = `${data.processed}/${data.total_channels} 频道`;
            } else if (data.stage === 'external_url_processing') {
                // 外部URL处理阶段进度
                document.getElementById('reading-progress-container').style.display = 'none';
                document.getElementById('external-url-progress-container').style.display = 'block';
                document.getElementById('validation-progress-container').style.display = 'none';
                
                const progressFill = document.getElementById('external-url-progress-fill');
                const progressPercentage = document.getElementById('external-url-progress-percentage');
                const progressStats = document.getElementById('external-url-progress-stats');
                
                // 计算外部URL处理进度
                const externalProgress = data.total_external > 0 ? Math.round((data.processed_external / data.total_external) * 100) : 0;
                
                progressFill.style.width = externalProgress + '%';
                progressPercentage.textContent = externalProgress + '%';
                progressStats.textContent = `${data.processed_external}/${data.total_external} 外部URL`;
            } else {
                // 验证阶段进度
                document.getElementById('reading-progress-container').style.display = 'none';
                document.getElementById('external-url-progress-container').style.display = 'none';
                document.getElementById('validation-progress-container').style.display = 'block';
                
                const progressFill = document.getElementById('validation-progress-fill');
                const progressPercentage = document.getElementById('validation-progress-percentage');
                const progressStats = document.getElementById('validation-progress-stats');
                
                progressFill.style.width = data.progress + '%';
                progressPercentage.textContent = data.progress + '%';
                progressStats.textContent = `${data.processed}/${data.total_channels} 频道`;
                
                // 仅在验证阶段更新计数器逻辑
                if (data.channel) {
                    if (data.channel.status === 'timeout') {
                        timeoutCount++;
                    } else if ('valid' in data.channel) {
                        if (data.channel.valid === null || data.channel.valid === undefined) {
                            // 未验证完成，不更新计数器
                        } else if (data.channel.valid) {
                            validCount++;
                            // 检查是否有分辨率
                            if (data.channel.resolution) {
                                resolutionValidCount++;
                            }
                        } else {
                            invalidCount++;
                        }
                    } else if (data.channel.status === 'invalid') {
                        // 处理没有'valid'字段但状态为'invalid'的情况
                        invalidCount++;
                    }
                    
                    // 更新进度统计
                    document.getElementById('valid-count').textContent = validCount;
                    document.getElementById('resolution-valid-count').textContent = resolutionValidCount;
                    document.getElementById('invalid-count').textContent = invalidCount;
                    document.getElementById('timeout-count').textContent = timeoutCount;
                }
            }
            
            // 只在收到实际验证结果时添加到表格，过滤掉解析阶段的虚拟频道
            if (data.channel) {
                // 实际频道必须包含URL，且不是解析阶段的进度更新
                if (data.channel.url && data.stage !== 'parsing') {
                    addResultToTable(data.channel);
                } else if (data.channel.name === '完成解析文件') {
                    // 兼容处理旧版数据，直接忽略
                    console.log('忽略虚拟频道：', data.channel.name);
                }
            }
        });
        
        // 验证完成事件
        socket.on('validation_completed', function(data) {
            console.log('验证完成:', data);
            
            // 检查验证ID是否匹配当前验证会话
            if (data.validation_id && data.validation_id !== currentValidationId) {
                console.log('忽略不属于当前验证会话的完成事件');
                return;
            }
            
            // 显示完成信息
            const message = `验证完成！总频道数: ${data.total_channels}, 有效频道数: ${data.valid_channels}`;
            const downloadLink = `<a href="/download/${data.output_file}" class="download-link">下载有效直播源文件</a>`;
            
            // 创建完成提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            resultDiv.innerHTML = '<p>' + message + '</p>' + downloadLink;
            container.appendChild(resultDiv);
            
            // 重新启用所有开始按钮，禁用所有停止按钮
            document.getElementById('start-btn1').removeAttribute('disabled');
            document.getElementById('start-btn2').removeAttribute('disabled');
            document.getElementById('start-btn3').removeAttribute('disabled');
            document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
        });
        
        // 验证错误事件
        socket.on('validation_error', function(data) {
            console.error('验证错误:', data);
            
            // 检查验证ID是否匹配当前验证会话
            if (data.validation_id && data.validation_id !== currentValidationId) {
                console.log('忽略不属于当前验证会话的错误事件');
                return;
            }
            
            // 创建错误提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result error';
            resultDiv.innerHTML = '<p>' + data.message + '</p>';
            container.appendChild(resultDiv);
            
            // 重新启用所有开始按钮，禁用所有停止按钮
            document.getElementById('start-btn1').removeAttribute('disabled');
            document.getElementById('start-btn2').removeAttribute('disabled');
            document.getElementById('start-btn3').removeAttribute('disabled');
            document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
        });
        
        // 验证停止事件
        socket.on('validation_stopped', function(data) {
            console.log('验证停止:', data.message);
            
            // 检查验证ID是否匹配当前验证会话
            if (data.validation_id && data.validation_id !== currentValidationId) {
                console.log('忽略不属于当前验证会话的停止事件');
                return;
            }
            
            // 重新启用所有开始按钮，禁用所有停止按钮
            document.getElementById('start-btn1').removeAttribute('disabled');
            document.getElementById('start-btn2').removeAttribute('disabled');
            document.getElementById('start-btn3').removeAttribute('disabled');
            document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
            
            // 清除现有的结果消息
            const existingResults = document.querySelectorAll('.result');
            existingResults.forEach(div => div.remove());
            
            // 重置进度条
            const progressFill = document.querySelector('.progress-fill');
            const progressPercentage = document.getElementById('progress-percentage');
            const progressStats = document.getElementById('progress-stats');
            progressFill.style.width = '0%';
            progressPercentage.textContent = '0%';
            progressStats.textContent = '0/0 频道';
            
            // 重置进度统计计数器
            validCount = 0;
            resolutionValidCount = 0;
            invalidCount = 0;
            timeoutCount = 0;
            
            // 重置统计显示
            document.getElementById('valid-count').textContent = '0';
            document.getElementById('resolution-valid-count').textContent = '0';
            document.getElementById('invalid-count').textContent = '0';
            document.getElementById('timeout-count').textContent = '0';
            
            // 创建停止提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result';
            resultDiv.innerHTML = '<p>' + data.message + '</p>';
            container.appendChild(resultDiv);
        });
        
        // 添加结果到表格
        function addResultToTable(result) {
            const tbody = document.getElementById('results-table-body');
            const row = document.createElement('tr');
            
            // 存储原始索引用于排序
            row.dataset.originalIndex = result.original_index;
            
            const nameCell = document.createElement('td');
            nameCell.textContent = result.name;
            
            const urlCell = document.createElement('td');
            const urlLink = document.createElement('a');
            urlLink.href = result.url;
            urlLink.target = '_blank';
            urlLink.textContent = result.url;
            urlCell.appendChild(urlLink);
            
            const validCell = document.createElement('td');
            if (result.status === 'timeout') {
                validCell.textContent = '超时';
                validCell.className = 'timeout';
            } else if (result.valid === null || result.valid === undefined) {
                validCell.textContent = ''; // 未验证时显示为空
                validCell.className = 'checking';
            } else {
                validCell.textContent = result.valid ? '有效' : '无效';
                validCell.className = result.valid ? 'valid' : 'invalid';
            }
            
            // 拆分分辨率为视频宽和视频高
            let width = '';
            let height = '';
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
            row.appendChild(validCell);
            row.appendChild(widthCell);
            row.appendChild(heightCell);
            
            // 根据原始索引将行插入到正确位置
            const rows = Array.from(tbody.children);
            const insertIndex = rows.findIndex(r => parseInt(r.dataset.originalIndex) > result.original_index);
            
            if (insertIndex === -1) {
                tbody.appendChild(row);
                const tableContainer = document.querySelector('.table-container');
                if (tableContainer) {
                    tableContainer.scrollTop = tableContainer.scrollHeight;
                }
            } else {
                tbody.insertBefore(row, rows[insertIndex]);
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
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

# 全局变量保存当前验证器实例
global_validator = None



def run_validation(data):
    """在单独线程中执行验证过程"""
    print("[调试] run_validation 函数开始执行")
    global global_validator
    sid = data.get('sid')
    temp_paths = []  # 存储所有创建的临时文件路径
    
    try:
        # 获取参数
        workers = data.get('workers', 20)
        timeout = data.get('timeout', 5)
        print(f"[调试] 参数: workers={workers}, timeout={timeout}")
        
        # 生成唯一验证ID
        validation_id = data.get('validation_id', '')
        print(f"[调试] validation_id: {validation_id}")
        
        # 首先发送验证开始事件，让前端准备好接收进度
        try:
            socketio.emit('validation_started', {
                'message': '验证过程已开始',
                'validation_id': validation_id
            }, room=sid)
            print(f"[调试] 验证开始事件已发送, validation_id: {validation_id}")
        except Exception as e:
            print(f"[调试] 发送验证开始事件失败: {str(e)}")
        
        # 定义进度回调函数，确保在正确的线程中发送事件
        # 注意：validation_id 在回调定义时已经可用
        def thread_safe_progress_callback(progress_data):
            try:
                # 确保validation_id始终存在
                if 'validation_id' not in progress_data:
                    progress_data['validation_id'] = validation_id
                
                # 确保channel对象始终包含基本字段
                if progress_data.get('channel'):
                    channel = progress_data['channel']
                    if 'name' not in channel or not channel['name']:
                        channel['name'] = channel.get('name', '未命名频道') or '未命名频道'
                    if 'url' not in channel:
                        channel['url'] = ''
                    if 'valid' not in channel:
                        channel['valid'] = None
                        channel['status'] = 'processing'
                
                socketio.emit('validation_progress', progress_data, room=sid)
            except Exception as e:
                print(f"[调试] 发送进度事件时出错: {str(e)}")
        
        # 根据验证类型处理
        if data.get('type') == 'file':
            print("[调试] 开始处理文件验证")
            # 处理文件验证
            file_data = data.get('file_data')
            if not file_data:
                print("[调试] 文件数据为空")
                socketio.emit('validation_error', {'message': '文件数据为空'}, room=sid)
                return
            
            try:
                # 解码文件内容
                print(f"[调试] 开始解码文件内容，数据长度: {len(file_data.get('content', ''))}")
                file_bytes = base64.b64decode(file_data['content'])
                print(f"[调试] 文件解码成功，大小: {len(file_bytes)} bytes")
            except Exception as decode_error:
                print(f"[调试] 文件解码失败: {str(decode_error)}")
                socketio.emit('validation_error', {'message': f'文件解码失败: {str(decode_error)}'}, room=sid)
                return
            
            # 创建临时文件
            try:
                print("[调试] 开始创建临时文件")
                temp_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex() + file_data['extension'])
                temp_paths.append(temp_path)
                print(f"[调试] 临时文件路径: {temp_path}")
                with open(temp_path, 'wb') as f:
                    f.write(file_bytes)
                print(f"[调试] 临时文件写入完成: {temp_path}")
            except Exception as file_error:
                print(f"[调试] 创建临时文件失败: {str(file_error)}")
                socketio.emit('validation_error', {'message': f'创建临时文件失败: {str(file_error)}'}, room=sid)
                return
                
            # 确保output目录存在
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(script_dir, 'output')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                app.logger.debug(f"已创建output目录: {output_dir}")
                
            # 执行验证，将引用保存在局部变量中
            original_filename = file_data.get('filename', f'uploaded{file_data["extension"]}')
            print(f"[调试] 开始创建IPTVValidator，文件路径: {temp_path}")
            
            try:
                local_validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout, original_filename=original_filename)
                global_validator = local_validator
                print(f"[调试] IPTVValidator创建完成, 文件类型: {local_validator.file_type}")
            except Exception as validator_error:
                print(f"[调试] 创建验证器失败: {str(validator_error)}")
                socketio.emit('validation_error', {'message': f'创建验证器失败: {str(validator_error)}'}, room=sid)
                return
            
            # 发送验证开始的进度更新
            thread_safe_progress_callback({
                'progress': 0,
                'total_channels': 0,
                'processed': 0,
                'message': f'开始解析{original_filename}，文件类型：{local_validator.file_type}',
                'stage': 'validation_started'
            })
            
            print(f"[调试] 开始解析文件: {local_validator.file_type}")
            # 根据文件类型解析文件内容
            try:
                if local_validator.file_type == 'm3u':
                    print("[调试] 调用 read_m3u_file")
                    local_validator.read_m3u_file(progress_callback=thread_safe_progress_callback)
                elif local_validator.file_type == 'json':
                    print("[调试] 调用 read_json_file")
                    local_validator.read_json_file(progress_callback=thread_safe_progress_callback)
                else:
                    print("[调试] 调用 read_txt_file")
                    local_validator.read_txt_file(progress_callback=thread_safe_progress_callback)
                
                print(f"[调试] 文件解析完成, 找到 {len(local_validator.channels)} 个频道")
            except Exception as parse_error:
                print(f"[调试] 文件解析失败: {str(parse_error)}")
                socketio.emit('validation_error', {'message': f'文件解析失败: {str(parse_error)}'}, room=sid)
                return
            
            # 发送解析完成的进度更新
            thread_safe_progress_callback({
                'progress': 10,
                'total_channels': len(local_validator.channels),
                'processed': 0,
                'message': f'文件解析完成，共找到{len(local_validator.channels)}个频道，开始验证频道有效性',
                'stage': 'parsing_completed'
            })
                
            # 检查是否请求停止
            if local_validator.stop_requested:
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id
                }, room=sid)
                return
                
            valid_channels = local_validator.validate_channels(progress_callback=thread_safe_progress_callback)
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id
                }, room=sid)
                return
                
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            
            socketio.emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(local_validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file,
                'validation_id': validation_id
            }, room=sid)
            
        elif data.get('type') == 'url':
            # 处理URL验证
            urls = data.get('urls')
            category = data.get('category', '默认分类')
            if not urls:
                socketio.emit('validation_error', {'message': 'URL列表为空'}, room=sid)
                return
                
            # 创建临时文件
            temp_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex() + '.m3u')
            temp_paths.append(temp_path)  # 添加到临时文件列表
            with open(temp_path, 'wb') as temp:
                temp.write(b'#EXTM3U\n')
                for line in urls.strip().split('\n'):
                    line = line.strip()
                    if line and ',' in line:
                        try:
                            name, url = line.split(',', 1)
                            if name.strip() and url.strip():
                                temp.write(f'#EXTINF:-1 group-title="{category}",{name.strip()}\n{url.strip()}\n'.encode('utf-8'))
                        except ValueError:
                            # 处理分割错误，跳过无效行
                            continue
                
            # 执行验证，将引用保存在局部变量中
            # 使用默认文件名"url_channels"作为原始文件名
            local_validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout, original_filename="url_channels.m3u")
            global_validator = local_validator  # 更新全局引用
            
            # 发送验证开始的进度更新
            thread_safe_progress_callback({
                'progress': 0,
                'total_channels': len(local_validator.channels),
                'processed': 0,
                'message': f'URL列表解析完成，共找到{len(local_validator.channels)}个频道，开始验证频道有效性',
                'stage': 'validation_started'
            })
            
            valid_channels = local_validator.validate_channels(progress_callback=thread_safe_progress_callback)
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id
                }, room=sid)
                return
                
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            
            socketio.emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(local_validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file,
                'validation_id': validation_id
            }, room=sid)
            
        elif data.get('type') == 'network':
            # 处理网络源验证
            url = data.get('url')
            if not url:
                socketio.emit('validation_error', {'message': '网络源URL为空'}, room=sid)
                return
                
            # 执行验证，将引用保存在局部变量中
            local_validator = IPTVValidator(url, max_workers=workers, timeout=timeout)
            global_validator = local_validator  # 更新全局引用
            
            # 发送验证开始的进度更新
            thread_safe_progress_callback({
                'progress': 0,
                'total_channels': 0,
                'processed': 0,
                'message': f'开始下载并解析网络源：{url}',
                'stage': 'validation_started'
            })
            
            # 根据文件类型解析文件内容
            if local_validator.file_type == 'm3u':
                local_validator.read_m3u_file(progress_callback=thread_safe_progress_callback)
            elif local_validator.file_type == 'json':
                local_validator.read_json_file(progress_callback=thread_safe_progress_callback)
            else:
                local_validator.read_txt_file(progress_callback=thread_safe_progress_callback)
            
            # 发送解析完成的进度更新
            thread_safe_progress_callback({
                'progress': 10,
                'total_channels': len(local_validator.channels),
                'processed': 0,
                'message': f'网络源解析完成，共找到{len(local_validator.channels)}个频道，开始验证频道有效性',
                'stage': 'parsing_completed'
            })
                
            # 检查是否请求停止
            if local_validator.stop_requested:
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id
                }, room=sid)
                return
                
            valid_channels = local_validator.validate_channels(progress_callback=thread_safe_progress_callback)
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id
                }, room=sid)
                return
                
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            
            socketio.emit('validation_completed', {
                'message': '验证完成',
                'total_channels': len(local_validator.channels),
                'valid_channels': len(valid_channels),
                'output_file': output_file,
                'validation_id': validation_id
            }, room=sid)
            
    except Exception as e:
        app.logger.error(f'验证过程出错: {str(e)}')
        # 获取验证ID，如果不存在则使用空字符串
        validation_id = data.get('validation_id', '')
        socketio.emit('validation_error', {
            'message': f'验证过程出错: {str(e)}',
            'validation_id': validation_id
        }, room=sid)
    finally:
        # 清理所有临时文件
        for temp_path in temp_paths:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as cleanup_error:
                app.logger.error(f'清理临时文件时出错: {str(cleanup_error)}')
        
        # 重置全局验证器实例
        global_validator = None

@socketio.on('start_validation')
def start_validation(data):
    """启动验证过程"""
    print(f"[调试] 收到验证请求: {data.get('type')}")
    global global_validator
    
    # 首先停止当前正在运行的验证器（如果有）
    if global_validator:
        print("[调试] 停止现有的验证器")
        global_validator.stop()
        # 重置全局验证器
        global_validator = None
    
    # 获取验证ID
    validation_id = data.get('validation_id', '')
    
    # 发送验证开始事件到正确的房间
    socketio.emit('validation_started', {
        'message': '验证过程已开始',
        'validation_id': validation_id
    }, room=request.sid)
    print("[调试] 验证开始消息已发送")
    
    # 将当前会话ID添加到数据中，以便在单独线程中可以发送事件到正确的客户端
    data['sid'] = request.sid
    
    print(f"[调试] 启动验证线程，会话ID: {request.sid}")
    # 在单独线程中执行验证逻辑，避免阻塞WebSocket事件处理
    validation_thread = threading.Thread(target=run_validation, args=(data,))
    validation_thread.daemon = True  # 设置为守护线程，以便在服务器关闭时自动退出
    validation_thread.start()
    print("[调试] 验证线程已启动")

@socketio.on('stop_validation')
def stop_validation():
    """停止验证过程"""
    global global_validator
    if global_validator:
        global_validator.stop()
        # 不立即发送停止消息，而是在run_validation函数中验证真正停止后发送
        # 不要立即重置global_validator，因为run_validation函数中可能还在使用它
        # 让run_validation函数在完成处理后自己清理global_validator

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download/<filename>')
def download_file(filename):
    # 确保只允许下载验证工具生成的有效文件
    safe_filename = os.path.basename(filename)  # 防止路径遍历攻击
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'output', safe_filename)
    if os.path.exists(file_path) and (file_path.endswith('_valid.m3u') or file_path.endswith('_valid.txt')):
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    else:
        flash('文件不存在或不允许下载', 'error')
        return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # 确保输出目录存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 启动Web服务
    socketio.run(app, debug=True, port=5001, host='127.0.0.1')