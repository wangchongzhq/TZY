#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具
功能：验证M3U和TXT格式直播源文件中的URL有效性，检测视频分辨率，并生成新的直播源文件
参考BlackBird-Player的验证思路进行优化
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
from datetime import datetime

# 验证时间戳跟踪器 - 参考BlackBird-Player的result.txt格式
class ValidationTimestamp:
    """验证时间戳跟踪器 - 参考BlackBird-Player的更新时间记录方式"""
    
    _instance = None
    _timestamp = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls._instance
    
    @classmethod
    def get_timestamp(cls):
        """获取当前验证时间戳"""
        return cls._timestamp
    
    @classmethod
    def update_timestamp(cls):
        """更新验证时间戳"""
        cls._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls._timestamp
    
    @classmethod
    def reset(cls):
        """重置时间戳"""
        cls._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_resolution_from_hls(url, timeout, headers=None):
    """从HLS播放列表中提取分辨率信息 - 优化版本"""
    import re
    import requests
    try:
        session = requests.Session()
        response = session.get(url, timeout=min(timeout, 3), headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return None

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
    except Exception:
        return None


def _extract_first_segment_from_m3u8(m3u8_url, timeout, headers=None):
    """从m3u8播放列表中提取第一个媒体片段URL - 优化版本"""
    import re
    import requests
    from urllib.parse import urljoin, urlparse
    try:
        session = requests.Session()
        response = session.get(m3u8_url, timeout=min(timeout, 3), headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return None

        content = response.text
        lines = content.splitlines()
        
        base_url = m3u8_url
        parsed_url = urlparse(m3u8_url)
        if parsed_url.path.rstrip('/'):
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('http://') or line.startswith('https://'):
                return line
            elif line.startswith('/'):
                return urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", line)
            else:
                return urljoin(base_url, line)

        return None
    except Exception:
        return None


def _get_resolution_from_segment(segment_url, timeout, headers=None):
    """使用ffprobe获取媒体片段的分辨率 - 优化版本"""
    import subprocess
    import json
    try:
        if not segment_url:
            return None

        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'json',
            '-timeout', str(int(timeout * 1000000))
        ]

        if headers:
            cmd.extend([
                '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0")}\r\n'
            ])

        cmd.append(segment_url)

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if 'streams' in data and len(data['streams']) > 0:
                    width = data['streams'][0].get('width', 0)
                    height = data['streams'][0].get('height', 0)
                    if width and height and width > 0 and height > 0:
                        codec = data['streams'][0].get('codec_name', '未知')
                        return f"{width}*{height}", codec, {'source': 'segment'}
            except json.JSONDecodeError:
                pass

        return None, None, {}
    except Exception:
        return None


def _ffprobe_get_resolution(url, timeout, headers=None, retry=1):
    """在进程池中执行的ffprobe分辨率检测函数 - 优化版本（参考新对话.txt）"""
    import subprocess
    import json

    url_lower = url.lower()
    is_rtsp = url_lower.startswith('rtsp://')
    is_hls = url_lower.endswith(('.m3u8', '.m3u')) or '/hls/' in url_lower or '/live/' in url_lower
    is_udp = url_lower.startswith('udp://') or url_lower.startswith('rtp://')

    timeout_us = int(timeout * 1000000)
    skip_bytes = 500000

    for attempt in range(retry + 1):
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-timeout', str(timeout_us),
                '-skip_initial_bytes', str(skip_bytes),
                '-flags', 'low_delay',
                '-fflags', '+genpts',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,codec_name:format=probe_score,duration',
                '-of', 'json'
            ]

            if is_rtsp:
                cmd.extend(['-rtsp_transport', 'tcp'])
            if is_hls:
                cmd.extend(['-allowed_extensions', 'ALL'])
            if is_udp:
                cmd.extend(['-f', 'mpegts'])

            if headers:
                cmd.extend([
                    '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0")}\r\n'
                ])

            cmd.append(url)

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                shell=False, encoding='utf-8', errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    format_info = data.get('format', {})
                    probe_score = format_info.get('probe_score', 0)
                    format_duration = format_info.get('duration', 'unknown')

                    if probe_score <= 0:
                        if attempt < retry:
                            continue
                        return None, None, {'error': 'format_unrecognizable', 'probe_score': probe_score}

                    if 'streams' in data and len(data['streams']) > 0:
                        stream = data['streams'][0]
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        if width and height and width > 0 and height > 0:
                            codec = stream.get('codec_name', '未知')
                            return f"{width}*{height}", codec, {
                                'probe_score': probe_score,
                                'duration': format_duration,
                                'codec': codec
                            }
                except json.JSONDecodeError:
                    pass

            if attempt < retry:
                continue

            return None, None, {'error': 'probe_failed', 'returncode': result.returncode}

        except subprocess.TimeoutExpired:
            if attempt < retry:
                continue
            return None, None, {'error': 'timeout'}

        except Exception as e:
            if attempt < retry:
                continue
            return None, None, {'error': str(e)}

    return None, None, {'error': 'max_retries_exceeded'}


