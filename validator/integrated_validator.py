#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具 - 整合版
功能：整合多个窗口功能为单一EXE应用程序
特点：包含文件选择、验证设置、进度显示、结果展示等所有功能
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import json
import tempfile
import logging
import subprocess
import re
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入核心验证模块
try:
    from validator.iptv_validator import IPTVValidator, validate_ipTV
    from validator.vlc_detector import VLCStreamDetectorV2
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from quick_url_checker import QuickURLChecker, create_quick_checker
    QUICK_CHECKER_AVAILABLE = True
except ImportError as e:
    print(f"导入警告: {e}")
    QUICK_CHECKER_AVAILABLE = False

class IntegratedValidatorApp:
    """整合版直播源验证器应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("直播源有效性验证工具 - 整合版 v2.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 验证状态
        self.is_validating = False
        self.validation_thread = None
        self.cancel_validation = False
        
        # 结果数据
        self.validation_results = []
        self.valid_channels = {}
        self.invalid_channels = {}
        self.original_channels = {}  # 保留原始频道分类和顺序
        
        # 配置参数
        self.config = {
            'timeout': 5,
            'workers': 30,
            'enable_vlc': True,
            'enable_quick_check': True,
            'batch_threshold': 50,
            'enable_resolution_detection': True,  # 新增：启用分辨率检测
            'skip_resolution_detection': False   # 新增：跳过分辨率检测
        }
        
        self.setup_ui()
        self.setup_logging()
        self.check_ffprobe_available()
        self.update_ffprobe_status()
        
    def check_ffprobe_available(self):
        """检查ffprobe是否可用"""
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, 
                                  timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.ffprobe_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self.ffprobe_available = False
        
        self.logger.info(f"ffprobe可用性检查: {'可用' if self.ffprobe_available else '不可用'}")
        
    def update_ffprobe_status(self):
        """更新ffprobe状态显示"""
        if hasattr(self, 'ffprobe_status_var'):
            if self.ffprobe_available:
                self.ffprobe_status_var.set("✓ ffprobe可用")
            else:
                self.ffprobe_status_var.set("✗ ffprobe不可用，分辨率检测将受限")
        
    def _get_resolution_from_hls(self, url, timeout, headers=None):
        """从HLS播放列表中提取分辨率信息"""
        try:
            session = requests.Session()
            response = session.get(url, timeout=min(timeout, 15), headers=headers, allow_redirects=True)
            if response.status_code != 200:
                return None, None, {}

            content = response.text
            re_resolution = re.compile(r'#EXT-X-STREAM-INF.*?RESOLUTION=(\d+)x(\d+)', re.IGNORECASE | re.DOTALL)
            matches = re_resolution.findall(content)

            if matches:
                max_height = 0
                best_width = 0
                for width, height in matches:
                    h = int(height)
                    w = int(width)
                    if h > max_height and h > 0 and w > 0:
                        max_height = h
                        best_width = w
                if max_height > 0:
                    return f"{best_width}*{max_height}", 'hls', {'source': 'hls_playlist'}
                return None, None, {}

            return None, None, {}
        except Exception as e:
            self.logger.debug(f"HLS分辨率检测失败: {e}")
            return None, None, {}

    def _ffprobe_get_resolution(self, url, timeout, headers=None, retry=2):
        """使用ffprobe获取分辨率"""
        if not self.ffprobe_available:
            return None, None, {'error': 'ffprobe_unavailable'}

        try:
            # 清理URL，移除认证信息
            clean_url = url
            if '$' in url:
                dollar_match = re.search(r'\$[^$]+$', url)
                if dollar_match:
                    auth_part = dollar_match.group(0)
                    clean_url = url[:url.rfind(auth_part)]

            timeout_us = int(timeout * 1000000)
            
            cmd = [
                'ffprobe', '-v', 'error',
                '-timeout', str(timeout_us),
                '-analyzeduration', str(timeout_us),
                '-probesize', str(5 * 1024 * 1024),
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,codec_name',
                '-of', 'json',
                clean_url
            ]

            if headers:
                cmd.extend([
                    '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0")}\r\n'
                ])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 1,
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if 'streams' in data and len(data['streams']) > 0:
                        stream = data['streams'][0]
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        codec = stream.get('codec_name', 'unknown')
                        if width and height and width > 0 and height > 0:
                            return f"{width}*{height}", codec, {'source': 'ffprobe'}
                except json.JSONDecodeError:
                    pass

            return None, None, {}
        except Exception as e:
            self.logger.debug(f"ffprobe分辨率检测失败: {e}")
            return None, None, {}

    def _extract_resolution_from_url(self, url):
        """从URL中提取分辨率信息"""
        try:
            # 分辨率标注提取： [1920*1080]
            re_resolution = re.compile(r'\[(\d+\*\d+)\]')
            match = re_resolution.search(url)
            if match:
                return match.group(1)
            
            # URL参数中的分辨率：$1920x1080
            re_dollar = re.compile(r'\$(\d+)x(\d+)')
            match = re_dollar.search(url)
            if match:
                return f"{match.group(1)}*{match.group(2)}"
            
            # URL参数：?resolution=1920x1080
            re_param = re.compile(r'[?&]resolution=(\d+)[x*](\d+)', re.IGNORECASE)
            match = re_param.search(url)
            if match:
                return f"{match.group(1)}*{match.group(2)}"
                
            return None
        except Exception:
            return None

    def get_resolution_info(self, url, timeout=None):
        """获取视频分辨率信息"""
        if not self.config['enable_resolution_detection'] or self.config['skip_resolution_detection']:
            return None, None, {}
        
        if timeout is None:
            timeout = self.config['timeout']
            
        try:
            # 首先尝试从URL中提取分辨率信息
            url_resolution = self._extract_resolution_from_url(url)
            if url_resolution:
                return url_resolution, 'url_inference', {'source': 'url_extraction'}
            
            # HLS播放列表检测
            if url.lower().endswith(('.m3u8', '.m3u')) or '/hls/' in url.lower():
                resolution = self._get_resolution_from_hls(url, timeout)
                if resolution and resolution[0]:
                    return resolution
            
            # ffprobe检测
            if self.ffprobe_available:
                resolution = self._ffprobe_get_resolution(url, timeout)
                if resolution and resolution[0]:
                    return resolution
                    
            return None, None, {}
        except Exception as e:
            self.logger.debug(f"分辨率检测失败: {e}")
            return None, None, {}
        
    def setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('validator_integrated.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="选择文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(file_frame, text="浏览", command=self.select_file).grid(row=0, column=2)
        
        # 文件格式说明
        format_label = ttk.Label(file_frame, text="支持格式: M3U, M3U8, TXT", foreground="gray")
        format_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 验证设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="验证设置", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # 超时设置
        ttk.Label(settings_frame, text="超时时间(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.timeout_var = tk.IntVar(value=5)
        timeout_spinbox = ttk.Spinbox(settings_frame, from_=1, to=30, textvariable=self.timeout_var, width=10)
        timeout_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 并发数设置
        ttk.Label(settings_frame, text="并发数:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.workers_var = tk.IntVar(value=30)
        workers_spinbox = ttk.Spinbox(settings_frame, from_=1, to=100, textvariable=self.workers_var, width=10)
        workers_spinbox.grid(row=0, column=3, sticky=tk.W)
        
        # 验证选项
        options_frame = ttk.Frame(settings_frame)
        options_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.enable_vlc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="启用VLC检测", variable=self.enable_vlc_var).pack(side=tk.LEFT, padx=(0, 20))
        
        self.enable_quick_check_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="启用快速检测", variable=self.enable_quick_check_var).pack(side=tk.LEFT, padx=(0, 20))
        
        if not QUICK_CHECKER_AVAILABLE:
            self.enable_quick_check_var.set(False)
            self.enable_quick_check_var.config(state="disabled")
        
        # 分辨率检测选项
        resolution_frame = ttk.Frame(settings_frame)
        resolution_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.enable_resolution_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(resolution_frame, text="启用分辨率检测", variable=self.enable_resolution_var).pack(side=tk.LEFT, padx=(0, 20))
        
        # 显示ffprobe可用性状态
        self.ffprobe_status_var = tk.StringVar(value="检查ffprobe状态...")
        ffprobe_label = ttk.Label(resolution_frame, textvariable=self.ffprobe_status_var, foreground="gray")
        ffprobe_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="开始验证", command=self.start_validation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止验证", command=self.stop_validation, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="清除结果", command=self.clear_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="保存结果", command=self.save_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="使用说明", command=self.show_help).pack(side=tk.LEFT, padx=(20, 0))
        
        # 进度显示区域
        progress_frame = ttk.LabelFrame(main_frame, text="验证进度", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 统计信息
        self.stats_var = tk.StringVar(value="总频道: 0 | 有效: 0 | 无效: 0")
        ttk.Label(progress_frame, textvariable=self.stats_var).grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # 结果显示区域
        results_frame = ttk.LabelFrame(main_frame, text="验证结果", padding="10")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 创建Notebook用于切换结果视图
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 有效结果标签页
        self.valid_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.valid_text, text="有效频道")
        
        # 无效结果标签页
        self.invalid_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.invalid_text, text="无效频道")
        
        # 日志显示标签页
        self.log_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.log_text, text="运行日志")
        
    def select_file(self):
        """选择文件"""
        filetypes = [
            ("直播源文件", "*.m3u *.m3u8 *.txt"),
            ("M3U文件", "*.m3u *.m3u8"),
            ("TXT文件", "*.txt"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择直播源文件",
            filetypes=filetypes
        )
        
        if filename:
            self.file_path_var.set(filename)
            
    def start_validation(self):
        """开始验证"""
        if self.is_validating:
            messagebox.showwarning("警告", "验证正在进行中")
            return
            
        file_path = self.file_path_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请先选择有效的文件")
            return
            
        # 更新配置
        self.config['timeout'] = self.timeout_var.get()
        self.config['workers'] = self.workers_var.get()
        self.config['enable_vlc'] = self.enable_vlc_var.get()
        self.config['enable_quick_check'] = self.enable_quick_check_var.get() and QUICK_CHECKER_AVAILABLE
        self.config['enable_resolution_detection'] = self.enable_resolution_var.get()
        self.config['skip_resolution_detection'] = not self.enable_resolution_var.get()
        
        # 重置状态
        self.cancel_validation = False
        self.validation_results = []
        self.valid_channels = {}
        self.invalid_channels = {}
        self.original_channels = {}  # 保留原始频道分类和顺序
        
        # 更新UI状态
        self.is_validating = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set("准备验证...")
        self.progress_bar.config(value=0)
        self.update_stats()
        self.clear_results_display()
        
        # 启动验证线程
        self.validation_thread = threading.Thread(target=self.run_validation, args=(file_path,), daemon=True)
        self.validation_thread.start()
        
    def stop_validation(self):
        """停止验证"""
        if self.is_validating:
            self.cancel_validation = True
            self.progress_var.set("正在停止...")
            
    def run_validation(self, file_path):
        """运行验证（在线程中执行）"""
        try:
            self.logger.info(f"开始验证文件: {file_path}")
            self.log_message(f"开始验证文件: {file_path}")
            
            # 解析文件并保存原始频道分类和顺序
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in ['.m3u', '.m3u8']:
                channels = self.parse_m3u_file(file_path)
                self.original_channels = {cat: list(channels[cat]) for cat in channels}  # 深拷贝
            elif file_ext == '.txt':
                channels = self.parse_txt_file(file_path)
                self.original_channels = {cat: list(channels[cat]) for cat in channels}  # 深拷贝
            else:
                raise ValueError(f"不支持的文件格式: {file_ext}")
            
            total_channels = sum(len(channel_list) for channel_list in channels.values())
            self.logger.info(f"解析到 {total_channels} 个频道")
            self.log_message(f"解析到 {total_channels} 个频道")
            
            if total_channels == 0:
                self.log_message("没有找到有效的频道")
                return
            
            # 更新进度
            self.update_progress(0, total_channels, "开始验证...")
            
            # 验证频道
            if self.config['enable_quick_check'] and total_channels > self.config['batch_threshold']:
                self.validate_with_quick_checker(channels)
            else:
                self.validate_traditional(channels)
                
        except Exception as e:
            self.logger.error(f"验证过程出错: {e}")
            self.log_message(f"验证过程出错: {e}")
        finally:
            # 完成验证
            self.is_validating = False
            self.root.after(0, self.validation_completed)
            
    def parse_m3u_file(self, file_path):
        """解析M3U文件"""
        channels = {}
        current_category = "默认"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith('#EXTINF:'):
                        # 提取频道信息
                        parts = line.split(',')
                        if len(parts) > 1:
                            channel_name = parts[-1].strip()
                        else:
                            channel_name = "未知频道"
                    elif line.startswith('http://') or line.startswith('https://'):
                        # URL行
                        url = line.strip()
                        if current_category not in channels:
                            channels[current_category] = []
                        channels[current_category].append((channel_name, url))
                        
            return channels
            
        except Exception as e:
            self.logger.error(f"解析M3U文件失败: {e}")
            raise
            
    def parse_txt_file(self, file_path):
        """解析TXT文件"""
        channels = {}
        current_category = "默认"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 处理分类标记 [分类名]
                    if line.startswith('[') and line.endswith(']'):
                        current_category = line[1:-1].strip()
                        if current_category not in channels:
                            channels[current_category] = []
                        continue
                    
                    # 跳过注释行
                    if line.startswith('#'):
                        continue
                        
                    # 解析频道行 频道名,URL
                    parts = line.split(',')
                    if len(parts) >= 2:
                        channel_name = parts[0].strip()
                        url = parts[1].strip()
                        
                        if current_category not in channels:
                            channels[current_category] = []
                        channels[current_category].append((channel_name, url))
                        
            return channels
            
        except Exception as e:
            self.logger.error(f"解析TXT文件失败: {e}")
            raise
            
    def validate_with_quick_checker(self, channels):
        """使用快速检测器验证"""
        try:
            self.log_message("使用快速检测器进行验证...")
            
            # 准备URL列表
            all_channel_items = []
            for category, channel_list in channels.items():
                for channel_name, url in channel_list:
                    all_channel_items.append((category, channel_name, url))
            
            urls = [item[2] for item in all_channel_items]
            
            # 创建快速检测器
            checker = create_quick_checker(
                timeout=self.config['timeout'],
                max_workers=self.config['workers'],
                enable_dns_check=True
            )
            
            # 批量检测
            results = checker.batch_check(urls, show_progress=False)
            
            # 处理结果
            for i, result in enumerate(results):
                if self.cancel_validation:
                    break
                    
                category, channel_name, url = all_channel_items[i]
                
                if result['valid']:
                    # 获取分辨率信息
                    resolution_info = None
                    if self.config['enable_resolution_detection']:
                        try:
                            resolution, codec, metadata = self.get_resolution_info(url)
                            resolution_info = resolution
                            if resolution:
                                self.log_message(f"{channel_name}: {resolution} ({codec})")
                        except Exception as e:
                            self.logger.debug(f"分辨率检测失败: {e}")
                    
                    if category not in self.valid_channels:
                        self.valid_channels[category] = []
                    
                    # 保存频道信息，包含分辨率
                    channel_info = [channel_name, url]
                    if resolution_info:
                        channel_info.append(resolution_info)
                    self.valid_channels[category].append(tuple(channel_info))
                else:
                    if category not in self.invalid_channels:
                        self.invalid_channels[category] = []
                    self.invalid_channels[category].append((channel_name, url, result.get('reason', 'Unknown')))
                
                # 更新进度
                processed = i + 1
                total = len(results)
                self.update_progress(processed, total, f"快速检测进度: {processed}/{total}")
                
            self.log_message("快速检测完成")
            
        except Exception as e:
            self.logger.error(f"快速检测失败: {e}")
            self.log_message(f"快速检测失败: {e}")
            # 回退到传统检测
            self.validate_traditional(channels)
            
    def validate_traditional(self, channels):
        """传统验证方法"""
        try:
            self.log_message("使用传统方法进行验证...")
            
            total_processed = 0
            total_channels = sum(len(channel_list) for channel_list in channels.values())
            
            for category, channel_list in channels.items():
                for channel_name, url in channel_list:
                    if self.cancel_validation:
                        break
                        
                    try:
                        # 简单HTTP检查
                        import requests
                        response = requests.head(url, timeout=self.config['timeout'], allow_redirects=True)
                        is_valid = response.status_code < 400
                        reason = f"HTTP {response.status_code}" if not is_valid else "Valid"
                        
                    except Exception as e:
                        is_valid = False
                        reason = str(e)[:50]
                    
                    if is_valid:
                        # 获取分辨率信息
                        resolution_info = None
                        if self.config['enable_resolution_detection']:
                            try:
                                resolution, codec, metadata = self.get_resolution_info(url)
                                resolution_info = resolution
                                if resolution:
                                    self.log_message(f"{channel_name}: {resolution} ({codec})")
                            except Exception as e:
                                self.logger.debug(f"分辨率检测失败: {e}")
                        
                        if category not in self.valid_channels:
                            self.valid_channels[category] = []
                        
                        # 保存频道信息，包含分辨率
                        channel_info = [channel_name, url]
                        if resolution_info:
                            channel_info.append(resolution_info)
                        self.valid_channels[category].append(tuple(channel_info))
                    else:
                        if category not in self.invalid_channels:
                            self.invalid_channels[category] = []
                        self.invalid_channels[category].append((channel_name, url, reason))
                    
                    total_processed += 1
                    self.update_progress(total_processed, total_channels, f"验证进度: {total_processed}/{total_channels}")
                    
        except Exception as e:
            self.logger.error(f"传统验证失败: {e}")
            self.log_message(f"传统验证失败: {e}")
            
    def update_progress(self, current, total, message=""):
        """更新进度显示 - 修复多线程UI更新问题"""
        def update():
            try:
                percentage = (current / total * 100) if total > 0 else 0
                self.progress_bar.config(value=percentage)
                if message:
                    self.progress_var.set(message)
                else:
                    self.progress_var.set(f"进度: {current}/{total} ({percentage:.1f}%)")
                self.update_stats()
                # 强制刷新UI
                self.root.update_idletasks()
            except Exception as e:
                # 静默处理错误，避免影响验证过程
                print(f"进度更新错误: {e}")
                
        # 使用更低延迟确保UI更新
        self.root.after(50, update)
        
    def update_stats(self):
        """更新统计信息"""
        valid_count = sum(len(channels) for channels in self.valid_channels.values())
        invalid_count = sum(len(channels) for channels in self.invalid_channels.values())
        total_count = valid_count + invalid_count
        
        stats_text = f"总频道: {total_count} | 有效: {valid_count} | 无效: {invalid_count}"
        self.stats_var.set(stats_text)
        
    def validation_completed(self):
        """验证完成回调"""
        self.is_validating = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if self.cancel_validation:
            self.progress_var.set("验证已取消")
            self.log_message("验证已取消")
        else:
            self.progress_var.set("验证完成")
            self.log_message("验证完成")
            
        # 显示结果
        self.display_results()
        
    def clear_results(self):
        """清除结果"""
        self.validation_results = []
        self.valid_channels = {}
        self.invalid_channels = {}
        self.progress_var.set("就绪")
        self.progress_bar.config(value=0)
        self.update_stats()
        self.clear_results_display()
        
    def clear_results_display(self):
        """清除结果显示"""
        self.valid_text.config(state="normal")
        self.valid_text.delete(1.0, tk.END)
        self.valid_text.config(state="disabled")
        
        self.invalid_text.config(state="normal")
        self.invalid_text.delete(1.0, tk.END)
        self.invalid_text.config(state="disabled")
        
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
    def display_results(self):
        """显示验证结果"""
        # 显示有效频道
        self.valid_text.config(state="normal")
        self.valid_text.delete(1.0, tk.END)
        
        for category, channels in self.valid_channels.items():
            self.valid_text.insert(tk.END, f"=== {category} ===\n")
            for channel_info in channels:
                channel_name = channel_info[0]
                url = channel_info[1]
                # 如果有分辨率信息，添加到显示
                if len(channel_info) > 2 and channel_info[2]:
                    resolution = channel_info[2]
                    self.valid_text.insert(tk.END, f"{channel_name} [{resolution}]\n{url}\n\n")
                else:
                    self.valid_text.insert(tk.END, f"{channel_name}\n{url}\n\n")
        self.valid_text.config(state="disabled")
        
        # 显示无效频道
        self.invalid_text.config(state="normal")
        self.invalid_text.delete(1.0, tk.END)
        
        for category, channels in self.invalid_channels.items():
            self.invalid_text.insert(tk.END, f"=== {category} ===\n")
            for channel_info in channels:
                channel_name = channel_info[0]
                url = channel_info[1]
                reason = channel_info[2] if len(channel_info) > 2 else "未知原因"
                self.invalid_text.insert(tk.END, f"{channel_name}\n{url}\n原因: {reason}\n\n")
        self.invalid_text.config(state="disabled")
        
    def log_message(self, message):
        """添加日志消息"""
        def update_log():
            self.log_text.config(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
            
        self.root.after(0, update_log)
        
    def save_results(self):
        """保存验证结果"""
        if not self.valid_channels and not self.invalid_channels:
            messagebox.showwarning("警告", "没有可保存的结果")
            return
            
        # 获取原始文件名（用于生成结果文件名）
        original_filename = self.file_path_var.get()
        if original_filename:
            base_name = os.path.splitext(os.path.basename(original_filename))[0]
        else:
            base_name = "验证结果"
            
        # 创建结果保存对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("保存验证结果")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="选择要保存的内容:", font=('Arial', 10, 'bold')).pack(pady=(0, 15))
        
        # 保存选项
        save_frame = ttk.Frame(main_frame)
        save_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.save_valid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(save_frame, text="保存有效频道", variable=self.save_valid_var).pack(anchor=tk.W, pady=2)
        
        self.save_invalid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(save_frame, text="保存无效频道", variable=self.save_invalid_var).pack(anchor=tk.W, pady=2)
        
        self.save_summary_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(save_frame, text="保存统计摘要", variable=self.save_summary_var).pack(anchor=tk.W, pady=2)
        
        # 文件格式选择
        format_frame = ttk.LabelFrame(main_frame, text="文件格式", padding="10")
        format_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.format_var = tk.StringVar(value="separate")
        ttk.Radiobutton(format_frame, text="分别保存（推荐）", variable=self.format_var, value="separate").pack(anchor=tk.W)
        ttk.Radiobutton(format_frame, text="合并保存", variable=self.format_var, value="combined").pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_save():
            # 检查选择
            if not self.save_valid_var.get() and not self.save_invalid_var.get():
                messagebox.showwarning("警告", "请至少选择一种内容类型")
                return
                
            # 选择保存位置
            if self.format_var.get() == "separate":
                # 分别保存，询问保存目录
                save_dir = filedialog.askdirectory(title="选择保存目录")
                if not save_dir:
                    return
                    
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                try:
                    # 保存有效频道
                    if self.save_valid_var.get() and self.valid_channels:
                        valid_file = os.path.join(save_dir, f"{base_name}_有效.txt")
                        self.save_channels_to_file(valid_file, self.valid_channels, "有效")
                        
                    # 保存无效频道
                    if self.save_invalid_var.get() and self.invalid_channels:
                        invalid_file = os.path.join(save_dir, f"{base_name}_无效.txt")
                        self.save_channels_to_file(invalid_file, self.invalid_channels, "无效", include_reason=True)
                        
                    # 保存全部结果（有效+无效频道）
                    if self.save_summary_var.get():
                        all_file = os.path.join(save_dir, f"{base_name}_全部.txt")
                        self.save_all_channels_to_file(all_file)
                        
                    messagebox.showinfo("成功", f"结果已保存到目录:\n{save_dir}")
                    dialog.destroy()
                    
                except Exception as e:
                    messagebox.showerror("错误", f"保存失败: {e}")
                    
            else:
                # 合并保存
                filename = filedialog.asksaveasfilename(
                    title="保存验证结果",
                    defaultextension=".txt",
                    filetypes=[("TXT文件", "*.txt"), ("所有文件", "*.*")]
                )
                
                if filename:
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            # 统计摘要
                            if self.save_summary_var.get():
                                self.write_summary_to_file(f)
                                f.write("\n" + "="*60 + "\n\n")
                            
                            # 有效频道
                            if self.save_valid_var.get() and self.valid_channels:
                                f.write("有效频道:\n")
                                f.write("-"*30 + "\n")
                                self.write_channels_to_file(f, self.valid_channels, include_reason=False)
                                f.write("\n\n")
                            
                            # 无效频道
                            if self.save_invalid_var.get() and self.invalid_channels:
                                f.write("无效频道:\n")
                                f.write("-"*30 + "\n")
                                self.write_channels_to_file(f, self.invalid_channels, include_reason=True)
                        
                        messagebox.showinfo("成功", f"结果已保存到: {filename}")
                        dialog.destroy()
                        
                    except Exception as e:
                        messagebox.showerror("错误", f"保存失败: {e}")
        
        ttk.Button(button_frame, text="保存", command=on_save, width=10).pack(side=tk.RIGHT, padx=(10, 0), pady=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.RIGHT, pady=5)
        
    def save_channels_to_file(self, filename, channels, channel_type, include_reason=False):
        """保存频道到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"直播源验证结果 - {channel_type}频道\n")
            f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"文件: {os.path.basename(filename)}\n")
            f.write("="*50 + "\n\n")
            
            total_count = sum(len(ch) for ch in channels.values())
            f.write(f"总计: {total_count} 个频道\n")
            f.write(f"分类数: {len(channels)}\n\n")
            
            self.write_channels_to_file(f, channels, include_reason)
            
    def write_channels_to_file(self, f, channels, include_reason=False):
        """写入频道信息到文件（按原始分类和顺序保存）"""
        # 按原始分类顺序保存结果
        for category, original_list in self.original_channels.items():
            # 检查该分类是否有结果需要保存
            if category not in channels or not channels[category]:
                continue
                
            # 写入分类标题
            f.write(f"[{category}]\n")
            
            # 获取该分类的所有频道名称和URL的映射
            result_map = {channel_info[0]: channel_info for channel_info in channels[category]}
            
            # 按原始顺序保存
            for original_channel in original_list:
                channel_name, url = original_channel[:2]
                
                # 查找验证结果
                if channel_name in result_map:
                    result_info = result_map[channel_name]
                    
                    if include_reason and len(result_info) == 3:
                        # 无效频道，保存原因
                        _, _, reason = result_info
                        f.write(f"{channel_name},{url} # {reason}\n")
                    else:
                        # 有效频道
                        f.write(f"{channel_name},{url}\n")
            
            f.write("\n")
    
    def save_summary_to_file(self, filename):
        """保存统计摘要"""
        with open(filename, 'w', encoding='utf-8') as f:
            self.write_summary_to_file(f)
    
    def save_all_channels_to_file(self, filename):
        """保存全部频道（有效+无效，按原始分类和顺序）"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"直播源验证结果 - 全部频道\n")
            f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"文件: {os.path.basename(filename)}\n")
            f.write("="*50 + "\n\n")
            
            # 统计信息
            valid_count = sum(len(channels) for channels in self.valid_channels.values())
            invalid_count = sum(len(channels) for channels in self.invalid_channels.values())
            total_count = valid_count + invalid_count
            f.write(f"总计: {total_count} 个频道\n")
            f.write(f"有效: {valid_count} 个频道\n")
            f.write(f"无效: {invalid_count} 个频道\n")
            f.write(f"有效率: {valid_count/total_count*100:.1f}%\n\n" if total_count > 0 else "有效率: 0%\n\n")
            
            # 按原始分类顺序保存
            for category, original_list in self.original_channels.items():
                # 获取该分类的验证结果
                valid_in_category = []
                invalid_in_category = []
                
                # 获取有效频道
                if category in self.valid_channels:
                    valid_map = {ch[0]: ch for ch in self.valid_channels[category]}
                    for original_ch in original_list:
                        ch_name = original_ch[0]
                        if ch_name in valid_map:
                            valid_in_category.append(valid_map[ch_name])
                
                # 获取无效频道
                if category in self.invalid_channels:
                    invalid_map = {ch[0]: ch for ch in self.invalid_channels[category]}
                    for original_ch in original_list:
                        ch_name = original_ch[0]
                        if ch_name in invalid_map:
                            invalid_in_category.append(invalid_map[ch_name])
                
                # 只有该分类有结果时才写入
                if valid_in_category or invalid_in_category:
                    f.write(f"[{category}]\n")
                    
                    # 先写入有效频道
                    for channel_info in valid_in_category:
                        channel_name, url = channel_info[:2]
                        # 如果有分辨率信息，添加到文件名
                        if len(channel_info) > 2 and channel_info[2]:
                            resolution = channel_info[2]
                            f.write(f"{channel_name},{url} [{resolution}]\n")
                        else:
                            f.write(f"{channel_name},{url}\n")
                    
                    # 再写入无效频道（包含原因）
                    for channel_info in invalid_in_category:
                        channel_name, url, reason = channel_info
                        f.write(f"{channel_name},{url} # {reason}\n")
                    
                    f.write("\n")
    
    def write_summary_to_file(self, f):
        """写入统计摘要"""
        valid_count = sum(len(channels) for channels in self.valid_channels.values())
        invalid_count = sum(len(channels) for channels in self.invalid_channels.values())
        total_count = valid_count + invalid_count
        
        f.write("直播源验证统计摘要\n")
        f.write("="*50 + "\n")
        f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总频道数: {total_count}\n")
        f.write(f"有效频道: {valid_count} ({valid_count/total_count*100:.1f}%)\n" if total_count > 0 else "有效频道: 0 (0.0%)\n")
        f.write(f"无效频道: {invalid_count} ({invalid_count/total_count*100:.1f}%)\n" if total_count > 0 else "无效频道: 0 (0.0%)\n")
        
        f.write(f"\n配置参数:\n")
        f.write(f"超时时间: {self.config['timeout']}秒\n")
        f.write(f"并发数: {self.config['workers']}\n")
        f.write(f"VLC检测: {'启用' if self.config['enable_vlc'] else '禁用'}\n")
        f.write(f"快速检测: {'启用' if self.config['enable_quick_check'] else '禁用'}\n")
        
        # 分类统计
        if self.valid_channels:
            f.write(f"\n有效频道分类:\n")
            for category, channels in self.valid_channels.items():
                f.write(f"  {category}: {len(channels)}个\n")
        
        if self.invalid_channels:
            f.write(f"\n无效频道分类:\n")
            for category, channels in self.invalid_channels.items():
                f.write(f"  {category}: {len(channels)}个\n")
                
    def show_help(self):
        """显示使用说明"""
        help_text = """直播源有效性验证工具 - 使用说明

