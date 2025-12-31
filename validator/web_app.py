#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具 - Web界面
"""

import os
import sys

# 添加项目根目录到Python路径，以支持模块导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import tempfile
import logging
import threading
import base64
import secrets
from flask import Flask, request, render_template_string, send_file, flash
from flask_socketio import SocketIO, emit
from validator.iptv_validator import IPTVValidator, validate_ipTV

# 导入统一的配置管理器
try:
    from config_manager import get_config_manager
except ImportError:
    # 如果无法导入，定义一个简单的替代函数
    def get_config_manager():
        class SimpleConfigManager:
            def load_config(self):
                return {}
        return SimpleConfigManager()

# 配置日志记录
def setup_logging():
    """设置日志记录配置"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler('web_validation.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志记录器
logger = setup_logging()

# 加载配置
try:
    config_manager = get_config_manager()
    app_config = config_manager.load_config()
except Exception:
    app_config = {}

# 检查是否启用调试模式
DEBUG_MODE = os.environ.get('WEB_VALIDATOR_DEBUG', 'false').lower() == 'true'

# 安全地获取SECRET_KEY
def get_secret_key():
    """安全地获取SECRET_KEY，优先从环境变量读取"""
    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if not secret_key:
        # 如果环境变量未设置，使用secrets模块生成安全的随机密钥
        secret_key = secrets.token_urlsafe(32)
        logging.warning("警告: 未设置FLASK_SECRET_KEY环境变量，使用生成的临时密钥。请在生产环境中设置FLASK_SECRET_KEY")
    return secret_key

# 从配置中获取值或使用默认值
web_config = app_config.get('web_app', {})
validation_config = app_config.get('validation', {})
logging_config = app_config.get('logging', {})

MAX_CONTENT_LENGTH = web_config.get('max_content_length', 16 * 1024 * 1024)
MAX_HTTP_BUFFER_SIZE = web_config.get('max_http_buffer_size', 100 * 1024 * 1024)
PING_TIMEOUT = web_config.get('ping_timeout', 120)
PING_INTERVAL = web_config.get('ping_interval', 30)
DEFAULT_TIMEOUT = web_config.get('default_timeout', 5)
ALLOWED_EXTENSIONS = set(web_config.get('allowed_extensions', ['m3u', 'm3u8', 'txt', 'json']))

DEFAULT_VALIDATION_TIMEOUT = validation_config.get('default_timeout', 5)
DEFAULT_VALIDATION_WORKERS = validation_config.get('default_workers', 30)

