#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具
功能：验证M3U和TXT格式直播源文件中的URL有效性，检测视频分辨率，并生成新的直播源文件
"""

import os
import re
import json
import time
import subprocess
import concurrent.futures
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tempfile
import multiprocessing
from urllib.parse import urlparse


def _ffprobe_get_resolution(url, timeout):
    """在进程池中执行的ffprobe分辨率检测函数"""
    import subprocess
    import json
    try:
        # 使用ffprobe获取视频信息
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'json', url
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False, encoding='utf-8', errors='ignore'
        )

        if result.returncode != 0:
            return None

        output = json.loads(result.stdout)
        if 'streams' in output and len(output['streams']) > 0:
            stream = output['streams'][0]
            if 'width' in stream and 'height' in stream:
                return f"{stream['width']}*{stream['height']}"
        return None
    except Exception:
        return None


class IPTVValidator:
    def __init__(self, input_file, output_file=None, max_workers=None, timeout=5, debug=False, original_filename=None, skip_resolution=False):
        self.input_file = input_file
        # 保存原始文件名（如果提供）
        self.original_filename = original_filename
        # 动态计算线程池大小，更适合GitHub Actions环境（通常2-4核心）
        cpu_count = multiprocessing.cpu_count()
        self.max_workers = max_workers or min(10, cpu_count * 2)
        self.debug = debug
        self.channels = []
        self.categories = []
        # 动态批次大小，根据总频道数和线程数自动调整，避免资源占用过高
        # 初始设置为max_workers的3倍，但不超过100，不少于20
        self.batch_size = min(max(self.max_workers * 3, 20), 100)
        
        # 添加停止标志
        self.stop_requested = False
        
        # 跟踪已处理的外部URL，防止重复添加频道
        self.processed_external_urls = set()
        
        # 初始化所有结果列表，避免AttributeError
        self.all_results = []
        
        # 分级超时策略，减少等待时间以加快整体检测速度
        self.timeouts = {
            'http_head': min(timeout, 3),  # HEAD请求超时更短
            'http_get': timeout,           # GET请求使用默认超时
            'non_http': min(timeout * 1.5, 5),  # 非HTTP协议超时减少到最多5秒
            'ffprobe': min(timeout * 1.5, 5)     # ffprobe超时减少到最多5秒
        }
        
        # 跳过分辨率检测标志
        self.skip_resolution = skip_resolution
        
        # 初始化HTTP会话和连接池
        self.session = self._init_http_session()
        
        # 确保输出目录存在
        self._check_output_dir()
        
        # 检测文件类型和ffprobe可用性
        self.file_type = self._detect_file_type()
        self.ffprobe_available = self._check_ffprobe_availability()
        
        # 生成输出文件名（在检测文件类型后，确保基于最终的input_file路径）
        self.output_file = output_file or self._generate_output_filename()
        
        # 初始化ffprobe进程池
        self.ffprobe_pool = None
        if self.ffprobe_available and not self.skip_resolution:
            # 使用与CPU核心数相同的进程池大小
            self.ffprobe_pool = concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
            
    def stop(self):
        """立即停止验证过程，终止所有线程和进程"""
        self.stop_requested = True
        
        # 如果有ffprobe进程池，立即关闭它而不等待
        if self.ffprobe_pool:
            # 取消所有未完成的ffprobe任务
            for process in self.ffprobe_pool._processes.values():
                try:
                    process.terminate()
                except Exception:
                    pass
            self.ffprobe_pool.shutdown(wait=False)
            self.ffprobe_pool = None  # 释放引用
        
        # 如果有HTTP会话，立即关闭它
        if hasattr(self, 'session') and self.session:
            try:
                # 关闭所有连接
                self.session.close()
            except Exception:
                pass
            self.session = None  # 释放引用
            
        # 如果有验证线程池，尝试关闭它
        if hasattr(self, '_validation_pool') and self._validation_pool:
            try:
                self._validation_pool.shutdown(wait=False)
                self._validation_pool = None  # 释放引用
            except Exception:
                pass
        
        # 强制垃圾回收，释放资源
        import gc
        gc.collect()

    def _init_http_session(self):
        """初始化HTTP会话，配置连接池和重试机制"""
        session = requests.Session()
        
        # 配置重试机制
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        
        # 配置HTTP适配器和连接池
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=50,
            pool_maxsize=50
        )
        
        # 为http和https协议挂载适配器
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session

    def _detect_file_type(self):
        """检测输入文件类型，支持本地文件和互联网URL"""
        # 检查是否为HTTP/HTTPS URL
        if self.input_file.startswith(('http://', 'https://')):
            # 下载文件并检测类型
            self.input_file = self._download_url(self.input_file)
            # 重新检测下载后的文件类型
            if self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
                return 'm3u'
            elif self.input_file.endswith('.txt'):
                return 'txt'
            elif self.input_file.endswith('.json'):
                return 'json'
            else:
                raise ValueError("不支持的文件格式，仅支持.m3u、.m3u8、.txt和.json格式")
        # 本地文件检测
        elif self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
            return 'm3u'
        elif self.input_file.endswith('.txt'):
            return 'txt'
        elif self.input_file.endswith('.json'):
            return 'json'
        else:
            raise ValueError("不支持的文件格式，仅支持.m3u、.m3u8、.txt和.json格式")

    def _download_url(self, url):
        """从URL下载直播源文件到临时目录"""
        try:
            if self.debug:
                print(f"[调试] 正在下载URL: {url}")
            
            # 获取文件名和扩展名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or 'temp_live_source'
            
            # 如果文件名没有扩展名，根据响应头或URL内容确定
            if not os.path.splitext(filename)[1]:
                # 发送请求获取文件内容
                response = self.session.get(url, timeout=self.timeouts['http_get'], allow_redirects=True, verify=False)
                response.raise_for_status()
                
                # 根据响应头或内容确定文件类型
                content_type = response.headers.get('Content-Type', '')
                if 'mpegurl' in content_type or 'm3u' in content_type:
                    filename += '.m3u'
                elif 'json' in content_type:
                    filename += '.json'
                elif 'text/plain' in content_type:
                    # 检查内容是否为JSON格式
                    try:
                        json.loads(response.text)
                        filename += '.json'
                    except json.JSONDecodeError:
                        filename += '.txt'
                else:
                    # 尝试根据内容确定
                    content = response.text.lower()
                    if '#extm3u' in content:
                        filename += '.m3u'
                    else:
                        # 尝试解析为JSON
                        try:
                            json.loads(response.text)
                            filename += '.json'
                        except json.JSONDecodeError:
                            filename += '.txt'
            else:
                # 文件名已有扩展名，直接下载
                response = self.session.get(url, timeout=self.timeouts['http_get'], allow_redirects=True, verify=False)
                response.raise_for_status()
            
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, filename)
            
            # 写入文件内容
            with open(temp_file_path, 'wb') as f:
                f.write(response.content)
            
            if self.debug:
                print(f"[调试] 文件已下载到: {temp_file_path}")
            
            return temp_file_path
        except Exception as e:
            if self.debug:
                print(f"[调试] 下载URL失败: {type(e).__name__}: {e}")
            raise ValueError(f"无法下载URL: {url}, 错误: {str(e)}")

    def _check_ffprobe_availability(self):
        """检查ffprobe是否可用"""
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, shell=False)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_output_dir(self):
        """确保输出目录存在"""
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 创建output目录在脚本所在目录下
        os.makedirs(os.path.join(script_dir, 'output'), exist_ok=True)

    def _generate_output_filename(self):
        """生成输出文件名"""
        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 如果提供了原始文件名，使用它；否则使用input_file的文件名
        if self.original_filename:
            base_name, ext = os.path.splitext(self.original_filename)
        else:
            base_name, ext = os.path.splitext(os.path.basename(self.input_file))
            
        return os.path.join(script_dir, 'output', f"{base_name}_valid{ext}")

    def read_m3u_file(self, progress_callback=None):
        """读取M3U格式文件，解析频道信息和分类，支持进度回调"""
        # 清除已处理的外部URL缓存，确保每次解析都是全新开始
        self.processed_external_urls.clear()
        
        channels = []
        categories = []
        current_category = None
        channel_buffer = {}
        processed_count = 0
        total_channels = 0
        update_interval = 10  # 每处理10个频道发送一次进度更新

        # 只读取一次文件
        with open(self.input_file, 'r', encoding='utf-8-sig', errors='replace') as f:
            lines = f.readlines()
        
        # 计算总频道数
        for line in lines:
            if self.stop_requested:
                print("解析文件过程已被停止")
                break
            if line.strip().startswith('#EXTINF:'):
                total_channels += 1
        
        # 解析频道信息
        for line in lines:
            # 检查是否请求停止
            if self.stop_requested:
                print("解析文件过程已被停止")
                break
                
            line = line.strip()
            if not line:
                continue

            # 解析EXTINF行，提取频道信息
            if line.startswith('#EXTINF:'):
                # 提取频道名称，支持两种格式：有逗号和没有逗号
                # 1. 标准格式：#EXTINF:-1 tvg-id="",频道名称
                # 2. 简化格式：#EXTINF:-1 tvg-id="" tvg-name="频道名称"
                name_match = re.search(r'#EXTINF:.*,(.+)', line)
                if name_match:
                    channel_buffer['name'] = name_match.group(1).strip()
                else:
                    # 没有逗号的情况，尝试从tvg-name提取
                    tvg_name_match = re.search(r'tvg-name="([^"]+)"', line)
                    if tvg_name_match:
                        channel_buffer['name'] = tvg_name_match.group(1).strip()
                    else:
                        # 尝试提取最后一个空格后的内容作为频道名称
                        parts = line.split()
                        if len(parts) > 1:
                            channel_buffer['name'] = parts[-1].strip()
                        else:
                            # 如果无法提取有效的频道名称，则跳过此频道
                            channel_buffer.clear()
                            continue
                    # 处理空频道名称的情况，避免"no desc"显示
                    if not channel_buffer['name']:
                        # 如果频道名称为空，则跳过此频道
                        channel_buffer.clear()
                        continue
                
                # 处理空频道名称的情况，避免"no desc"显示
                if not channel_buffer.get('name'):
                    # 如果频道名称为空，则跳过此频道
                    channel_buffer.clear()
                    continue
                    
                # 从频道名称中提取分辨率信息（如果存在）- 适用于所有格式
                resolution_match = re.search(r'\[(\d+\*\d+)\]', channel_buffer['name'])
                channel_buffer['resolution_from_name'] = resolution_match.group(1) if resolution_match else None

                # 提取分类信息
                category_match = re.search(r'group-title="([^"]+)"', line)
                if category_match:
                    channel_buffer['category'] = category_match.group(1)
                    if category_match.group(1) not in categories:
                        categories.append(category_match.group(1))

            # 解析URL行
            elif not line.startswith('#') and channel_buffer.get('name'):
                # 去除URL两端的反引号和空白字符
                url = line.strip().strip('`')
                channel_buffer['url'] = url
                channels.append(channel_buffer.copy())
                processed_count += 1
                
                # 发送进度更新，每处理一定数量的频道发送一次
                if progress_callback and total_channels > 0 and processed_count % update_interval == 0:
                    progress = int((processed_count / total_channels) * 100)
                    progress_callback({
                        'progress': progress,
                        'total_channels': total_channels,
                        'processed': processed_count,
                        'channel': channel_buffer.copy(),
                        'stage': 'parsing'  # 添加阶段信息
                    })
                
                channel_buffer.clear()
        
        # 发送最后一次进度更新，不包含虚拟频道
        if progress_callback and total_channels > 0:
            progress = int((processed_count / total_channels) * 100)
            progress_callback({
                'progress': progress,
                'total_channels': total_channels,
                'processed': processed_count,
                'stage': 'parsing'
            })

        self.channels = channels
        self.categories = categories
        return channels, categories

    def read_txt_file(self, progress_callback=None):
        """读取TXT格式文件，解析频道信息和分类，支持外部URL处理和进度回调"""
        # 清除已处理的外部URL缓存，确保每次解析都是全新开始
        self.processed_external_urls.clear()
        
        channels = []
        categories = []
        current_category = None
        all_lines = []
        processed_count = 0
        actual_channel_count = 0

        # 先读取文件内容，支持多种编码
        try:
            with open(self.input_file, 'rb') as f:
                content = f.read()

            # 检测文件编码 - 尝试多种编码
            encodings = ['utf-8-sig', 'gbk', 'mbcs', 'utf-16', 'latin-1']
            content_str = None
            
            for encoding in encodings:
                try:
                    content_str = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content_str is None:
                # 所有编码都尝试失败，使用latin-1作为最后的保障
                content_str = content.decode('latin-1', errors='replace')

            all_lines = content_str.splitlines()
        except Exception as e:
            if self.debug:
                print(f"[调试] 读取文件时出错: {str(e)}")
            return channels, categories

        # 先计算实际的频道数（包括直接频道和外部URL中的频道）
        # 严格按照要求：只计算英文逗号分隔的name,url格式行
        for line in all_lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过注释行
            if line.startswith('//') or (line.startswith('#') and '#genre#' not in line):
                continue

            # 跳过分类行
            if re.search(r'([^,]+),#genre#', line):
                continue

            # 只处理包含英文逗号的行
            if ',' in line:
                try:
                    # 使用最后一个逗号分割频道名和URL
                    name, url = line.rsplit(',', 1)
                    name = name.strip()
                    url = url.strip().strip('`')
                    
                    # 检查频道名和URL是否都存在
                    if name and url:
                        actual_channel_count += 1
                except ValueError:
                    continue

        # 逐行处理文件内容
        for line in all_lines:
            # 检查是否请求停止
            if self.stop_requested:
                print("解析文件过程已被停止")
                break
                
            line = line.strip()
            if not line:
                continue
                
            # 跳过注释行
            if line.startswith('//') or (line.startswith('#') and '#genre#' not in line):
                continue

            # 检测分类行：支持多种格式，包括#分类名#,genre#和emoji开头的分类名,genre#
            category_match = re.search(r'([^,]+),#genre#', line)
            if category_match:
                current_category = category_match.group(1).strip()
                if current_category not in categories:
                    categories.append(current_category)
                continue

            # 解析频道行：严格按照要求只处理英文逗号分隔的name,url格式
            # 只处理包含英文逗号的行
            if ',' not in line:
                continue
            
            try:
                # 严格按照要求：使用最后一个英文逗号分割频道名和URL
                name, url = line.rsplit(',', 1)
                name = name.strip()
                url = url.strip().strip('`')
                
                # 基本要求：频道名和URL都必须存在
                if not name or not url:
                    continue
                
                # 从频道名称中提取分辨率信息（如果存在）
                resolution_match = re.search(r'\[(\d+\*\d+)\]', name)
                resolution = resolution_match.group(1) if resolution_match else None
                
                # 检查URL是否为外部直播源文件
                if self._is_external_source_file(url):
                    # 处理外部URL，下载并解析，传递进度回调
                    external_channels, external_categories, processed_count = self._handle_external_url(url, current_category, progress_callback, processed_count, actual_channel_count)
                    channels.extend(external_channels)
                    categories.extend([cat for cat in external_categories if cat not in categories])
                    
                    # 无需再增加actual_channel_count，因为在初步计数时已经计算过了
                    # 更新进度计数
                    processed_count += len(external_channels)
                else:
                    # 普通频道，直接添加
                    channel = {
                        'name': name,
                        'url': url,
                        'category': current_category if current_category else '未分类',
                        'resolution_from_name': resolution
                    }
                    channels.append(channel)
                    actual_channel_count += 1
                    
                    # 发送进度更新
                    processed_count += 1
                    if progress_callback:
                        # 使用实际的频道数计算进度
                        if actual_channel_count > 0:
                            progress = int((processed_count / actual_channel_count) * 100)
                        else:
                            progress = 0
                        progress_callback({
                            'progress': progress,
                            'total_channels': actual_channel_count,
                            'processed': processed_count,
                            'channel': channel
                        })
            except ValueError:
                continue

        # 发送最后一次进度更新，不包含虚拟频道
        if progress_callback and actual_channel_count > 0:
            progress_callback({
                'progress': 100,
                'total_channels': actual_channel_count,
                'processed': processed_count,
                'stage': 'parsing'
            })

        if self.debug:
            print(f"[调试] TXT文件解析完成，找到 {actual_channel_count} 个频道，实际处理 {processed_count} 个频道")

        # 确保所有分类都存在
        if not categories:
            categories.append('未分类')
            current_category = '未分类'

        # 如果没有解析到任何频道，尝试更宽松的解析方式，但仍严格要求name,URL格式
        if not channels:
            for line in all_lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                
                # 仍然要求必须包含英文逗号分隔的name,url格式
                if ',' not in line:
                    continue
                    
                # 提取URL
                url = line.split(',')[-1].strip() if ',' in line else line.strip()
                name = line.split(',')[0].strip() if ',' in line else ''
                
                # 基本要求：频道名和URL都必须存在
                if not name or not url:
                    continue
                    
                # 检查URL是否为有效的流媒体URL
                if re.search(r'http[s]?://', url) or re.search(r'rtsp://', url) or re.search(r'rtmp://', url) or re.search(r'mms://', url):
                    # 检查URL是否为外部直播源文件
                    if self._is_external_source_file(url):
                        # 处理外部URL，下载并解析，传递进度回调
                        external_channels, external_categories, _ = self._handle_external_url(url, '未分类', progress_callback)
                        channels.extend(external_channels)
                        categories.extend([cat for cat in external_categories if cat not in categories])
                    else:
                        # 普通频道，直接添加
                        # 从频道名称中提取分辨率信息（如果存在）
                        resolution_match = re.search(r'\[(\d+\*\d+)\]', name)
                        resolution = resolution_match.group(1) if resolution_match else None
                        channels.append({
                            'name': name,
                            'url': url,
                            'category': '未分类',
                            'resolution_from_name': resolution
                        })

        self.channels = channels
        self.categories = categories
        return channels, categories
        
    def _is_external_source_file(self, url):
        """检查URL是否指向外部直播源文件"""
        if not url.startswith(('http://', 'https://')):
            return False
            
        # 检查URL是否以直播源文件扩展名结尾
        url_lower = url.lower()
        
        # 对于.m3u/.m3u8文件，默认不视为外部直播源文件
        # 只有当URL中明确包含直播源列表关键字时才视为外部直播源文件
        if url_lower.endswith(('.m3u', '.m3u8')):
            # 仅当URL路径中包含明确的直播源列表关键字时，才视为外部直播源文件
            playlist_keywords = ['playlist', 'm3u', 'm3u8', 'playlist.m3u8', 'live.txt', 'iptv.txt']
            for keyword in playlist_keywords:
                if keyword in url_lower:
                    # 进一步检查，确保不是单个频道的播放URL
                    # 如果URL中包含stream、live_等关键字，很可能是单个频道的播放URL
                    stream_keywords = ['stream', 'live_', 'live/', 'edge/', 'playlist.m3u8']
                    for stream_keyword in stream_keywords:
                        if stream_keyword in url_lower:
                            return False
                    return True
            # 默认不处理为外部直播源文件
            return False
        
        # 对于txt和json文件，保持现有判断逻辑
        if url_lower.endswith(('.txt', '.json')):
            # 检查URL路径中是否包含直播源相关关键字
            keywords = ['iptv', 'live', 'channel', 'playlist']
            for keyword in keywords:
                if keyword in url_lower:
                    return True
            # 如果没有明确的关键字，不处理为外部直播源
            return False
                
        return False
        
    def read_json_file(self, progress_callback=None):
        """读取JSON格式文件，解析频道信息和分类，支持进度回调"""
        # 清除已处理的外部URL缓存，确保每次解析都是全新开始
        self.processed_external_urls.clear()
        
        channels = []
        categories = []
        processed_count = 0
        
        try:
            if self.debug:
                print(f"[调试] 正在解析JSON文件: {self.input_file}")
            
            # 读取JSON文件
            with open(self.input_file, 'r', encoding='utf-8-sig', errors='replace') as f:
                data = json.load(f)
            
            # 递归提取频道信息的辅助函数
            def extract_channels(obj, category=None):
                if isinstance(obj, dict):
                    # 检查是否为频道对象
                    if 'name' in obj and 'url' in obj:
                        name = obj['name']
                        # 从频道名称中提取分辨率信息（如果存在）
                        resolution_match = re.search(r'\[(\d+\*\d+)\]', name)
                        resolution = resolution_match.group(1) if resolution_match else None
                        return [{
                            'name': name,
                            'url': obj['url'],
                            'category': obj.get('category') or category or '未分类',
                            'resolution_from_name': resolution
                        }]
                    elif 'channel' in obj and 'url' in obj:
                        name = obj['channel']
                        # 从频道名称中提取分辨率信息（如果存在）
                        resolution_match = re.search(r'\[(\d+\*\d+)\]', name)
                        resolution = resolution_match.group(1) if resolution_match else None
                        return [{
                            'name': name,
                            'url': obj['url'],
                            'category': obj.get('category') or category or '未分类',
                            'resolution_from_name': resolution
                        }]
                    
                    # 递归处理字典
                    result = []
                    for key, value in obj.items():
                        # 如果值是列表或字典，递归处理
                        if isinstance(value, (list, dict)):
                            # 尝试将键作为分类名
                            result.extend(extract_channels(value, key))
                        # 检查是否有channels、list或data字段
                        elif key in ['channels', 'list', 'data']:
                            result.extend(extract_channels(value))
                    return result
                elif isinstance(obj, list):
                    # 递归处理列表
                    result = []
                    for item in obj:
                        result.extend(extract_channels(item, category))
                    return result
                return []
            
            # 提取所有频道
            all_channels = extract_channels(data)
            total_channels = len(all_channels)
            
            if self.debug:
                print(f"[调试] 从JSON文件中提取到 {total_channels} 个频道")
            
            # 处理提取到的频道
            for channel in all_channels:
                # 检查是否请求停止
                if self.stop_requested:
                    print("解析文件过程已被停止")
                    break
                    
                # 检查频道信息完整性
                if channel.get('name') and channel.get('url'):
                    channels.append(channel)
                    
                    # 更新分类列表
                    category = channel.get('category', '未分类')
                    if category not in categories:
                        categories.append(category)
                    
                    processed_count += 1
                    
                    # 发送进度更新
                    if progress_callback:
                        progress = int((processed_count / max(total_channels, 1)) * 100)
                        progress_callback({
                            'progress': progress,
                            'total_channels': max(total_channels, 1),
                            'processed': processed_count,
                            'channel': channel,
                            'stage': 'parsing'
                        })
        
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[调试] JSON解析错误: {str(e)}")
        except Exception as e:
            if self.debug:
                print(f"[调试] 读取JSON文件时出错: {str(e)}")
        
        # 确保所有分类都存在
        if not categories:
            categories.append('未分类')
        
        self.channels = channels
        self.categories = categories
        return channels, categories

    def _handle_external_url(self, url, default_category, progress_callback=None, processed_count=0, total_channels=0):
        """处理外部URL，下载并解析直播源文件，支持进度回调"""
        external_channels = []
        external_categories = []
        
        # 检查是否已经处理过这个URL，避免重复添加
        if url in self.processed_external_urls:
            if self.debug:
                print(f"[调试] 外部URL已处理过，跳过: {url}")
            return external_channels, external_categories, processed_count
        
        # 标记URL为已处理
        self.processed_external_urls.add(url)
        
        try:
            if self.debug:
                print(f"[调试] 处理外部URL: {url}")
            
            # 检查是否请求停止
            if self.stop_requested:
                return external_channels, external_categories, processed_count
            
            # 下载外部文件 - 使用会话对象的get方法，并设置超时
            with self.session.get(url, timeout=self.timeouts['http_get'], allow_redirects=True, verify=False) as response:
                response.raise_for_status()
                
                # 检查是否请求停止
                if self.stop_requested:
                    return external_channels, external_categories, processed_count
                
                # 获取文件名和扩展名
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or 'temp_live_source'
                
                # 如果文件名没有扩展名，根据响应头或内容确定
                if not os.path.splitext(filename)[1]:
                    # 根据响应头或内容确定文件类型
                    content_type = response.headers.get('Content-Type', '')
                    if 'mpegurl' in content_type or 'm3u' in content_type:
                        filename += '.m3u'
                    elif 'json' in content_type:
                        filename += '.json'
                    else:
                        # 尝试解析为JSON
                        try:
                            json.loads(response.text)
                            filename += '.json'
                        except json.JSONDecodeError:
                            # 检查是否为M3U格式
                            if '#extm3u' in response.text.lower():
                                filename += '.m3u'
                            else:
                                filename += '.txt'
                
                # 创建临时文件
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, filename)
                
                # 写入文件内容
                with open(temp_file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        # 检查是否请求停止
                        if self.stop_requested:
                            os.remove(temp_file_path)
                            return external_channels, external_categories, processed_count
                        if chunk:
                            f.write(chunk)
            
            # 检查是否请求停止
            if self.stop_requested:
                os.remove(temp_file_path)
                return external_channels, external_categories, processed_count
            
            # 检测文件类型
            file_ext = os.path.splitext(temp_file_path)[1].lower()
            
            if file_ext in ['.m3u', '.m3u8']:
                # 使用read_m3u_file方法解析
                temp_validator = IPTVValidator(temp_file_path, debug=self.debug)
                temp_validator.file_type = 'm3u'
                # 将已处理URL集合传递给临时验证器，避免重复处理
                temp_validator.processed_external_urls = self.processed_external_urls.copy()
                temp_validator.stop_requested = self.stop_requested  # 传递停止标志
                external_channels, external_categories = temp_validator.read_m3u_file(progress_callback)
            elif file_ext == '.txt':
                # 使用read_txt_file方法解析（递归）
                temp_validator = IPTVValidator(temp_file_path, debug=self.debug)
                temp_validator.file_type = 'txt'
                # 将已处理URL集合传递给临时验证器，避免重复处理
                temp_validator.processed_external_urls = self.processed_external_urls.copy()
                temp_validator.stop_requested = self.stop_requested  # 传递停止标志
                external_channels, external_categories = temp_validator.read_txt_file(progress_callback)
            elif file_ext == '.json':
                # 使用read_json_file方法解析
                temp_validator = IPTVValidator(temp_file_path, debug=self.debug)
                temp_validator.file_type = 'json'
                # 将已处理URL集合传递给临时验证器，避免重复处理
                temp_validator.processed_external_urls = self.processed_external_urls.copy()
                temp_validator.stop_requested = self.stop_requested  # 传递停止标志
                external_channels, external_categories = temp_validator.read_json_file(progress_callback)
            
            # 检查是否请求停止
            if self.stop_requested:
                os.remove(temp_file_path)
                return external_channels, external_categories, processed_count
            
            # 清理临时文件
            os.remove(temp_file_path)
            
            # 如果外部文件没有分类信息，使用默认分类
            for channel in external_channels:
                if not channel.get('category'):
                    channel['category'] = default_category
                # 发送进度更新
                if progress_callback:
                    processed_count += 1
                    # 计算进度百分比，使用传入的total_channels（即actual_channel_count）
                    if total_channels > 0:
                        progress = int((processed_count / total_channels) * 100)
                    else:
                        progress = 0
                    progress_callback({
                        'progress': progress,
                        'total_channels': total_channels,
                        'processed': processed_count,
                        'channel': channel,
                        'stage': 'parsing'
                    })
            
            if self.debug:
                print(f"[调试] 从外部URL解析到 {len(external_channels)} 个频道")
                
        except Exception as e:
            if self.debug:
                print(f"[调试] 处理外部URL出错: {str(e)}")
            # 外部URL处理失败，忽略该URL
        
        return external_channels, external_categories, processed_count

    def check_url_validity(self, url):
        """检查URL的有效性"""
        try:
            # 处理包含特殊字符的URL，如$符号（通常是电视端的标识）
            if '$' in url:
                # 移除$符号及其后面的内容，只保留前面的URL部分
                url = url.split('$')[0]
                if self.debug:
                    print(f"[调试] 处理包含$符号的URL: {url}")

            # 检测是否包含动态参数（如{PSID}、{TARGETOPT}等，包括URL编码形式%7BPSID%7D）
            has_dynamic_params = re.search(r'(\{[A-Z_]+\}|%7B[A-Z_]+%7D)', url)
            if has_dynamic_params and self.debug:
                print(f"[调试] 检测到包含动态参数的URL: {url}")

            # 根据用户要求，文件中的线路都是电视上能打开播放的频道线路
            # 所以我们对URL验证更加宽松，只要URL不为空就视为有效
            if url.strip():
                if self.debug:
                    print(f"[调试] URL不为空，视为有效: {url}")
                return True
            
            # 只有空URL才视为无效
            if self.debug:
                print(f"[调试] URL为空，视为无效: {url}")
            return False
        except Exception as e:
            if self.debug:
                print(f"[调试] 检查URL有效性时出错: {type(e).__name__}: {e}")
            # 如果发生任何异常，只要URL不为空就视为有效
            if url.strip():
                if self.debug:
                    print(f"[调试] 异常处理中URL不为空，视为有效: {url}")
                return True
            return False


    
    def get_resolution(self, url):
        """获取视频分辨率，使用进程池提高性能，支持停止请求"""
        try:
            # 如果跳过分辨率检测，直接返回None
            if self.skip_resolution:
                return None
                
            # 检查是否请求停止
            if self.stop_requested:
                return None

            # 检查ffprobe是否可用
            if not self.ffprobe_available:
                return None

            # 支持更多协议和格式的分辨率检测
            supported_protocols = [
                '.m3u8', 'm3u8', 'rtsp://', 'rtmp://', 
                'udp://', 'rtp://', 'http://', 'https://'
            ]
            
            # 检查URL是否包含任何支持的协议或格式
            if not any(protocol in url for protocol in supported_protocols):
                return None

            # 使用进程池执行ffprobe命令，并设置超时
            future = self.ffprobe_pool.submit(_ffprobe_get_resolution, url, self.timeouts['ffprobe'])
            try:
                # 检查是否请求停止
                if self.stop_requested:
                    future.cancel()
                    return None
                # 使用较短的超时时间获取结果，以便及时响应停止请求
                resolution = future.result(timeout=self.timeouts['ffprobe'])
                return resolution
            except concurrent.futures.TimeoutError:
                future.cancel()
                return None

        except Exception:
            return None

    def process_channel(self, channel, original_index):
        """处理单个频道：验证URL并检测分辨率，包含原始索引信息"""
        # 检查是否请求停止
        if self.stop_requested:
            return {
                'name': channel['name'],
                'url': channel['url'],
                'category': channel.get('category', '未分类'),
                'original_index': original_index,
                'valid': False,
                'resolution': None,
                'status': 'stopped'
            }
            
        result = {
            'name': channel['name'],
            'url': channel['url'],
            'category': channel.get('category', '未分类'),
            'original_index': original_index,
            'valid': None,  # 初始值为None，表示尚未验证
            'resolution': None,
            'status': 'checking'  # 初始状态为正在检查
        }
        
        try:
            # 再次检查是否请求停止
            if self.stop_requested:
                result['status'] = 'stopped'
                return result
            
            valid = self.check_url_validity(channel['url'])
            if not valid:
                return result

            result['valid'] = True
            result['status'] = 'valid'  # 设置为有效状态
            
            try:
                # 检测分辨率
                resolution = self.get_resolution(channel['url'])
                
                # 如果ffprobe检测失败，尝试使用从频道名称中提取的分辨率
                if not resolution and channel.get('resolution_from_name'):
                    resolution = channel['resolution_from_name']
                    
                result['resolution'] = resolution
                
                if resolution:
                    # 检查频道名称是否已经包含分辨率信息
                    if f"[{resolution}]" not in channel['name']:
                        result['name_with_resolution'] = f"{channel['name']}[{resolution}]"
                    else:
                        result['name_with_resolution'] = channel['name']
                else:
                    result['name_with_resolution'] = channel['name']
            except concurrent.futures.TimeoutError:
                # 捕获分辨率检测超时异常
                result['status'] = 'timeout'  # 设置为超时状态
                # 超时情况下也尝试使用从名称中提取的分辨率
                if channel.get('resolution_from_name'):
                    result['resolution'] = channel['resolution_from_name']
                    result['name_with_resolution'] = channel['name']
                else:
                    result['name_with_resolution'] = channel['name']
            except Exception as e:
                if self.debug:
                    print(f"[调试] 检测频道 {channel['name']} 分辨率时出错: {type(e).__name__}: {e}")
                # 分辨率检测失败不影响URL有效性判断
                # 异常情况下也尝试使用从名称中提取的分辨率
                if channel.get('resolution_from_name'):
                    result['resolution'] = channel['resolution_from_name']
                    result['name_with_resolution'] = channel['name']
                else:
                    result['name_with_resolution'] = channel['name']

        except concurrent.futures.TimeoutError:
            # 捕获URL验证超时异常
            result['status'] = 'timeout'  # 设置为超时状态
            # 超时情况下也尝试使用从名称中提取的分辨率
            if channel.get('resolution_from_name'):
                result['resolution'] = channel['resolution_from_name']
            result['name_with_resolution'] = channel['name']
        except Exception as e:
            if self.debug:
                print(f"[调试] 处理频道 {channel['name']} 时出错: {type(e).__name__}: {e}")
            # 其他异常保持频道为无效
            # 异常情况下也尝试使用从名称中提取的分辨率
            if channel.get('resolution_from_name'):
                result['resolution'] = channel['resolution_from_name']
            result['name_with_resolution'] = channel['name']

        return result

    def validate_channels(self, progress_callback=None):
        """批量验证所有频道，分批次处理以避免占用过多资源"""
        all_results = []
        valid_channels = []
        resolution_valid_channels = []  # 存储检测到分辨率的有效频道
        total_channels = len(self.channels)
        processed_count = 0
        
        # 清除已处理的外部URL缓存，确保每次验证都是全新开始
        self.processed_external_urls.clear()
        
        # 只创建一个线程池用于整个验证过程，避免频繁创建和关闭的开销
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 分批次处理频道，保持原始顺序
            for i in range(0, total_channels, self.batch_size):
                # 检查是否请求停止
                if self.stop_requested:
                    print("验证过程已被停止")
                    executor.shutdown(wait=False)
                    break
                    
                batch_start = i
                batch_end = min(i + self.batch_size, total_channels)
                
                # 发送批次处理开始的进度更新
                if progress_callback:
                    progress = int((processed_count / total_channels) * 100)
                    progress_callback({
                        'progress': progress,
                        'total_channels': total_channels,
                        'processed': processed_count,
                        'message': f'开始处理批次 {batch_start + 1}-{batch_end} / {total_channels}',
                        'stage': 'batch_processing'
                    })
                
                batch_channels = self.channels[batch_start:batch_end]
                
                # 使用map方法保持原始顺序处理当前批次的所有任务
                for idx, result in enumerate(executor.map(self.process_channel, batch_channels, range(batch_start, batch_end))):
                    # 检查是否请求停止
                    if self.stop_requested:
                        executor.shutdown(wait=False)
                        print("验证过程已被停止")
                        break
                        
                    # 原始索引已经在process_channel中添加
                    
                    all_results.append(result)
                    processed_count += 1
                    
                    # 发送实时进度
                    if progress_callback:
                        progress = int((processed_count / total_channels) * 100)
                        progress_callback({
                            'progress': progress,
                            'total_channels': total_channels,
                            'processed': processed_count,
                            'channel': result,
                            'stage': 'validation'
                        })
                    
                    if result['valid']:
                        valid_channels.append(result)
                        # 检查是否有分辨率信息
                        if result.get('resolution'):
                            resolution_valid_channels.append(result)

        # 发送完成通知
        if progress_callback:
            progress_callback({
                'progress': 100 if processed_count == total_channels else processed_count,
                'total_channels': total_channels,
                'processed': processed_count,
                'valid_count': len(valid_channels),
                'resolution_valid_count': len(resolution_valid_channels),  # 分辨率有效频道数量
                'invalid_count': processed_count - len(valid_channels),
                'status': 'completed' if not self.stop_requested else 'stopped'
            })
        
        self.all_results = all_results
        return valid_channels

    def generate_m3u_output(self, valid_channels):
        """生成M3U格式的输出文件"""
        # 按分类分组频道
        channels_by_category = {category: [] for category in self.categories}
        # 确保所有分类都存在，包括无分类的频道
        if '未分类' not in channels_by_category:
            channels_by_category['未分类'] = []
            self.categories.append('未分类')
        
        for channel in valid_channels:
            category = channel.get('category', '未分类')
            if category in channels_by_category:
                channels_by_category[category].append(channel)

        # 生成M3U内容
        content = ['#EXTM3U']
        for category in self.categories:
            for channel in channels_by_category[category]:
                content.append(f"#EXTINF:-1 group-title=\"{channel['category']}\",{channel['name_with_resolution']}")
                content.append(channel['url'])

        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        return self.output_file

    def generate_txt_output(self, valid_channels):
        """生成TXT格式的输出文件"""
        # 按分类分组频道
        channels_by_category = {}
        
        # 首先将所有有效分类添加到字典中
        for category in self.categories:
            if category not in channels_by_category:
                channels_by_category[category] = []
        
        # 遍历所有有效频道，添加到对应的分类中
        for channel in valid_channels:
            category = channel['category']
            if category not in channels_by_category:
                channels_by_category[category] = []
                # 如果这是一个新的分类，将其添加到分类列表中
                if category not in self.categories:
                    self.categories.append(category)
            channels_by_category[category].append(channel)

        # 生成TXT内容
        content = []
        for category in self.categories:
            if category in channels_by_category and channels_by_category[category]:
                content.append(f"#{category}#,genre#")
                for channel in channels_by_category[category]:
                    content.append(f"{channel['name_with_resolution']},{channel['url']}")

        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))
        
        return self.output_file
        
    def generate_json_output(self, valid_channels):
        """生成JSON格式的输出文件"""
        # 按分类分组频道
        channels_by_category = {}
        
        # 遍历所有有效频道，添加到对应的分类中
        for channel in valid_channels:
            category = channel['category']
            if category not in channels_by_category:
                channels_by_category[category] = []
            channels_by_category[category].append({
                'name': channel['name_with_resolution'],
                'url': channel['url'],
                'category': category
            })

        # 创建JSON结构
        json_data = {
            'total_channels': len(valid_channels),
            'categories': list(channels_by_category.keys()),
            'channels': []
        }
        
        # 添加所有频道
        for channel in valid_channels:
            json_data['channels'].append({
                'name': channel['name_with_resolution'],
                'url': channel['url'],
                'category': channel['category']
            })

        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return self.output_file
        
    def get_all_results(self):
        """获取所有频道的验证结果，包括有效和无效的"""
        return getattr(self, 'all_results', [])
        
    def generate_output_files(self):
        """生成输出文件，根据文件类型选择合适的方法"""
        # 获取有效频道，使用getattr确保即使all_results未设置也不会出错
        valid_channels = [channel for channel in getattr(self, 'all_results', []) if channel['valid']]
        
        # 根据文件类型生成输出文件
        if self.file_type == 'm3u':
            output_file = self.generate_m3u_output(valid_channels)
        elif self.file_type == 'json':
            output_file = self.generate_json_output(valid_channels)
        else:
            output_file = self.generate_txt_output(valid_channels)
        
        # 生成分辨率有效频道的输出文件
        resolution_valid_channels = [channel for channel in valid_channels if channel.get('resolution')]
        if resolution_valid_channels:
            # 创建带分辨率标记的输出文件名
            base_name, ext = os.path.splitext(output_file)
            resolution_output_file = f"{base_name}_resolution{ext}"
            
            # 保存原始输出文件名，临时替换为分辨率输出文件名
            original_output_file = self.output_file
            self.output_file = resolution_output_file
            
            # 生成分辨率有效频道文件
            if self.file_type == 'm3u':
                self.generate_m3u_output(resolution_valid_channels)
            elif self.file_type == 'json':
                self.generate_json_output(resolution_valid_channels)
            else:
                self.generate_txt_output(resolution_valid_channels)
            
            # 恢复原始输出文件名
            self.output_file = original_output_file
            
            print(f"分辨率有效频道输出文件已生成: {resolution_output_file}")
        
        return output_file

    def run(self):
        """运行验证流程"""
        print(f"开始验证文件: {self.input_file}")
        print(f"文件类型: {self.file_type}")
        
        # 检查ffprobe是否可用
        if not self.ffprobe_available:
            print("警告: 未检测到ffprobe，将跳过视频分辨率检测")
            print("请安装FFmpeg并添加到系统PATH以启用分辨率检测功能")

        # 读取文件
        if self.file_type == 'm3u':
            self.read_m3u_file()
        elif self.file_type == 'json':
            self.read_json_file()
        else:
            self.read_txt_file()

        print(f"共解析到 {len(self.channels)} 个频道，{len(self.categories)} 个分类")
        
        # 如果没有解析到频道
        if not self.channels:
            print("错误: 没有从文件中解析到任何频道")
            print("提示: 请检查文件格式是否正确，确保是标准的M3U或TXT格式")
            return None

        # 验证频道
        start_time = time.time()
        valid_channels = self.validate_channels()
        end_time = time.time()

        print(f"验证完成，耗时 {end_time - start_time:.2f} 秒")
        print(f"有效频道数: {len(valid_channels)}")
        # 计算分辨率有效频道数，使用getattr确保即使all_results未设置也不会出错
        resolution_valid_channels = [channel for channel in getattr(self, 'all_results', []) if channel['valid'] and channel.get('resolution')]
        print(f"分辨率有效频道数: {len(resolution_valid_channels)}")
        if len(self.channels) > 0:
            print(f"有效率: {len(valid_channels) / len(self.channels) * 100:.2f}%")
        else:
            print("有效率: 0.00%")

        # 生成输出文件
        if valid_channels:
            output_file = self.generate_output_files()
            print(f"输出文件已生成: {output_file}")
            return output_file
        else:
            print("\n没有找到有效的直播源")
            print("\n🔍 可能的原因:")
            print("1. 网络环境限制：可能是防火墙、代理或网络策略阻止了对直播源的访问")
            print("2. DNS解析失败：无法解析直播源服务器的域名")
            print("3. URL已失效：直播源服务器可能已经关闭或更改了地址")
            print("4. 网络连接不稳定：网络延迟或丢包导致连接超时")
            print("5. URL格式错误：请确保所有URL都包含正确的协议（http/https/rtsp/rtmp/mms）")
            
            print("\n💡 建议的解决方案:")
            print("1. 检查网络连接：确保您的计算机可以正常访问互联网")
            print("2. 验证URL有效性：手动测试几个URL是否可以访问")
            print("3. 更换直播源：尝试使用其他可靠的直播源提供商")
            print("4. 调整超时时间：使用 -t 参数增加超时时间，例如：-t 10")
            print("5. 检查URL格式：确保所有URL都符合标准格式")
            
            print("\n📝 示例：如何使用有效的直播源")
            print("您可以尝试使用以下格式的M3U文件：")
            print("#EXTM3U")
            print("#EXTINF:-1 group-title=\"测试\",测试频道")
            print("http://example.com/valid_stream.m3u8")
            
        # 关闭ffprobe进程池
        if hasattr(self, 'ffprobe_pool') and self.ffprobe_pool:
            self.ffprobe_pool.shutdown()
            
        return None


def validate_file(input_file, output_file=None, max_workers=20, timeout=5, debug=False, skip_resolution=False):
    """便捷函数：验证单个文件"""
    # 确保输出目录存在，即使在创建validator实例之前
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(script_dir, 'output'), exist_ok=True)
    
    validator = IPTVValidator(input_file, output_file, max_workers, timeout, debug, skip_resolution=skip_resolution)
    output_file = validator.run()
    return output_file, validator.all_results


def validate_all_files(directory='.', max_workers=20, timeout=5, debug=False, skip_resolution=False):
    """便捷函数：验证目录下所有支持的文件"""
    # 确保输出目录存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(script_dir, 'output'), exist_ok=True)
    
    supported_extensions = ('.m3u', '.m3u8', '.txt')
    files_to_validate = []

    for filename in os.listdir(directory):
        if filename.endswith(supported_extensions) and not filename.endswith('_valid.m3u') and not filename.endswith('_valid.txt'):
            files_to_validate.append(os.path.join(directory, filename))

    print(f"找到 {len(files_to_validate)} 个文件需要验证")

    for file_path in files_to_validate:
        print(f"\n{'='*50}")
        output_file, _ = validate_file(file_path, max_workers=max_workers, timeout=timeout, debug=debug, skip_resolution=skip_resolution)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='直播源有效性验证工具')
    # 创建互斥组
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--input', help='输入文件路径')
    group.add_argument('-a', '--all', action='store_true', help='验证当前目录下所有支持的文件')
    
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-w', '--workers', type=int, default=20, help='并发工作线程数')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='超时时间(秒)')
    parser.add_argument('-d', '--debug', action='store_true', help='启用调试模式，显示详细的验证信息')
    parser.add_argument('--no-resolution', action='store_true', help='跳过视频分辨率检测，加快验证速度')

    args = parser.parse_args()

    if args.all:
        validate_all_files('.', args.workers, args.timeout, args.debug, args.no_resolution)
    else:
        output_file, _ = validate_file(args.input, args.output, args.workers, args.timeout, args.debug, args.no_resolution)