【基本功能】
• 验证直播源文件的URL有效性
• 支持M3U、M3U8、TXT格式文件
• 提供详细的验证结果和统计信息

【操作步骤】
1. 点击"浏览"按钮选择要验证的直播源文件
2. 根据需要调整验证设置：
   - 超时时间：设置URL响应超时时间（秒）
   - 并发数：同时验证的URL数量（推荐5-10）
   - VLC检测：使用VLC检测流媒体格式
   - 快速检测：启用预过滤和批量处理

3. 点击"开始验证"开始处理
4. 在验证过程中可以：
   - 查看实时进度
   - 点击"停止验证"中断处理
   - 切换结果标签页查看不同内容

5. 验证完成后：
   - 点击"保存结果"保存验证结果
   - 使用"清除结果"清空当前数据

【保存选项】
• 有效频道：保存所有可访问的直播源
• 无效频道：保存无法访问的直播源及原因
• 统计摘要：保存验证统计信息和配置参数
• 分别保存：为每种类型创建独立文件
• 合并保存：将所有选择的内容保存到单个文件

【高级功能】
• 快速检测：使用预过滤技术快速排除明显无效的URL
• DNS预检查：在HTTP请求前验证域名有效性
• 批量处理：并发验证提高处理效率
• 日志记录：记录详细的验证过程和错误信息