WEB_LOG_FILE = logging_config.get('web_log_file', 'web_validation.log')
LOG_LEVEL = logging_config.get('log_level', 'INFO')

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = get_secret_key()
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 初始化SocketIO，增加消息缓冲区大小以支持大文件
socketio = SocketIO(app, 
    cors_allowed_origins="*",
    max_http_buffer_size=MAX_HTTP_BUFFER_SIZE,
    ping_timeout=PING_TIMEOUT,
    ping_interval=PING_INTERVAL,
    async_mode='threading'
)

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
    <title>直播源有效性验证工具    by  ZHQ</title>
    <link rel="icon" href="data:," />
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
            padding: 12px 12px 8px 12px;
        }
        
        .form-group {
            margin-bottom: 6px;
        }
        
        label {
            display: block;
            margin-bottom: 2px;
            font-weight: 600;
            color: #495057;
            font-size: 12px;
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
            gap: 15px;
            margin-bottom: 15px;
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
            margin-top: 15px;
            padding: 15px;
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
            margin-top: 8px;
            border-radius: 6px;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
            max-height: 350px;
            overflow-y: auto;
            border: 1px solid #e9ecef;
        }
        
        .results-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
        }
        
        .results-table th, .results-table td {
            padding: 4px 6px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
            font-size: 12px;
            white-space: nowrap;
        }

        /* 为URL列添加截断效果 */
        .results-table td:nth-child(2) {
            max-width: 280px;
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
        
        /* 设置各列宽度 */
        .results-table th:nth-child(1),
        .results-table td:nth-child(1) {
            width: 120px;
            max-width: 120px;
        }
        .results-table th:nth-child(2),
        .results-table td:nth-child(2) {
            width: auto;
        }
        .results-table th:nth-child(3),
        .results-table td:nth-child(3) {
            width: 70px;
            text-align: center;
        }
        .results-table th:nth-child(4),
        .results-table td:nth-child(4) {
            width: 60px;
            text-align: center;
        }
        .results-table th:nth-child(5),
        .results-table td:nth-child(5) {
            width: 60px;
            text-align: center;
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
        
        .unknown {
            color: #6c757d;
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
            margin: 8px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
        }
        
        .progress-bar {
            width: 100%;
            height: 16px;
            background-color: #e9ecef;
            border-radius: 8px;
            overflow: hidden;
            margin: 6px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            transition: width 0.3s ease;
        }
        
        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #495057;
        }
        
        /* 进度统计样式 */
        .progress-stats {
            margin-top: 6px;
            padding: 8px 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            font-size: 12px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        /* 控制按钮样式 */
        .control-buttons {
            display: flex;
            gap: 8px;
            margin-top: 10px;
            flex-wrap: wrap;
        }

        /* 实时状态样式 */
        .real-time-status {
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            font-size: 12px;
        }
        
        .status-item {
            margin-bottom: 4px;
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
    <h1>直播源有效性验证工具    by  ZHQ</h1>
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
                    <div class="form-group" style="flex: 0 0 auto;">
                        <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                            <input type="checkbox" id="filter_no_audio" name="filter_no_audio" style="width: auto;">
                            <span>过滤无音频源</span>
                        </label>
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
                    <div class="form-group" style="flex: 0 0 auto;">
                        <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                            <input type="checkbox" id="filter_no_audio2" name="filter_no_audio2" style="width: auto;">
                            <span>过滤无音频源</span>
                        </label>
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
                    <div class="form-group" style="flex: 0 0 auto;">
                        <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                            <input type="checkbox" id="filter_no_audio3" name="filter_no_audio3" style="width: auto;">
                            <span>过滤无音频源</span>
                        </label>
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
        let socket = io(window.location.origin, {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000
        });
        
        // 连接事件
        socket.on('connection_established', function(data) {
            console.log('WebSocket连接已建立:', data.message);
        });
        
        // 重连事件
        socket.on('reconnect', function(attemptNumber) {
            console.log('WebSocket重连成功，尝试次数:', attemptNumber);
        });
        
        socket.on('reconnect_attempt', function(attemptNumber) {
            console.log('WebSocket正在重连，尝试次数:', attemptNumber);
        });
        
        socket.on('reconnect_error', function(error) {
            console.log('WebSocket重连错误:', error);
        });
        
        socket.on('reconnect_failed', function() {
            console.log('WebSocket重连失败');
        });
        
        // 断开连接事件
        socket.on('disconnect', function(reason) {
            console.log('WebSocket连接已断开:', reason);
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
        
        // 初始化文件输入事件监听
        function initFileInputListener() {
            const fileInput = document.getElementById('file');
            if (fileInput) {
                fileInput.addEventListener('change', function() {
                    console.log('文件选择事件触发，清除检测结果');
                    if (this.files.length > 0) {
                        // 用户选择了新文件，自动清除之前的检测结果
                        clearList();
                    }
                });
            }
        }

        // DOM内容加载完成后立即初始化
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM内容加载完成，初始化文件选择监听器');
            initFileInputListener();
        });

        // 文件上传验证
        async function startFileValidation() {
            const fileInput = document.getElementById('file');
            const workers = document.getElementById('workers').value;
            const timeout = document.getElementById('timeout').value;
            const filter_no_audio = document.getElementById('filter_no_audio').checked;
            
            if (!fileInput.files.length) {
                alert('请选择文件');
                return;
            }
            
            const file = fileInput.files[0];
            const fileContent = await readFileAsBase64(file);
            const extension = '.' + file.name.split('.').pop();
            
            await startValidation('file', { file_data: { content: fileContent, extension, filename: file.name } }, workers, timeout, filter_no_audio);
        }
        
        // URL输入验证
        async function startUrlValidation() {
            const urlsText = document.getElementById('urls').value;
            const category = document.getElementById('category').value;
            const workers = document.getElementById('workers2').value;
            const timeout = document.getElementById('timeout2').value;
            const filter_no_audio = document.getElementById('filter_no_audio2').checked;
            
            if (!urlsText.trim()) {
                alert('请输入URL');
                return;
            }
            
            await startValidation('url', { urls: urlsText, category }, workers, timeout, filter_no_audio);
        }
        
        // 互联网直播源验证
        async function startWebSourceValidation() {
            const sourceUrl = document.getElementById('source_url').value;
            const workers = document.getElementById('workers3').value;
            const timeout = document.getElementById('timeout3').value;
            const filter_no_audio = document.getElementById('filter_no_audio3').checked;
            
            if (!sourceUrl.trim()) {
                alert('请输入互联网直播源文件URL');
                return;
            }
            
            await startValidation('network', { url: sourceUrl }, workers, timeout, filter_no_audio);
        }
        
        // 通用开始验证函数
        async function startValidation(type, data, workers, timeout, filter_no_audio=false) {
            // 首先确保任何现有的验证都已停止
            try {
                // 如果有正在进行的验证，先停止
                if (validationInProgress) {
                    socket.emit('stop_validation');
                    console.log('发送停止验证命令');
                    // 等待一下确保停止命令被处理
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            } catch (e) {
                console.log('停止现有验证时出错:', e);
            }
            
            // 重新建立WebSocket连接以确保连接状态干净
            try {
                await resetWebSocketConnection();
            } catch (e) {
                console.error('重新建立连接失败:', e);
                alert('连接服务器失败，请检查网络或服务器状态。');
                return;
            }
            
            // 清空结果列表
            document.getElementById('results-table-body').innerHTML = '';
            
            const existingResults = document.querySelectorAll('.result');
            existingResults.forEach(div => div.remove());
            
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
            
            // 生成唯一验证ID
            const validation_id = generateValidationId();
            
            // 发送验证请求
            socket.emit('start_validation', {
                type: type,
                ...data,
                workers: parseInt(workers) || 20,
                timeout: parseInt(timeout) || 5,
                filter_no_audio: filter_no_audio,
                validation_id: validation_id
            });
            
            // 更新验证状态
            setValidationState(validation_id, true, socket.id);
        }
        
        // 停止验证函数
        function stopValidation() {
            console.log('停止验证函数被调用');
            
            // 立即重新启用开始按钮，禁用停止按钮
            document.getElementById('start-btn1').removeAttribute('disabled');
            document.getElementById('start-btn2').removeAttribute('disabled');
            document.getElementById('start-btn3').removeAttribute('disabled');
            document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
            document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
            
            // 发送停止验证请求
            console.log('发送stop_validation事件');
            socket.emit('stop_validation');
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
            // 显示进度区域，直接显示验证进度（跳过读取进度显示）
            document.getElementById('progress-container').style.display = 'block';
            // 直接显示验证阶段进度，不显示读取阶段
            document.getElementById('reading-progress-container').style.display = 'none';
            document.getElementById('external-url-progress-container').style.display = 'none';
            document.getElementById('validation-progress-container').style.display = 'block';
        });
        
        // 进度统计计数器
        let validCount = 0;
        let resolutionValidCount = 0;
        let invalidCount = 0;
        let timeoutCount = 0;
        
        // 当前验证会话ID
        let currentValidationId = null;
        
        // 验证状态管理
        let validationInProgress = false;
        let currentSessionId = null; // 当前会话ID
        
        // 生成验证ID
        function generateValidationId() {
            return 'validation_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
        }
        
        // 设置验证状态
        function setValidationState(id, inProgress, sessionId) {
            currentValidationId = id;
            validationInProgress = inProgress;
            if (sessionId) {
                currentSessionId = sessionId;
            }
            
            // 更新UI状态
            if (inProgress) {
                document.getElementById('start-btn1').setAttribute('disabled', 'disabled');
                document.getElementById('start-btn2').setAttribute('disabled', 'disabled');
                document.getElementById('start-btn3').setAttribute('disabled', 'disabled');
                
                document.getElementById('stop-btn1').removeAttribute('disabled');
                document.getElementById('stop-btn2').removeAttribute('disabled');
                document.getElementById('stop-btn3').removeAttribute('disabled');
            } else {
                document.getElementById('start-btn1').removeAttribute('disabled');
                document.getElementById('start-btn2').removeAttribute('disabled');
                document.getElementById('start-btn3').removeAttribute('disabled');
                
                document.getElementById('stop-btn1').setAttribute('disabled', 'disabled');
                document.getElementById('stop-btn2').setAttribute('disabled', 'disabled');
                document.getElementById('stop-btn3').setAttribute('disabled', 'disabled');
            }
        }
        
        // 重置WebSocket连接
        async function resetWebSocketConnection() {
            // 断开当前WebSocket连接并重新建立连接
            console.log('重新建立WebSocket连接...');
            const oldSocket = socket;
            
            // 创建一个新的Socket.IO实例
            socket = io(window.location.origin, {
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: 5
            });
            
            // 复制事件监听器
            oldSocket.listeners('validation_progress').forEach(listener => {
                socket.on('validation_progress', listener);
            });
            
            oldSocket.listeners('validation_completed').forEach(listener => {
                socket.on('validation_completed', listener);
            });
            
            oldSocket.listeners('validation_error').forEach(listener => {
                socket.on('validation_error', listener);
            });
            
            oldSocket.listeners('validation_stopped').forEach(listener => {
                socket.on('validation_stopped', listener);
            });
            
            oldSocket.listeners('validation_started').forEach(listener => {
                socket.on('validation_started', listener);
            });
            
            // 等待新连接建立
            return new Promise((resolve, reject) => {
                const timeoutId = setTimeout(() => {
                    reject(new Error('连接超时'));
                }, 10000);
                
                socket.once('connect', () => {
                    clearTimeout(timeoutId);
                    console.log('新WebSocket连接已建立');
                    resolve();
                });
                
                socket.once('connect_error', (error) => {
                    clearTimeout(timeoutId);
                    console.error('WebSocket连接错误:', error);
                    reject(error);
                });
            });
        }
        
        // 进度更新事件
        socket.on('validation_progress', function(data) {
            console.log('进度更新:', data);
            
            // 检查验证ID是否匹配当前验证会话
            // 如果data中没有validation_id，也应该接受（向后兼容）
            if (data.validation_id && currentValidationId && data.validation_id !== currentValidationId) {
                console.log('忽略不属于当前验证会话的进度更新');
                return;
            }
            
            // 始终保持在验证进度显示区域，显示所有频道的检测实况
            document.getElementById('reading-progress-container').style.display = 'none';
            document.getElementById('external-url-progress-container').style.display = 'none';
            document.getElementById('validation-progress-container').style.display = 'block';
            
            const progressFill = document.getElementById('validation-progress-fill');
            const progressPercentage = document.getElementById('validation-progress-percentage');
            const progressStats = document.getElementById('validation-progress-stats');
            
            // 计算总进度（基于已处理的频道数，不区分阶段）
            const totalChannels = data.total_channels || 0;
            const processedChannels = data.processed || 0;
            const progress = totalChannels > 0 ? Math.round((processedChannels / totalChannels) * 100) : 0;
            
            if (progressFill) progressFill.style.width = progress + '%';
            if (progressPercentage) progressPercentage.textContent = progress + '%';
            if (progressStats) progressStats.textContent = `${processedChannels}/${totalChannels} 频道`;
            
            // 更新计数器逻辑
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
                const validCountEl = document.getElementById('valid-count');
                const resolutionValidCountEl = document.getElementById('resolution-valid-count');
                const invalidCountEl = document.getElementById('invalid-count');
                const timeoutCountEl = document.getElementById('timeout-count');
                
                if (validCountEl) validCountEl.textContent = validCount;
                if (resolutionValidCountEl) resolutionValidCountEl.textContent = resolutionValidCount;
                if (invalidCountEl) invalidCountEl.textContent = invalidCount;
                if (timeoutCountEl) timeoutCountEl.textContent = timeoutCount;
            }
            
            // 只在收到实际验证结果时添加到表格
            if (data.channel) {
                // 忽略虚拟频道
                if (data.channel.name === '完成解析文件') {
                    console.log('忽略虚拟频道：', data.channel.name);
                }
                // 解析阶段显示频道名称（标记为待验证）
                else if (data.stage === 'parsing' && data.channel.url) {
                    addResultToTable(data.channel);
                }
                // 验证阶段显示检测结果
                else if ((data.stage === 'validation' || data.stage === 'validation_started') && data.channel.url) {
                    addResultToTable(data.channel);
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
            
            // 使用后端返回的最终统计更新显示
            const validCountEl = document.getElementById('valid-count');
            const resolutionValidCountEl = document.getElementById('resolution-valid-count');
            const invalidCountEl = document.getElementById('invalid-count');
            
            if (data.valid_count !== undefined && validCountEl) {
                validCountEl.textContent = data.valid_count;
            }
            if (data.resolution_valid_count !== undefined && resolutionValidCountEl) {
                resolutionValidCountEl.textContent = data.resolution_valid_count;
            }
            if (data.invalid_count !== undefined && invalidCountEl) {
                invalidCountEl.textContent = data.invalid_count;
            }
            
            // 更新所有仍显示"检测中"的行
            const checkingRows = document.querySelectorAll('#results-table-body tr');
            checkingRows.forEach(row => {
                const validCell = row.querySelector('td:nth-child(3)');
                if (validCell && validCell.textContent === '检测中') {
                    validCell.textContent = '未知';
                    validCell.className = 'unknown';
                }
            });
            
            // 显示完成信息
            const message = `验证完成！总频道数: ${data.total_channels}, 有效频道数: ${data.valid_count || data.valid_channels}`;
            const saveButton = `<a href="/download/${data.output_file}" class="btn btn-primary" style="margin-top: 15px; display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #8e9bef 100%); color: white; text-decoration: none; border-radius: 5px; cursor: pointer;">保存有效直播源</a>`;
            
            // 创建完成提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result success';
            resultDiv.innerHTML = '<p>' + message + '</p>' + saveButton;
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
            console.log('验证停止:', data);
            console.log('output_file:', data.output_file);
            console.log('valid_count:', data.valid_count);
            
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
            if (progressFill) progressFill.style.width = '0%';
            if (progressPercentage) progressPercentage.textContent = '0%';
            if (progressStats) progressStats.textContent = '0/0 频道';
            
            // 重置进度统计计数器
            validCount = 0;
            resolutionValidCount = 0;
            invalidCount = 0;
            timeoutCount = 0;
            
            // 重置统计显示
            const validCountEl = document.getElementById('valid-count');
            const resolutionValidCountEl = document.getElementById('resolution-valid-count');
            const invalidCountEl = document.getElementById('invalid-count');
            const timeoutCountEl = document.getElementById('timeout-count');
            
            if (validCountEl) validCountEl.textContent = '0';
            if (resolutionValidCountEl) resolutionValidCountEl.textContent = '0';
            if (invalidCountEl) invalidCountEl.textContent = '0';
            if (timeoutCountEl) timeoutCountEl.textContent = '0';
            
            // 创建停止提示
            const container = document.querySelector('.container');
            const resultDiv = document.createElement('div');
            resultDiv.className = 'result';
            let html = '<p>' + data.message + '</p>';
            if (data.output_file) {
                const validCount = data.valid_count || 0;
                html += `<p style="color: #28a745; margin-top: 10px;">已保存 ${validCount} 个有效频道</p>`;
                html += `<a href="/download/${data.output_file}" class="btn btn-primary" style="margin-top: 15px; display: inline-block; padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #8e9bef 100%); color: white; text-decoration: none; border-radius: 5px; cursor: pointer;">保存有效直播源</a>`;
            }
            resultDiv.innerHTML = html;
            container.appendChild(resultDiv);
        });
        
        // 添加结果到表格
        function addResultToTable(result) {
            const tbody = document.getElementById('results-table-body');
            
            // 检查必要字段，处理不完整数据
            if (!result || !result.name) {
                console.log('跳过无效频道数据:', result);
                return;
            }
            
            const row = document.createElement('tr');
            
            // 存储原始索引用于排序，默认使用频道名称的哈希值或当前时间戳
            const originalIndex = result.original_index !== undefined ? result.original_index : 
                (result.name ? result.name.charCodeAt(0) * 1000 + (result.url ? result.url.length : 0) : Date.now());
            row.dataset.originalIndex = originalIndex;
            
            const nameCell = document.createElement('td');
            nameCell.textContent = result.name;
            
            const urlCell = document.createElement('td');
            if (result.url) {
                const urlLink = document.createElement('a');
                urlLink.href = result.url;
                urlLink.target = '_blank';
                urlLink.textContent = result.url;
                urlCell.appendChild(urlLink);
            } else {
                urlCell.textContent = '(无URL)';
                urlCell.style.color = '#999';
            }
            
            const validCell = document.createElement('td');
            if (result.status === 'timeout') {
                validCell.textContent = '超时';
                validCell.className = 'timeout';
            } else if (result.status === 'checking' || result.valid === null || result.valid === undefined) {
                // 未验证完成时显示为"检测中"
                validCell.textContent = '检测中';
                validCell.className = 'checking';
                validCell.style.color = '#667eea';
            } else if ('valid' in result) {
                validCell.textContent = result.valid ? '有效' : '无效';
                validCell.className = result.valid ? 'valid' : 'invalid';
            } else {
                validCell.textContent = '待验证';
                validCell.className = 'checking';
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
    sid = request.sid
    if DEBUG_MODE:
        logger.debug(f"WebSocket连接建立, 会话ID: {sid}")
    
    # 清除任何残留的会话状态
    clear_session_validator(sid)
    
    emit('connection_established', {
        'message': '已连接到服务器',
        'sid': sid
    })

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    sid = request.sid
    if DEBUG_MODE:
        logger.debug(f"WebSocket连接断开, 会话ID: {sid}")
    
    # 确保清理该会话的所有资源
    clear_session_validator(sid)

# 全局变量保存当前验证器实例和会话ID映射
global_validator = None
# 保存每个会话对应的验证器实例，以防止多个会话互相干扰
validator_sessions = {}

def clear_session_validator(session_id):
    """彻底清除指定会话的验证器实例和所有相关资源"""
    global validator_sessions
    if session_id in validator_sessions:
        validator = validator_sessions[session_id]
        if validator:
            try:
                if DEBUG_MODE:
                    logger.debug(f"正在清理会话 {session_id} 的验证器...")
                # 强制停止验证器
                validator.stop_requested = True
                
                # 强制取消所有活跃的future对象
                if hasattr(validator, '_active_futures'):
                    for future in list(validator._active_futures):
                        try:
                            future.cancel()
                        except Exception as e:
                            if DEBUG_MODE:
                                logger.debug(f"取消future时出错: {str(e)}")
                    validator._active_futures.clear()
                
                # 强制关闭线程池
                if hasattr(validator, '_validation_pool') and validator._validation_pool:
                    validator._validation_pool.shutdown(wait=False, cancel_futures=True)
                    validator._validation_pool = None
                
                if hasattr(validator, 'ffprobe_pool') and validator.ffprobe_pool:
                    validator.ffprobe_pool.shutdown(wait=False, cancel_futures=True)
                    validator.ffprobe_pool = None
                
                if DEBUG_MODE:
                    logger.debug(f"会话 {session_id} 的验证器资源已强制清理")
            except Exception as e:
                if DEBUG_MODE:
                    logger.debug(f"清理验证器时出错: {str(e)}")
        
        # 删除会话记录
        del validator_sessions[session_id]
        if DEBUG_MODE:
            logger.debug(f"已清除会话 {session_id} 的验证器记录")
    else:
        if DEBUG_MODE:
            logger.debug(f"会话 {session_id} 不存在验证器记录")

def get_validator_for_session(session_id):
    """获取指定会话的验证器实例"""
    global validator_sessions
    if session_id not in validator_sessions:
        validator_sessions[session_id] = None
    return validator_sessions[session_id]

def set_validator_for_session(session_id, validator):
    """为指定会话设置验证器实例"""
    global validator_sessions
    # 先清除旧验证器
    clear_session_validator(session_id)
    validator_sessions[session_id] = validator
    if DEBUG_MODE:
        logger.debug(f"为会话 {session_id} 设置新的验证器")



def run_validation(data):
    """在单独线程中执行验证过程"""
    if DEBUG_MODE:
        logger.debug("run_validation 函数开始执行")
    
    sid = data.get('sid')
    if not sid:
        if DEBUG_MODE:
            logger.debug("缺少会话ID，退出验证")
        return
        
    temp_paths = []  # 存储所有创建的临时文件路径
    
    try:
        # 获取参数
        workers = data.get('workers', 20)
        timeout = data.get('timeout', 5)
        if DEBUG_MODE:
            logger.debug(f"参数: workers={workers}, timeout={timeout}")
        
        # 生成唯一验证ID
        validation_id = data.get('validation_id', '')
        if DEBUG_MODE:
            logger.debug(f"validation_id: {validation_id}")
        
        # 首先发送验证开始事件，让前端准备好接收进度
        try:
            socketio.emit('validation_started', {
                'message': '验证过程已开始',
                'validation_id': validation_id
            }, room=sid)
            if DEBUG_MODE:
                logger.debug(f"验证开始事件已发送, validation_id: {validation_id}")
        except Exception as e:
            if DEBUG_MODE:
                logger.debug(f"发送验证开始事件失败: {str(e)}")
        
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
                if DEBUG_MODE:
                    logger.debug(f"发送进度事件时出错: {str(e)}")
        
        # 根据验证类型处理
        if data.get('type') == 'file':
            if DEBUG_MODE:
                logger.debug("开始处理文件验证")
            # 处理文件验证
            file_data = data.get('file_data')
            if not file_data:
                if DEBUG_MODE:
                    logger.debug("文件数据为空")
                socketio.emit('validation_error', {'message': '文件数据为空'}, room=sid)
                return
            
            try:
                # 解码文件内容
                if DEBUG_MODE:
                    logger.debug(f"开始解码文件内容，数据长度: {len(file_data.get('content', ''))}")
                file_bytes = base64.b64decode(file_data['content'])
                if DEBUG_MODE:
                    logger.debug(f"文件解码成功，大小: {len(file_bytes)} bytes")
            except Exception as decode_error:
                if DEBUG_MODE:
                    logger.debug(f"文件解码失败: {str(decode_error)}")
                socketio.emit('validation_error', {'message': f'文件解码失败: {str(decode_error)}'}, room=sid)
                return
            
            # 安全地创建临时文件
            try:
                if DEBUG_MODE:
                    logger.debug("开始创建临时文件")
                # 使用tempfile模块的安全临时文件创建方式
                with tempfile.NamedTemporaryFile(mode='wb', suffix=file_data['extension'], 
                                                delete=False, dir=tempfile.gettempdir()) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(file_bytes)
                
                # 设置安全的文件权限（仅所有者可读写）
                os.chmod(temp_path, 0o600)
                temp_paths.append(temp_path)
                if DEBUG_MODE:
                    logger.debug(f"临时文件路径: {temp_path}")
                if DEBUG_MODE:
                    logger.debug(f"临时文件写入完成: {temp_path}")
            except Exception as file_error:
                if DEBUG_MODE:
                    logger.debug(f"创建临时文件失败: {str(file_error)}")
                socketio.emit('validation_error', {'message': f'创建临时文件失败: {str(file_error)}'}, room=sid)
                return
                
            # 确保output目录存在
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_dir = os.path.join(script_dir, 'output')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                if DEBUG_MODE:
                    logger.debug(f"已创建output目录: {output_dir}")
                
            # 执行验证，将引用保存在局部变量中
            original_filename = file_data.get('filename', f'uploaded{file_data["extension"]}')
            if DEBUG_MODE:
                logger.debug(f"开始创建IPTVValidator，文件路径: {temp_path}")
            
            try:
                # 为当前会话创建一个新的验证器
                local_validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout, 
                                              original_filename=original_filename, 
                                              filter_no_audio=data.get('filter_no_audio', False), 
                                              validation_id=data.get('validation_id'))
                
                # 将验证器关联到当前会话
                set_validator_for_session(sid, local_validator)
                if DEBUG_MODE:
                    logger.debug(f"IPTVValidator创建完成, 文件类型: {local_validator.file_type}")
            except Exception as validator_error:
                if DEBUG_MODE:
                    logger.debug(f"创建验证器失败: {str(validator_error)}")
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
            
            if DEBUG_MODE:
                logger.debug(f"开始解析文件: {local_validator.file_type}")
            # 根据文件类型解析文件内容
            try:
                if local_validator.file_type == 'm3u':
                    if DEBUG_MODE:
                        logger.debug("调用 read_m3u_file")
                    local_validator.read_m3u_file(progress_callback=thread_safe_progress_callback)
                elif local_validator.file_type == 'json':
                    if DEBUG_MODE:
                        logger.debug("调用 read_json_file")
                    local_validator.read_json_file(progress_callback=thread_safe_progress_callback)
                else:
                    if DEBUG_MODE:
                        logger.debug("调用 read_txt_file")
                    local_validator.read_txt_file(progress_callback=thread_safe_progress_callback)
                
                if DEBUG_MODE:
                    logger.debug(f"文件解析完成, 找到 {len(local_validator.channels)} 个频道")
            except Exception as parse_error:
                if DEBUG_MODE:
                    logger.debug(f"文件解析失败: {str(parse_error)}")
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
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                if DEBUG_MODE:
                    logger.debug(f"停止时output_file: {output_file}, valid_count: {valid_count}")
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id,
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                return
                
            # 执行验证
            local_validator.validate_channels(progress_callback=thread_safe_progress_callback)
            
            # 计算有效频道数
            valid_count = sum(1 for r in local_validator.all_results if r['valid'])
            valid_channels = [r for r in local_validator.all_results if r['valid']]
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                if DEBUG_MODE:
                    logger.debug(f"停止时output_file: {output_file}, valid_count: {valid_count}")
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id,
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                return
            
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            if DEBUG_MODE:
                logger.debug(f"输出文件: {output_file}")
            
            # 发送验证完成事件
            try:
                socketio.emit('validation_completed', {
                    'message': '验证完成',
                    'total_channels': len(local_validator.channels),
                    'valid_channels': len(valid_channels),
                    'valid_count': valid_count,
                    'invalid_count': len(local_validator.channels) - valid_count,
                    'resolution_valid_count': sum(1 for r in valid_channels if r.get('resolution')),
                    'output_file': output_file,
                    'validation_id': validation_id
                }, room=sid)
                if DEBUG_MODE:
                    logger.debug("验证完成事件已发送")
            except Exception as e:
                if DEBUG_MODE:
                    logger.debug(f"发送验证完成事件失败: {str(e)}")
            
        elif data.get('type') == 'url':
            # 处理URL验证
            urls = data.get('urls')
            category = data.get('category', '默认分类')
            if not urls:
                socketio.emit('validation_error', {'message': 'URL列表为空'}, room=sid)
                return
                
            # 安全地创建临时文件
            try:
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.m3u', 
                                                delete=False, dir=tempfile.gettempdir()) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(b'#EXTM3U\n')
                    for line in urls.strip().split('\n'):
                        line = line.strip()
                        if line and ',' in line:
                            try:
                                name, url = line.split(',', 1)
                                if name.strip() and url.strip():
                                    temp_file.write(f'#EXTINF:-1 group-title="{category}",{name.strip()}\n{url.strip()}\n'.encode('utf-8'))
                            except ValueError:
                                # 处理分割错误，跳过无效行
                                continue
                
                # 设置安全的文件权限（仅所有者可读写）
                os.chmod(temp_path, 0o600)
                temp_paths.append(temp_path)  # 添加到临时文件列表
            except Exception as temp_error:
                socketio.emit('validation_error', {'message': f'创建临时文件失败: {str(temp_error)}'}, room=sid)
                return
                
            local_validator = IPTVValidator(temp_path, max_workers=workers, timeout=timeout, original_filename="url_channels.m3u", filter_no_audio=data.get('filter_no_audio', False), validation_id=data.get('validation_id'))
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
            
            # 计算有效频道数
            valid_count = sum(1 for r in local_validator.all_results if r['valid'])
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                if DEBUG_MODE:
                    logger.debug(f"停止时output_file: {output_file}, valid_count: {valid_count}")
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id,
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                return
            
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            if DEBUG_MODE:
                logger.debug(f"输出文件: {output_file}")
            
            # 发送验证完成事件
            try:
                socketio.emit('validation_completed', {
                    'message': '验证完成',
                    'total_channels': len(local_validator.channels),
                    'valid_channels': len(valid_channels),
                    'valid_count': valid_count,
                    'invalid_count': len(local_validator.channels) - valid_count,
                    'resolution_valid_count': sum(1 for r in local_validator.all_results if r['valid'] and r.get('resolution')),
                    'output_file': output_file,
                    'validation_id': validation_id
                }, room=sid)
                if DEBUG_MODE:
                    logger.debug("验证完成事件已发送")
            except Exception as e:
                if DEBUG_MODE:
                    logger.debug(f"发送验证完成事件失败: {str(e)}")
            
        elif data.get('type') == 'network':
            # 处理网络源验证
            url = data.get('url')
            if not url:
                socketio.emit('validation_error', {'message': '网络源URL为空'}, room=sid)
                return
                
            local_validator = IPTVValidator(url, max_workers=workers, timeout=timeout, filter_no_audio=data.get('filter_no_audio', False), validation_id=data.get('validation_id'))
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
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                if DEBUG_MODE:
                    logger.debug(f"停止时output_file: {output_file}, valid_count: {valid_count}")
                # 发送停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id,
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                return
                
            valid_channels = local_validator.validate_channels(progress_callback=thread_safe_progress_callback)
            
            # 计算有效频道数
            valid_count = sum(1 for r in local_validator.all_results if r['valid'])
            
            # 检查是否请求停止
            if local_validator.stop_requested:
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                if DEBUG_MODE:
                    logger.debug(f"停止时output_file: {output_file}, valid_count: {valid_count}")
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': validation_id,
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                return
            
            # 生成输出文件
            output_file = os.path.basename(local_validator.generate_output_files())
            if DEBUG_MODE:
                logger.debug(f"输出文件: {output_file}")
            
            # 发送验证完成事件
            try:
                socketio.emit('validation_completed', {
                    'message': '验证完成',
                    'total_channels': len(local_validator.channels),
                    'valid_channels': len(valid_channels),
                    'valid_count': valid_count,
                    'invalid_count': len(local_validator.channels) - valid_count,
                    'resolution_valid_count': sum(1 for r in local_validator.all_results if r['valid'] and r.get('resolution')),
                    'output_file': output_file,
                    'validation_id': validation_id
                }, room=sid)
                if DEBUG_MODE:
                    logger.debug("验证完成事件已发送")
            except Exception as e:
                if DEBUG_MODE:
                    logger.debug(f"发送验证完成事件失败: {str(e)}")
            
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
    if DEBUG_MODE:
        logger.debug(f"收到验证请求: {data.get('type')}")
    
    # 获取当前会话ID
    sid = request.sid
    if DEBUG_MODE:
        logger.debug(f"start_validation 会话ID: {sid}")
    
    # 立即清理当前会话的所有资源
    if DEBUG_MODE:
        logger.debug("立即清理当前会话的所有资源")
    clear_session_validator(sid)
    
    # 获取验证ID
    validation_id = data.get('validation_id', '')
    if DEBUG_MODE:
        logger.debug(f"validation_id: {validation_id}")
    
    # 发送验证开始事件到正确的房间
    socketio.emit('validation_started', {
        'message': '验证过程已开始',
        'validation_id': validation_id
    }, room=sid)
    if DEBUG_MODE:
        logger.debug("验证开始消息已发送")
    
    # 将当前会话ID添加到数据中，以便在单独线程中可以发送事件到正确的客户端
    data['sid'] = sid
    
    if DEBUG_MODE:
        logger.debug(f"启动验证线程，会话ID: {sid}")
    # 在单独线程中执行验证逻辑，避免阻塞WebSocket事件处理
    validation_thread = threading.Thread(target=run_validation, args=(data,))
    validation_thread.daemon = True  # 设置为守护线程，以便在服务器关闭时自动退出
    validation_thread.start()
    if DEBUG_MODE:
        logger.debug("验证线程已启动")

@socketio.on('stop_validation')
def stop_validation():
    """停止验证过程"""
    if DEBUG_MODE:
        logger.debug(f"收到停止验证请求，会话ID: {request.sid}")
    
    # 获取当前会话ID
    sid = request.sid
    
    # 检查当前会话是否有活跃的验证器
    output_file = None
    valid_count = 0
    
    if sid in validator_sessions:
        local_validator = validator_sessions[sid]
        if local_validator:
            try:
                # 停止验证器并获取输出文件
                output_file = local_validator.stop()
                valid_count = sum(1 for r in local_validator.all_results if r['valid'])
                output_basename = os.path.basename(output_file) if output_file else None
                
                if DEBUG_MODE:
                    logger.debug(f"停止验证器 - output_file: {output_file}, valid_count: {valid_count}")
                
                # 发送停止消息包含有效结果信息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': '',
                    'output_file': output_basename,
                    'valid_count': valid_count
                }, room=sid)
                
            except Exception as e:
                if DEBUG_MODE:
                    logger.debug(f"停止验证器时出错: {str(e)}")
                # 即使出错也发送基本停止消息
                socketio.emit('validation_stopped', {
                    'message': '验证过程已停止',
                    'validation_id': ''
                }, room=sid)
        else:
            # 验证器为空，发送基本停止消息
            socketio.emit('validation_stopped', {
                'message': '验证过程已停止',
                'validation_id': ''
            }, room=sid)
    else:
        # 没有活跃验证器
        socketio.emit('validation_stopped', {
            'message': '验证过程已停止',
            'validation_id': ''
        }, room=sid)
    
    # 强制清理当前会话的所有资源
    clear_session_validator(sid)
    
    if DEBUG_MODE:
        logger.debug(f"验证停止处理完成, 会话ID: {sid}")

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