def _test_stream_playback(url, timeout, headers=None):
    """BlackBird-Player风格的试播验证函数 - 通过实际播放测试判断URL是否真正有效
    并获取真实分辨率，而不是从URL模式推断
    
    试播策略：
    1. UDP/RTSP/RTMP/RTP: 使用FFmpeg尝试解码一小段数据，确认流可播放
    2. IPv6: 使用FFprobe探测，检查是否能在IPv6环境下正常连接
    3. 成功播放后获取真实分辨率和编码信息
    """
    import subprocess
    import json
    import socket
    import threading
    import time
    
    url_lower = url.lower()
    is_ipv6 = '[' in url and ']' in url
    is_udp = url_lower.startswith('udp://') or url_lower.startswith('rtp://')
    is_rtsp = url_lower.startswith('rtsp://')
    is_rtmp = url_lower.startswith('rtmp://')
    
    timeout_us = int(timeout * 1000000)
    
    def _check_socket_connection(host, port, timeout_sec=2):
        """检查socket连接是否可达"""
        try:
            sock = socket.socket(socket.AF_INET6 if ':' in host else socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_sec)
            sock.connect((host, int(port)))
            sock.close()
            return True
        except Exception:
            return False
    
    def _try_udp_multicast(url, timeout_sec):
        """尝试UDP组播连接检查"""
        try:
            if not url.startswith('udp://'):
                return False
            parts = url[7:].split('@')
            if len(parts) < 2:
                return False
            addr_port = parts[1].split('/')[0]
            addr, port = addr_port.rsplit(':', 1)
            return _check_socket_connection(addr, int(port), timeout_sec)
        except Exception:
            return False
    
    try:
        if is_udp:
            if not _try_udp_multicast(url, min(timeout, 3)):
                return None, None, {'error': 'udp_unreachable', 'method': 'socket_check'}
        
        elif is_rtsp or is_rtmp:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            port = parsed.port or (554 if is_rtsp else 1935)
            if not _check_socket_connection(parsed.hostname, port, min(timeout, 3)):
                return None, None, {'error': f'{("RTSP" if is_rtsp else "RTMP")}_unreachable', 'method': 'socket_check'}
        
        cmd = [
            'ffprobe', '-v', 'error',
            '-timeout', str(timeout_us),
            '-skip_initial_bytes', '0',
            '-flags', 'low_delay',
            '-fflags', '+genpts+discardcorrupt',
            '-max_delay', '500000',
            '-reorder_queue_size', '2048',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,codec_name,duration,bit_rate:format=duration,format_name',
            '-of', 'json'
        ]
        
        if is_rtsp:
            cmd.extend(['-rtsp_transport', 'tcp'])
        elif is_rtmp:
            cmd.extend(['-f', 'flv'])
        elif is_udp:
            cmd.extend(['-f', 'mpegts', '-err_detect', 'ignore_err'])
        elif is_ipv6:
            cmd.extend(['-timeout', str(timeout_us)])
        
        if headers:
            cmd.extend([
                '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")}\r\n'
            ])
        
        cmd.append(url)
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout + 2,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                format_info = data.get('format', {})
                format_duration = format_info.get('duration', '0')
                format_name = format_info.get('format_name', 'unknown')
                
                if 'streams' in data and len(data['streams']) > 0:
                    stream = data['streams'][0]
                    width = stream.get('width', 0)
                    height = stream.get('height', 0)
                    
                    if width and height and width > 0 and height > 0:
                        codec = stream.get('codec_name', '未知')
                        bitrate = stream.get('bit_rate', None)
                        
                        return f"{width}*{height}", codec, {
                            'method': 'playback_test',
                            'verified': True,
                            'duration': format_duration,
                            'format': format_name,
                            'bitrate': bitrate,
                            'protocol': 'ipv6' if is_ipv6 else ('rtsp' if is_rtsp else ('rtmp' if is_rtmp else ('udp' if is_udp else 'rtp')))
                        }
                
                return None, None, {'error': 'no_video_stream', 'format': format_name}
                
            except json.JSONDecodeError:
                return None, None, {'error': 'parse_failed'}
        
        error_output = result.stderr.lower() if result.stderr else ''
        
        if 'connection refused' in error_output or 'no such file' in error_output:
            return None, None, {'error': 'connection_refused'}
        elif 'network is unreachable' in error_output or 'address' in error_output:
            return None, None, {'error': 'network_unreachable'}
        elif 'timeout' in error_output:
            return None, None, {'error': 'timeout'}
        else:
            return None, None, {'error': 'probe_failed', 'stderr': result.stderr[:200] if result.stderr else 'unknown'}
            
    except subprocess.TimeoutExpired:
        return None, None, {'error': 'timeout'}
    except Exception as e:
        return None, None, {'error': str(e)}