【注意事项】
• 大量URL验证可能需要较长时间，请耐心等待
• 网络状况会影响验证结果
• 建议在网络状况良好时进行验证
• 保存的文件包含时间戳，避免覆盖重要数据

【故障排除】
• 如果验证卡住，请点击"停止验证"
• 如遇网络错误，请检查网络连接
• 如需技术支持，请查看运行日志标签页
"""
        
        # 创建帮助对话框
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        help_window.transient(self.root)
        help_window.grab_set()
        
        # 居中显示
        help_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # 创建文本显示区域
        text_frame = ttk.Frame(help_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用ScrolledText显示帮助内容
        help_text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            state="disabled"
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 插入帮助内容
        help_text_widget.config(state="normal")
        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state="disabled")
        
        # 按钮区域
        button_frame = ttk.Frame(text_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="关闭", command=help_window.destroy).pack(side=tk.RIGHT)
        
    def run(self):
        """运行应用程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_validating:
            if messagebox.askokcancel("退出", "验证正在进行中，确定要退出吗？"):
                self.cancel_validation = True
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    try:
        app = IntegratedValidatorApp()
        app.run()
    except Exception as e:
        print(f"启动失败: {e}")
        messagebox.showerror("错误", f"应用程序启动失败: {e}")

if __name__ == "__main__":
    main()