def _ffprobe_get_audio_info(url, timeout, headers=None):
    """使用ffprobe获取音频流信息（编码格式、采样率、声道数、码率等）"""
    import subprocess
    import json
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name,sample_rate,channels,bit_rate',
            '-of', 'json'
        ]

        if headers:
            cmd.extend([
                '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0")}\r\n'
            ])

        cmd.append(url)

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        if result.returncode != 0:
            return None

        output = json.loads(result.stdout)
        if 'streams' in output and len(output['streams']) > 0:
            stream = output['streams'][0]
            return {
                'codec': stream.get('codec_name', '未知'),
                'sample_rate': stream.get('sample_rate', '未知'),
                'channels': stream.get('channels', '未知'),
                'bit_rate': stream.get('bit_rate', '未知')
            }
        return None
    except Exception:
        return None


def _check_url_has_audio(url, timeout, headers=None):
    """检查URL是否有有效的音频流，返回布尔值"""
    import subprocess
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'csv=p=0'
        ]

        if headers:
            cmd.extend([
                '-headers', f'Referer: {headers.get("Referer", "")}\r\nUser-Agent: {headers.get("User-Agent", "Mozilla/5.0")}\r\n'
            ])

        cmd.append(url)

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        return result.returncode == 0 and result.stdout.strip()
    except Exception:
        return False


def _check_mediainfo_available():
    """检查MediaInfo命令行工具是否可用"""
    import subprocess
    try:
        result = subprocess.run(
            ['mediainfo', '--version'],
            capture_output=True, text=True, timeout=5,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        return result.returncode == 0
    except Exception:
        return False


def _mediainfo_get_resolution(url, timeout, headers=None):
    """使用MediaInfo获取视频分辨率，作为ffprobe的备选方案"""
    import subprocess
    import re

    def _parse_mediainfo_output(output):
        """解析MediaInfo输出，提取分辨率"""
        try:
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if 'x' in line:
                    parts = line.split('x')
                    if len(parts) == 2:
                        width = parts[0].strip()
                        height = parts[1].strip()
                        if width.isdigit() and height.isdigit():
                            w, h = int(width), int(height)
                            if w > 0 and h > 0:
                                return f"{w}*{h}"
            return None
        except Exception:
            return None

    try:
        cmd = [
            'mediainfo', '--Output=Video;%Width%x%Height%', url
        ]

        if headers:
            env = os.environ.copy()
            env['HTTP_REFERER'] = headers.get('Referer', '')
            env['HTTP_USER_AGENT'] = headers.get('User-Agent', 'Mozilla/5.0')
        else:
            env = None

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=False, encoding='utf-8', errors='ignore',
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            env=env
        )

        if result.returncode != 0:
            return None

        return _parse_mediainfo_output(result.stdout)

    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


class IPTVValidator:
    def __init__(self, input_file, output_file=None, max_workers=None, timeout=5, debug=False, original_filename=None, skip_resolution=False, filter_no_audio=False):
        self.input_file = input_file
        self.original_filename = original_filename
        self.max_workers = max_workers or min(30, multiprocessing.cpu_count() * 4)
        self.debug = debug
        self.channels = []
        self.categories = []
        self.batch_size = min(max(self.max_workers * 4, 50), 200)
        self.stop_requested = False
        self.processed_external_urls = set()
        self._active_futures = set()
        self.all_results = []
        self.timeouts = {
            'http_head': min(timeout, 5),
            'http_get': timeout,
            'non_http': min(timeout * 2, 10),
            'ffprobe': min(timeout * 2.5, 12)
        }
        self.skip_resolution = skip_resolution
        self.filter_no_audio = filter_no_audio
        
        # 预编译正则表达式，减少重复编译开销
        self._compile_regex_patterns()
        
        # 初始化HTTP会话和连接池
        self.session = self._init_http_session()

        # 检测文件类型（必须在生成输出文件名之前）
        self.file_type = self._detect_file_type()

        # 生成输出文件名（依赖于file_type）
        self.output_file = output_file or self._generate_output_filename()

        # 确保输出目录存在
        self._check_output_dir()
        self.ffprobe_available = self._check_ffprobe_availability()
        self.mediainfo_available = _check_mediainfo_available()
        if self.debug:
            if self.mediainfo_available:
                print("[调试] MediaInfo可用，将作为ffprobe的备选方案")
            else:
                print("[调试] MediaInfo不可用，仅使用ffprobe")
        
        # 初始化ffprobe进程池
        self.ffprobe_pool = None
        self._validation_pool = None  # 用于验证的线程池
        if self.ffprobe_available and not self.skip_resolution:
            # 使用ThreadPoolExecutor避免ProcessPoolExecutor的多进程启动问题
            self.ffprobe_pool = concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
            
    def _compile_regex_patterns(self):
        """预编译所有使用的正则表达式模式，减少重复编译开销"""
        # M3U文件解析正则表达式
        self.re_extinf_name = re.compile(r'#EXTINF:.*,(.+)')
        self.re_tvg_name = re.compile(r'tvg-name="([^"]+)"')
        self.re_group_title = re.compile(r'group-title="([^"]+)"')
        
        # 分辨率提取正则表达式
        self.re_resolution = re.compile(r'\[(\d+\*\d+)\]')
        
        # URL参数中的分辨率提取正则表达式
        # 支持格式：$3840x2160, ?resolution=1920x1080, &res=720, resolution=1280*720
        self.re_url_resolution_dollar = re.compile(r'\$(\d+)x(\d+)')
        self.re_url_resolution_param = re.compile(r'[?&]resolution=(\d+)[x*](\d+)', re.IGNORECASE)
        self.re_url_res_param = re.compile(r'[?&]res=(\d+)', re.IGNORECASE)
        
        # TXT文件分类解析正则表达式 - 支持逗号或Tab分隔
        self.re_category = re.compile(r'^(.+?)[\t,]\s*#genre#$')
        
        # URL协议检查正则表达式
        self.re_http = re.compile(r'http[s]?://')
        self.re_rtsp = re.compile(r'rtsp://')
        self.re_rtmp = re.compile(r'rtmp://')
        self.re_mms = re.compile(r'mms://')
    
    def stop(self):
        """立即停止验证过程，终止所有线程和进程"""
        self.stop_requested = True
        
        # 取消所有活跃的future对象
        # 创建集合的副本进行迭代，避免"Set changed size during iteration"错误
        for future in list(self._active_futures):
            try:
                future.cancel()
            except Exception:
                pass
        # 清空活跃future集合
        self._active_futures.clear()
        
        # 如果有验证线程池，立即关闭它
        if hasattr(self, '_validation_pool') and self._validation_pool:
            try:
                # 立即关闭线程池，不等待任务完成
                self._validation_pool.shutdown(wait=False)
                self._validation_pool = None  # 释放引用
            except Exception:
                pass
        
        # 如果有ffprobe线程池，立即关闭它而不等待
        if self.ffprobe_pool:
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
        
        # 清理已处理的外部URL集合，释放内存
        if hasattr(self, 'processed_external_urls'):
            self.processed_external_urls.clear()
        
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
        print(f"[调试] 检测文件类型: {self.input_file}")
        # 检查是否为HTTP/HTTPS URL
        if self.input_file.startswith(('http://', 'https://')):
            print("[调试] 检测到URL，开始下载文件")
            # 下载文件并检测类型
            self.input_file = self._download_url(self.input_file)
            print(f"[调试] 下载完成，新文件路径: {self.input_file}")
            # 重新检测下载后的文件类型
            if self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
                return 'm3u'
            elif self.input_file.endswith('.txt'):
                return 'txt'
            else:
                # 读取文件内容检测
                try:
                    with open(self.input_file, 'r', encoding='utf-8') as f:
                        content = f.read(1024)
                        if content.startswith('#EXTM3U'):
                            return 'm3u'
                        elif content and ('#genre#' in content or '\t' in content):
                            return 'txt'
                        elif content:
                            return 'txt'
                except Exception:
                    pass
                return 'txt'
        elif self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
            return 'm3u'
        elif self.input_file.endswith('.txt'):
            return 'txt'
        else:
            # 尝试读取文件内容检测
            try:
                with open(self.input_file, 'r', encoding='utf-8') as f:
                    content = f.read(1024)
                    if content.startswith('#EXTM3U'):
                        return 'm3u'
                    elif content and ('#genre#' in content or '\t' in content):
                        return 'txt'
                    elif content:
                        return 'txt'
            except Exception:
                pass
            return 'txt'

    def _check_ffprobe_availability(self):
        """检查ffprobe是否可用"""
        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True, text=True, timeout=5,
                shell=False
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_output_dir(self):
        """确保输出目录存在"""
        output_dir = os.path.dirname(self.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

    def _generate_output_filename(self):
        """生成输出文件名（使用原始文件名）"""
        if self.original_filename:
            base = os.path.splitext(os.path.basename(self.original_filename))[0]
        else:
            base = os.path.splitext(os.path.basename(self.input_file))[0]
        if self.file_type == 'm3u':
            filename = f"{base}_valid.m3u"
        else:
            filename = f"{base}_valid.txt"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, 'output')
        return os.path.join(output_dir, filename)

    def _download_url(self, url, timeout=30):
        """下载URL内容到临时文件"""
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, allow_redirects=True)
            response.raise_for_status()
            
            # 创建临时文件
            fd, temp_path = tempfile.mkstemp(suffix='.txt')
            with os.fdopen(fd, 'wb') as f:
                f.write(response.content)
            return temp_path
        except Exception as e:
            print(f"[错误] 下载URL失败: {url}, 错误: {str(e)}")
            return None

    def _http_request_with_retry(self, url, method='head', timeout=None, headers=None, retries=3):
        """发送HTTP请求，支持重试机制"""
        if self.stop_requested:
            return None
            
        if timeout is None:
            timeout = self.timeouts['http_head']
        
        session = self.session
        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        for attempt in range(retries + 1):
            # 检查停止标志
            if self.stop_requested:
                return None
            
            try:
                if method.lower() == 'head':
                    response = session.head(url, timeout=timeout, headers=headers, allow_redirects=True)
                else:
                    response = session.get(url, timeout=timeout, headers=headers, allow_redirects=True)
                
                if response.status_code < 400:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = (attempt + 1) * 2
                    if self.debug:
                        print(f"[调试] 收到429错误，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                if self.debug:
                    print(f"[调试] 请求超时 (尝试 {attempt + 1}/{retries + 1}): {url}")
                if attempt < retries:
                    continue
                return None
            except requests.exceptions.RequestException as e:
                if self.debug:
                    print(f"[调试] 请求失败 (尝试 {attempt + 1}/{retries + 1}): {url}, 错误: {str(e)}")
                if attempt < retries:
                    continue
                return None
        
        return None

    def _parse_m3u_file(self):
        """解析M3U文件，提取频道信息"""
        channels = []
        current_category = "未分类"
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#EXTINF:'):
                name_match = self.re_extinf_name.search(line)
                name = name_match.group(1).strip() if name_match else "未知频道"
                
                group_match = self.re_group_title.search(line)
                if group_match:
                    current_category = group_match.group(1).strip()
                
                tvg_match = self.re_tvg_name.search(line)
                if tvg_match:
                    name = tvg_match.group(1).strip()
                
            elif line.startswith('#'):
                continue
            elif line.startswith('http://') or line.startswith('https://'):
                channels.append({
                    'name': name,
                    'url': line.strip(),
                    'category': current_category
                })
            elif not line.startswith('#'):
                if self.re_category.match(line):
                    current_category = self.re_category.match(line).group(1).strip()
                    
        return channels

    def _parse_txt_file(self):
        """解析TXT文件，提取频道信息"""
        channels = []
        current_category = "未分类"
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if self.re_category.match(line):
                current_category = self.re_category.match(line).group(1).strip()
                continue
            
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    if url:
                        channels.append({
                            'name': name,
                            'url': url,
                            'category': current_category
                        })
            elif '\t' in line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    if url:
                        channels.append({
                            'name': name,
                            'url': url,
                            'category': current_category
                        })
                        
        return channels

    def _extract_resolution_from_url(self, url):
        """从URL中提取分辨率信息，返回(宽度, 高度)元组"""
        # 尝试从URL中的分辨率标注提取
        match = self.re_resolution.search(url)
        if match:
            res = match.group(1)
            parts = res.split('*')
            if len(parts) == 2:
                return parts[0], parts[1]
        
        # 尝试从URL参数中提取分辨率
        dollar_match = self.re_url_resolution_dollar.search(url)
        if dollar_match:
            return dollar_match.group(1), dollar_match.group(2)
        
        param_match = self.re_url_resolution_param.search(url)
        if param_match:
            return param_match.group(1), param_match.group(2)
        
        res_match = self.re_url_res_param.search(url)
        if res_match:
            width = res_match.group(1)
            # 常见的分辨率宽度对应高度
            height_map = {
                '720': '720',
                '1080': '1080',
                '4k': '2160',
                '2160': '2160'
            }
            height = height_map.get(width, width)
            return width, height
        
        return None, None

    def _validate_url(self, channel, original_index=None):
        """验证单个URL"""
        if self.stop_requested:
            return None
            
        name = channel.get('name', '未知频道')
        url = channel.get('url', '')
        category = channel.get('category', '未分类')
        
        if original_index is None:
            original_index = channel.get('original_index', 0)
        
        if not url:
            return None
        
        result = {
            'name': name,
            'url': url,
            'category': category,
            'original_index': original_index,
            'valid': False,
            'resolution': None,
            'resolution_width': None,
            'resolution_height': None,
            'codec': None,
            'audio': None,
            'error': None
        }
        
        # 首先检查URL格式
        if not (url.startswith('http://') or url.startswith('https://') or 
                url.startswith('rtsp://') or url.startswith('rtmp://') or 
                url.startswith('udp://') or url.startswith('rtp://')):
            result['error'] = '不支持的URL协议'
            return result
        
        # 对于HTTP(S) URL进行快速HEAD请求检查
        if url.startswith('http://') or url.startswith('https://'):
            # 检测IPv6地址格式（包含方括号，如 http://[2409:8087:8:21::0b]:6610/）
            is_ipv6 = '[' in url and ']' in url
            
            # 跳过UDP代理URL(HTTP代理UDP流的特殊格式)
            if '/udp/' in url.lower() or '/rtp/' in url.lower() or '/rtmp/' in url.lower():
                result['valid'] = True
                result['error'] = None
                width, height = self._extract_resolution_from_url(url)
                result['resolution_width'] = width
                result['resolution_height'] = height
                if width and height:
                    result['resolution'] = f"{width}*{height}"
                return result
            
            # IPv6 URL跳过HTTP请求，初步标记为有效，继续进行分辨率检测
            if is_ipv6:
                result['valid'] = True
                result['error'] = None
                result['is_ipv6'] = True
            else:
                response = self._http_request_with_retry(url, method='head', timeout=self.timeouts['http_head'])
                if not response:
                    response = self._http_request_with_retry(url, method='get', timeout=self.timeouts['http_get'])
                
                if response:
                    result['valid'] = True
                else:
                    result['error'] = 'HTTP请求失败'
                    return result
        else:
            result['is_ipv6'] = False
        
        # 对于非HTTP URL,使用BlackBird-Player风格的试播验证来真正判断有效性
        if url.startswith('udp://') or url.startswith('rtsp://') or url.startswith('rtmp://') or url.startswith('rtp://'):
            result['is_special_protocol'] = True
            if self.ffprobe_available and not self.skip_resolution:
                playback_result = _test_stream_playback(url, self.timeouts['ffprobe'])
                if playback_result and playback_result[0]:
                    result['valid'] = True
                    result['error'] = None
                    result['resolution'], result['codec'], result['audio'] = playback_result
                    if result['resolution']:
                        res_parts = result['resolution'].split('*')
                        if len(res_parts) == 2:
                            result['resolution_width'] = res_parts[0]
                            result['resolution_height'] = res_parts[1]
                else:
                    result['valid'] = False
                    error_info = playback_result[2] if playback_result else {}
                    result['error'] = error_info.get('error', '试播失败')
                    return result
            else:
                result['valid'] = True
                result['error'] = None
                width, height = self._extract_resolution_from_url(url)
                result['resolution_width'] = width
                result['resolution_height'] = height
                if width and height:
                    result['resolution'] = f"{width}*{height}"
            return result
        
        # IPv6 URL使用BlackBird-Player风格的试播验证
        # 采用BlackBird-Player的策略：对于特殊格式的直播源（UDP/RTSP/RTMP/IPv6），通过试播真正验证有效性
        if result.get('is_ipv6'):
            if self.ffprobe_available and not self.skip_resolution:
                playback_result = _test_stream_playback(url, self.timeouts['ffprobe'])
                if playback_result and playback_result[0]:
                    result['valid'] = True
                    result['error'] = None
                    result['resolution'], result['codec'], result['audio'] = playback_result
                    if result['resolution']:
                        res_parts = result['resolution'].split('*')
                        if len(res_parts) == 2:
                            result['resolution_width'] = res_parts[0]
                            result['resolution_height'] = res_parts[1]
                else:
                    error_info = playback_result[2] if playback_result else {}
                    result['error'] = error_info.get('error', 'IPv6试播失败')
                    if 'IPv6' in result['error']:
                        result['valid'] = True
                        width, height = self._extract_resolution_from_url(url)
                        result['resolution_width'] = width
                        result['resolution_height'] = height
                        if width and height:
                            result['resolution'] = f"{width}*{height}"
                    else:
                        result['valid'] = False
                        return result
            else:
                result['valid'] = True
                result['error'] = None
                width, height = self._extract_resolution_from_url(url)
                result['resolution_width'] = width
                result['resolution_height'] = height
                if width and height:
                    result['resolution'] = f"{width}*{height}"
            return result
        
        # 如果启用了ffprobe且不是跳过分辨率检测，获取分辨率
        if self.ffprobe_available and not self.skip_resolution and result['valid']:
            resolution_info = self._get_resolution_with_fallback(url)
            if resolution_info:
                result['resolution'], result['codec'], result['audio'] = resolution_info
                if result['resolution']:
                    res_parts = result['resolution'].split('*')
                    if len(res_parts) == 2:
                        result['resolution_width'] = res_parts[0]
                        result['resolution_height'] = res_parts[1]
            else:
                result['resolution'] = None
        
        # 如果需要检查音频流
        if self.filter_no_audio and result['valid']:
            has_audio = _check_url_has_audio(url, self.timeouts['ffprobe'])
            if not has_audio:
                result['valid'] = False
                result['error'] = '无音频流'
        
        return result

    def _get_resolution_with_fallback(self, url):
        """获取分辨率，支持多种检测方法的fallback"""
        # 检查停止标志
        if self.stop_requested:
            return None
        
        timeout = self.timeouts['ffprobe']
        
        # 方法1: 尝试从HLS播放列表提取分辨率
        if url.endswith('.m3u8') or url.endswith('.m3u') or '/hls/' in url.lower() or '/live/' in url.lower():
            resolution = _get_resolution_from_hls(url, timeout)
            if resolution and resolution[0]:
                return resolution
        
        # 检查停止标志
        if self.stop_requested:
            return None
        
        # 方法2: 尝试使用ffprobe直接检测
        resolution = _ffprobe_get_resolution(url, timeout)
        if resolution and resolution[0]:
            return resolution
        
        # 检查停止标志
        if self.stop_requested:
            return None
        
        # 方法3: 如果有MediaInfo作为备选
        if self.mediainfo_available:
            resolution = _mediainfo_get_resolution(url, timeout)
            if resolution:
                return resolution, 'unknown', {'source': 'mediainfo'}
        
        return None

    def _run_validation(self, progress_callback=None):
        """运行验证过程"""
        print(f"开始验证: {self.input_file}")
        
        # 清除之前的验证结果缓存
        self.all_results = []
        
        # 解析输入文件
        if self.file_type == 'm3u':
            self.channels = self._parse_m3u_file()
        else:
            self.channels = self._parse_txt_file()
        
        total_channels = len(self.channels)
        print(f"共发现 {total_channels} 个频道")
        
        # 发送解析完成进度
        if progress_callback:
            progress_callback({
                'progress': 10,
                'total_channels': total_channels,
                'processed': 0,
                'message': f'文件解析完成，共找到{total_channels}个频道，开始验证频道有效性',
                'stage': 'parsing_completed'
            })
        
        # 创建验证线程池并保存到实例变量
        self._validation_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        try:
            futures = []
            for idx, channel in enumerate(self.channels):
                if self.stop_requested:
                    break
                channel['original_index'] = idx
                future = self._validation_pool.submit(self._validate_url, channel)
                futures.append(future)
                self._active_futures.add(future)
            
            # 收集结果并发送进度更新
            processed_count = 0
            for future in concurrent.futures.as_completed(futures):
                self._active_futures.discard(future)
                if self.stop_requested:
                    continue
                    
                try:
                    result = future.result()
                    if result:
                        self.all_results.append(result)
                        processed_count += 1
                        
                        # 发送进度更新
                        if progress_callback:
                            progress_callback({
                                'progress': 10 + int(processed_count / total_channels * 80),
                                'total_channels': total_channels,
                                'processed': processed_count,
                                'message': f'验证中: {result.get("name", "未知频道")} - {result.get("status", "")}',
                                'stage': 'validation',
                                'channel': result
                            })
                except Exception as e:
                    if self.debug:
                        print(f"[调试] 验证过程出错: {str(e)}")
                    
                    processed_count += 1
                    if progress_callback:
                        progress_callback({
                            'progress': 10 + int(processed_count / total_channels * 80),
                            'total_channels': total_channels,
                            'processed': processed_count,
                            'message': f'验证出错: {str(e)}',
                            'stage': 'validation'
                        })
        finally:
            # 确保关闭线程池
            if self._validation_pool:
                self._validation_pool.shutdown(wait=False)
                self._validation_pool = None
        
        # 按original_index排序，保持原文件中的频道顺序
        self.all_results.sort(key=lambda x: x.get('original_index', 0))
        
        print(f"验证完成，有效频道: {sum(1 for r in self.all_results if r['valid'])}/{len(self.all_results)}")

    def _generate_m3u_output(self):
        """生成M3U格式输出文件"""
        output_lines = ['#EXTM3U']
        
        # 按分类组织结果
        categorized = {}
        for result in self.all_results:
            if not result['valid']:
                continue
            
            category = result['category'] or '未分类'
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(result)
        
        for category, channels in sorted(categorized.items()):
            for channel in channels:
                extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                if channel['resolution']:
                    extinf += f' tvg-shift=1,{channel["name"]}[{channel["resolution"]}]'
                else:
                    extinf += f',{channel["name"]}'
                output_lines.append(extinf)
                output_lines.append(channel['url'])
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"M3U输出已保存到: {self.output_file}")

    def _generate_txt_output(self):
        """生成TXT格式输出文件"""
        output_lines = []
        
        # 添加验证时间戳 - 参考BlackBird-Player的result.txt格式
        timestamp = ValidationTimestamp.get_timestamp()
        output_lines.append(f"🕘️更新时间,#genre#")
        output_lines.append(f"{timestamp}")
        output_lines.append("")
        
        # 按分类组织结果
        categorized = {}
        for result in self.all_results:
            if not result['valid']:
                continue
            
            category = result['category'] or '未分类'
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(result)
        
        for category, channels in sorted(categorized.items()):
            output_lines.append(f"{category},#genre#")
            for channel in channels:
                if channel['resolution']:
                    output_lines.append(f'{channel["name"]}[{channel["resolution"]}],{channel["url"]}')
                else:
                    output_lines.append(f'{channel["name"]},{channel["url"]}')
            output_lines.append("")
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"TXT输出已保存到: {self.output_file}")

    def run(self):
        """运行完整的验证过程"""
        try:
            # 更新验证时间戳
            ValidationTimestamp.update_timestamp()
            
            # 运行验证
            self._run_validation()
            
            # 生成输出
            if self.file_type == 'm3u':
                self._generate_m3u_output()
            else:
                self._generate_txt_output()
            
            return self.output_file
            
        except KeyboardInterrupt:
            print("\n用户中断验证过程")
            return None
        except Exception as e:
            print(f"验证过程出错: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return None

    def read_m3u_file(self, progress_callback=None):
        """解析M3U文件，提取频道信息（公开接口）"""
        self.channels = self._parse_m3u_file()
        if progress_callback:
            progress_callback({
                'progress': 5,
                'total_channels': len(self.channels),
                'processed': 0,
                'message': f'M3U文件解析完成，共找到{len(self.channels)}个频道'
            })
        return self.channels

    def read_txt_file(self, progress_callback=None):
        """解析TXT文件，提取频道信息（公开接口）"""
        self.channels = self._parse_txt_file()
        if progress_callback:
            progress_callback({
                'progress': 5,
                'total_channels': len(self.channels),
                'processed': 0,
                'message': f'TXT文件解析完成，共找到{len(self.channels)}个频道'
            })
        return self.channels

    def read_json_file(self, progress_callback=None):
        """解析JSON文件，提取频道信息（公开接口）"""
        self.channels = self._parse_json_file()
        if progress_callback:
            progress_callback({
                'progress': 5,
                'total_channels': len(self.channels),
                'processed': 0,
                'message': f'JSON文件解析完成，共找到{len(self.channels)}个频道'
            })
        return self.channels

    def _parse_json_file(self):
        """解析JSON文件，提取频道信息"""
        import json
        channels = []
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'url' in item:
                        channels.append({
                            'name': item.get('name', '未知频道'),
                            'url': item['url'],
                            'category': item.get('category', '未分类')
                        })
            elif isinstance(data, dict):
                for name, url in data.items():
                    if isinstance(url, str):
                        channels.append({
                            'name': name,
                            'url': url,
                            'category': '未分类'
                        })
        except Exception as e:
            print(f"[错误] 解析JSON文件失败: {str(e)}")
        return channels

    def validate_channels(self, progress_callback=None):
        """验证所有频道（公开接口）"""
        self._run_validation(progress_callback=progress_callback)
        if progress_callback:
            progress_callback({
                'progress': 90,
                'total_channels': len(self.channels),
                'processed': len(self.all_results),
                'message': f'验证完成，有效频道: {sum(1 for r in self.all_results if r["valid"])}/{len(self.all_results)}',
                'stage': 'validation_completed'
            })
        return self.all_results

    def generate_output_files(self):
        """生成输出文件（公开接口）"""
        if self.file_type == 'm3u':
            self._generate_m3u_output()
        else:
            self._generate_txt_output()
        return self.output_file

    def get_results_summary(self):
        """获取验证结果摘要"""
        total = len(self.all_results)
        valid = sum(1 for r in self.all_results if r['valid'])
        invalid = total - valid
        
        resolution_stats = {}
        for result in self.all_results:
            if result['resolution']:
                res = result['resolution']
                resolution_stats[res] = resolution_stats.get(res, 0) + 1
        
        return {
            'total': total,
            'valid': valid,
            'invalid': invalid,
            'valid_rate': f"{valid/total*100:.1f}%" if total > 0 else "0%",
            'resolution_stats': resolution_stats
        }

    def get_results_by_category(self):
        """按分类获取验证结果"""
        categorized = {}
        for result in self.all_results:
            if not result['valid']:
                continue
            
            category = result['category'] or '未分类'
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(result)
        
        return categorized


def validate_ipTV(input_file, output_file=None, max_workers=None, timeout=5, debug=False, original_filename=None, skip_resolution=False, filter_no_audio=False):
    """
    验证IPTV直播源
    
    参数:
        input_file: 输入文件路径或URL
        output_file: 输出文件路径（可选）
        max_workers: 最大并发数（可选，默认自动计算）
        timeout: 超时时间（秒）
        debug: 是否开启调试模式
        original_filename: 原始文件名（用于生成输出文件名）
        skip_resolution: 是否跳过分辨率检测
        filter_no_audio: 是否过滤无音频流的频道
    
    返回:
        验证结果摘要字典
    """
    validator = IPTVValidator(
        input_file=input_file,
        output_file=output_file,
        max_workers=max_workers,
        timeout=timeout,
        debug=debug,
        original_filename=original_filename,
        skip_resolution=skip_resolution,
        filter_no_audio=filter_no_audio
    )
    
    output_path = validator.run()
    summary = validator.get_results_summary()
    
    if output_path:
        summary['output_file'] = output_path
        print(f"\n验证摘要:")
        print(f"  总频道数: {summary['total']}")
        print(f"  有效频道: {summary['valid']}")
        print(f"  无效频道: {summary['invalid']}")
        print(f"  有效率: {summary['valid_rate']}")
        
        if summary['resolution_stats']:
            print(f"  分辨率分布:")
            for res, count in sorted(summary['resolution_stats'].items(), key=lambda x: int(x[0].split('*')[1]), reverse=True):
                print(f"    {res}: {count}个")
    
    return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='IPTV直播源验证工具')
    parser.add_argument('input', help='输入文件路径或URL')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-w', '--workers', type=int, help='最大并发数')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='超时时间（秒）')
    parser.add_argument('-d', '--debug', action='store_true', help='开启调试模式')
    parser.add_argument('-s', '--skip-resolution', action='store_true', help='跳过分辨率检测')
    parser.add_argument('--no-audio-filter', action='store_true', help='过滤无音频流的频道')
    
    args = parser.parse_args()
    
    validate_ipTV(
        input_file=args.input,
        output_file=args.output,
        max_workers=args.workers,
        timeout=args.timeout,
        debug=args.debug,
        skip_resolution=args.skip_resolution,
        filter_no_audio=args.no_audio_filter
    )
