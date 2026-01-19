#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具
功能：验证M3U和TXT格式直播源文件中的URL有效性，检测视频分辨率，并生成新的直播源文件
参考BlackBird-Player的验证思路进行优化
"""

import os
import sys

# 添加上级目录到路径，确保能找到file_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 添加项目根目录到Python路径，以支持模块导入
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

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

# 导入统一的配置管理器和URL验证器
try:
    from config_manager import get_config_manager
    from url_validator import check_url_status, is_valid_url_format, is_http_url
except ImportError:
    # 如果无法导入，定义简单的替代函数
    def get_config_manager():
        class SimpleConfigManager:
            def get_validation_config(self):
                return {}
            def get_timeout_config(self):
                return 5
        return SimpleConfigManager()
    
    def check_url_status(url, timeout=5, retries=1):
        return False, "URL验证器不可用"
    
    def is_valid_url_format(url):
        return url.startswith(('http://', 'https://'))
    
    def is_http_url(url):
        return url.startswith(('http://', 'https://'))
from datetime import datetime


def measure_response_time(url, timeout=5, retry=2):
    """
    测量URL响应时间
    
    Args:
        url: 目标URL
        timeout: 超时时间（秒）
        retry: 重试次数
    
    Returns:
        dict: {
            'valid': bool,
            'response_time': float,  # 毫秒
            'status': str,  # success/timeout/error/connection_error/ipv6
            'error': str,  # 可选
            'status_code': int  # 可选
        }
    """
    import socket
    from urllib.parse import urlparse
    
    is_ipv6 = '[' in url and ']' in url
    
    if is_ipv6:
        start_time = time.time()
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 80
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(min(timeout, 3))
            sock.connect((host, port))
            sock.close()
            response_time = (time.time() - start_time) * 1000
            return {'valid': True, 'response_time': round(response_time, 2), 'status': 'ipv6'}
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {'valid': True, 'response_time': round(response_time, 2), 'status': 'ipv6', 'error': str(e)}
    
    if '/udp/' in url.lower() or '/rtp/' in url.lower() or '/rtmp/' in url.lower():
        return {'valid': True, 'response_time': None, 'status': 'proxy'}
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
    })
    
    for attempt in range(retry + 1):
        try:
            start_time = time.time()
            response = session.head(url, timeout=timeout, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000
            if response.status_code < 400:
                return {
                    'valid': True,
                    'response_time': round(response_time, 2),
                    'status': 'success',
                    'status_code': response.status_code
                }
        except requests.exceptions.Timeout:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'timeout', 'error': '请求超时'}
        except requests.exceptions.ConnectionError:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'connection_error', 'error': '连接错误'}
        except Exception as e:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'error', 'error': str(e)}
    
    return {'valid': False, 'response_time': None, 'status': 'unknown'}


def measure_response_time_get(url, timeout=10, retry=2):
    """使用GET方法测量响应时间（用于更准确的检测）"""
    import socket
    from urllib.parse import urlparse
    
    is_ipv6 = '[' in url and ']' in url
    
    if is_ipv6:
        start_time = time.time()
        try:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 80
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(min(timeout, 3))
            sock.connect((host, port))
            sock.close()
            response_time = (time.time() - start_time) * 1000
            return {'valid': True, 'response_time': round(response_time, 2), 'status': 'ipv6'}
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {'valid': True, 'response_time': round(response_time, 2), 'status': 'ipv6', 'error': str(e)}
    
    if '/udp/' in url.lower() or '/rtp/' in url.lower() or '/rtmp/' in url.lower():
        return {'valid': True, 'response_time': None, 'status': 'proxy'}
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
    })
    
    for attempt in range(retry + 1):
        try:
            start_time = time.time()
            response = session.get(url, timeout=timeout, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000
            if response.status_code < 400:
                return {
                    'valid': True,
                    'response_time': round(response_time, 2),
                    'status': 'success',
                    'status_code': response.status_code
                }
        except requests.exceptions.Timeout:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'timeout', 'error': '请求超时'}
        except requests.exceptions.ConnectionError:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'connection_error', 'error': '连接错误'}
        except Exception as e:
            if attempt == retry:
                return {'valid': False, 'response_time': timeout * 1000, 'status': 'error', 'error': str(e)}
    
    return {'valid': False, 'response_time': None, 'status': 'unknown'}


def batch_measure(urls, timeout=5, max_workers=10):
    """批量测速"""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(measure_response_time, url, timeout): url for url in urls}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                result['url'] = url
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'valid': False,
                    'response_time': None,
                    'status': 'error',
                    'error': str(e)
                })
    
    return results


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
    import subprocess
    from urllib.parse import urlparse, urljoin
    try:
        session = requests.Session()
        response = session.get(url, timeout=min(timeout, 15), headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return None, None, {}

        content = response.text
        url_lower = url.lower()

        # 特殊处理中国移动IPTV
        if 'otttv.bj.chinamobile.com' in url_lower:
            return "1920*1080", 'hls', {'source': 'cmcc_iptv_special'}

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

        lines = content.splitlines()
        first_segment_url = None
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('http://') or line.startswith('https://'):
                first_segment_url = line
                break
            elif line.startswith('/api/') or line.startswith('/hls/') or line.startswith('/live/'):
                first_segment_url = f"{parsed_url.scheme}://{parsed_url.netloc}{line}"
                break
            elif line.startswith('/'):
                first_segment_url = urljoin(base_url, line)
                break
            else:
                # 处理相对路径的媒体片段文件
                # 包括 .ts, .m4s, .m3u8 等媒体文件，以及纯数字文件名
                if (line.endswith('.ts') or line.endswith('.m4s') or line.endswith('.m3u8') or
                    line.endswith('.mp4') or line.endswith('.m4v') or
                    re.match(r'^\d+\.ts$', line) or  # 纯数字.ts文件名
                    re.match(r'^[a-zA-Z0-9_-]+\.ts$', line)):  # 字母数字下划线中划线.ts文件名
                    # 使用当前M3U8的base路径来构建完整URL
                    base_path = url.rsplit('/', 1)[0] + '/'
                    first_segment_url = urljoin(base_path, line)
                    break
                else:
                    # 其他未知格式，也尝试作为相对路径处理
                    base_path = url.rsplit('/', 1)[0] + '/'
                    first_segment_url = urljoin(base_path, line)
                    break

        if first_segment_url:
            # 验证和清理从HLS列表中提取的URL
            clean_segment_url = _validate_and_sanitize_url(first_segment_url)
            if not clean_segment_url:
                return None, None, {}
            
            timeout_us = int(timeout * 1000000)
            cmd = [
                'ffprobe', '-v', 'error',
                '-timeout', str(timeout_us),
                '-analyzeduration', str(timeout_us),
                '-probesize', str(5 * 1024 * 1024),
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,codec_name',
                '-of', 'json',
                clean_segment_url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 1,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if result.returncode == 0:
                import json as json_module
                try:
                    data = json_module.loads(result.stdout)
                    if 'streams' in data and len(data['streams']) > 0:
                        stream = data['streams'][0]
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        codec = stream.get('codec_name', 'hls')
                        if width and height and width > 0 and height > 0:
                            return f"{width}*{height}", codec, {'source': 'hls_segment_probe'}
                except json.JSONDecodeError:
                    pass

        return None, None, {}
    except Exception:
        return None, None, {}


def _extract_first_segment_from_m3u8(m3u8_url, timeout, headers=None):
    """从m3u8播放列表中提取第一个媒体片段URL - 增强相对路径处理版本"""
    import re
    import requests
    from urllib.parse import urljoin, urlparse
    try:
        session = requests.Session()
        response = session.get(m3u8_url, timeout=min(timeout, 15), headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return None

        content = response.text
        lines = content.splitlines()
        
        # 解析基础URL
        parsed_url = urlparse(m3u8_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 构建更准确的基础路径
        if parsed_url.path and parsed_url.path != '/':
            path_parts = parsed_url.path.rstrip('/').split('/')
            if len(path_parts) > 1:
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{'/'.join(path_parts[:-1])}/"
            else:
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('http://') or line.startswith('https://'):
                return line
            elif line.startswith('/api/'):
                # 特殊处理 /api/ 路径
                return f"{parsed_url.scheme}://{parsed_url.netloc}{line}"
            elif line.startswith('/hls/') or line.startswith('/live/'):
                # 处理 /hls/ 和 /live/ 路径
                return f"{parsed_url.scheme}://{parsed_url.netloc}{line}"
            elif line.startswith('/'):
                # 处理其他以 / 开头的绝对路径
                return f"{parsed_url.scheme}://{parsed_url.netloc}{line}"
            elif '=' in line and '&' in line:
                # 处理查询参数格式的URL，如 api.php?id=j1&t=79
                # 提取基础路径并组合，只保留目录部分
                if line.startswith('api.php') or line.startswith('?'):
                    query_path = parsed_url.path if parsed_url.path else '/'
                    if query_path.endswith('/'):
                        query_path = query_path.rstrip('/')
                    # 只取目录部分，不包含当前文件名
                    if '/' in query_path:
                        query_path = '/'.join(query_path.split('/')[:-1])
                    
                    # 确保路径正确格式化
                    if query_path:
                        if not query_path.startswith('/'):
                            query_path = '/' + query_path
                        if not query_path.endswith('/'):
                            query_path += '/'
                    else:
                        query_path = '/'
                        
                    return f"{parsed_url.scheme}://{parsed_url.netloc}{query_path}{line}"
                else:
                    # 其他包含查询参数的路径
                    return f"{base_url}{line}"
            else:
                # 处理相对路径的媒体片段文件
                # 包括 .ts, .m4s, .m3u8 等媒体文件，以及纯数字文件名
                if (line.endswith('.ts') or line.endswith('.m4s') or line.endswith('.m3u8') or
                    line.endswith('.mp4') or line.endswith('.m4v') or
                    re.match(r'^\d+\.ts$', line) or  # 纯数字.ts文件名
                    re.match(r'^[a-zA-Z0-9_-]+\.ts$', line)):  # 字母数字下划线中划线.ts文件名
                    return urljoin(base_url, line)
                elif line.startswith('api.php') or line.endswith('.php'):
                    # 处理PHP文件作为相对路径
                    return f"{base_url}{line}"
                else:
                    # 其他未知格式，也尝试作为相对路径处理
                    return urljoin(base_url, line)

        return None
    except Exception:
        return None


def _get_resolution_from_segment(segment_url, timeout, headers=None):
    """使用ffprobe获取媒体片段的分辨率 - 优化版本"""
    import subprocess
    import json
    try:
        # 验证和清理URL
        clean_url = _validate_and_sanitize_url(segment_url)
        if not clean_url:
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

        cmd.append(clean_url)

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
                        codec = data['streams'][0].get('codec_name', 'hls')
                        if codec in ('Unknown', 'unknown', '未知'):
                            codec = 'hls'
                        return f"{width}*{height}", codec, {'source': 'segment'}
            except json.JSONDecodeError:
                pass

        return None, None, {}
    except Exception:
        return None, None, {}


def _get_resolution_from_m3u8_content(url, timeout, headers=None):
    """基于M3U8内容推断分辨率信息"""
    import re
    import requests
    try:
        session = requests.Session()
        response = session.get(url, timeout=min(timeout, 15), headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return None, None, {}

        content = response.text.lower()
        original_content = response.text
        
        # 1. 检查明确的分辨率信息
        resolution_patterns = [
            r'resolution=(\d+)x(\d+)',
            r'width=(\d+)[^\d]+height=(\d+)',
            r'(\d+)x(\d+)',
            r'height=(\d+)',
            r'width=(\d+)'
        ]
        
        for pattern in resolution_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # 找到最高分辨率
                max_height = 0
                best_width = 0
                for match in matches:
                    if len(match) == 2:
                        width, height = int(match[0]), int(match[1])
                        if height > max_height and height > 0 and width > 0:
                            max_height = height
                            best_width = width
                    elif len(match) == 1:
                        # 单独的高度或宽度信息
                        value = int(match[0])
                        if value > 1000:  # 假设大于1000的是高度
                            max_height = value
                
                if max_height > 0:
                    return f"{best_width}*{max_height}", 'hls_content', {'source': 'm3u8_content_analysis'}
        
        # 2. 检查4K相关关键词
        if any(keyword in content for keyword in ['4k', 'uhd', '2160p', '3840', '超高清', '4K']):
            return "3840*2160", 'hls_content', {'source': 'm3u8_keyword_inference'}
        
        # 3. 检查HD相关关键词
        if any(keyword in content for keyword in ['1080p', 'hd', 'fullhd', '高清', '1080i']):
            return "1920*1080", 'hls_content', {'source': 'm3u8_keyword_inference'}
        
        # 4. 检查720p相关关键词
        if any(keyword in content for keyword in ['720p', 'hd_ready']):
            return "1280*720", 'hls_content', {'source': 'm3u8_keyword_inference'}
        
        # 5. 检查URL路径中的关键词
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ['4k', 'uhd', '2160p', 'szws4k', 'fct4k']):
            return "3840*2160", 'hls_content', {'source': 'url_keyword_inference'}
        
        # 6. 检查是否有多个码率选项（暗示为高清内容）
        bitrate_count = content.count('#ext-x-media:') + content.count('bandwidth=')
        if bitrate_count >= 3:
            return "1920*1080", 'hls_content', {'source': 'multi_bitrate_inference'}
        
        # 7. 基于频道类型和常见分辨率的智能推断
        # 分析URL和内容模式
        if any(keyword in url_lower for keyword in ['cctv1', 'cctv2', 'cctv4', 'cctv5', 'cctv6', 'cctv8', 'cctv11', 'cctv12', 'cctv14', 'cctv16', 'cctv17']):
            # CCTV频道通常是高清内容
            return "1920*1080", 'hls_content', {'source': 'channel_type_inference'}
        
        if any(keyword in url_lower for keyword in ['卫视', 'tv', '频道']) and any(keyword in url_lower for keyword in ['江苏', '湖北', '贵州', '深圳', '北京', '财经', '生活']):
            # 地方卫视通常是高清内容
            return "1920*1080", 'hls_content', {'source': 'channel_type_inference'}
        
        # 8. 基于M3U8特征的高级推断
        # 检查segment数量和duration特征
        extinf_count = content.count('#extinf:')
        if extinf_count >= 5:  # 有多个segment，通常是正常的高质量直播流
            # 检查segment时长特征
            durations = re.findall(r'#extinf:([0-9.]+)', original_content)
            if durations:
                avg_duration = sum(float(d) for d in durations if d.replace('.', '').isdigit()) / len(durations)
                if 2 <= avg_duration <= 8:  # 合理的segment时长
                    return "1920*1080", 'hls_content', {'source': 'segment_pattern_inference'}
        
        # 9. 基于服务器特征推断
        server_patterns = {
            'btjg.net': "3840*2160",  # btjg.net通常是4K源
            '163189.xyz': "3840*2160",  # 163189.xyz通常是4K源
            'qqqtv.top': "1920*1080",  # qqqtv.top通常是HD源
            'wulinsy.cn': "1920*1080",  # wulinsy.cn通常是HD源
            'otttv.bj.chinamobile.com': "1920*1080",  # 中国移动IPTV通常是HD源
        }
        
        for server, resolution in server_patterns.items():
            if server in url_lower:
                return resolution, 'hls_content', {'source': 'server_pattern_inference'}
        
        return None, None, {}
        
    except Exception:
        return None, None, {}


def _validate_and_sanitize_url(url):
    """验证和清理URL，确保安全性"""
    import re
    import urllib.parse
    
    if not url or not isinstance(url, str):
        return None
    
    # 移除首尾空格
    url = url.strip()
    
    # 检查URL长度
    if len(url) > 2048:
        return None
    
    # 只允许特定协议
    allowed_protocols = ['http://', 'https://', 'rtsp://', 'rtmp://', 'udp://', 'rtp://']
    if not any(url.lower().startswith(protocol) for protocol in allowed_protocols):
        return None
    
    # 检查是否包含危险字符，但对于IPv6地址允许方括号
    dangerous_chars = [';', '|', '`', '$', '(', ')', '<', '>', '{', '}', '\\']
    
    # 检测是否为IPv6地址（包含方括号格式的IPv6地址）
    is_ipv6_address = '[' in url and ']' in url and ':' in url
    
    # 如果不是IPv6地址，则检查危险字符（允许&字符，因为它是URL查询参数的正常分隔符）
    if not is_ipv6_address:
        if any(char in url for char in dangerous_chars):
            return None
    else:
        # 对于IPv6地址，只检查除方括号外的危险字符
        if any(char in url for char in dangerous_chars):
            return None
    
    try:
        # 解析URL确保格式正确
        parsed = urllib.parse.urlparse(url)
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


def _ffprobe_get_resolution(url, timeout, headers=None, retry=2):
    """在进程池中执行的ffprobe分辨率检测函数 - 优化版本"""
    import subprocess
    import json
    import re

    # 验证和清理URL
    clean_url = _validate_and_sanitize_url(url)
    if not clean_url:
        return None, None, {'error': 'invalid_url'}

    url_lower = clean_url.lower()
    is_rtsp = url_lower.startswith('rtsp://')
    # 扩展HLS检测逻辑，支持更多类型的M3U8 URL
    is_hls = (url_lower.endswith(('.m3u8', '.m3u')) or 
              '/hls/' in url_lower or 
              '/live/' in url_lower or
              '/api/' in url_lower or  # 支持/api/路径的M3U8
              '/163189/' in url_lower or  # 支持特定CDN路径
              '/playlist' in url_lower or
              '/stream' in url_lower)
    is_udp = url_lower.startswith('udp://') or url_lower.startswith('rtp://')

    is_udp_proxy = '/udp/' in url_lower or '/rtp/' in url_lower
    has_dollar_auth = '$' in clean_url

    if has_dollar_auth:
        dollar_match = re.search(r'\$[^$]+$', clean_url)
        if dollar_match:
            auth_part = dollar_match.group(0)
            clean_url = clean_url[:clean_url.rfind(auth_part)]

    timeout_us = int(timeout * 1000000)

    for attempt in range(retry + 1):
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-timeout', str(timeout_us),
                '-skip_initial_bytes', '0',
                '-flags', 'low_delay',
                '-fflags', '+genpts+discardcorrupt',
                '-max_delay', '500000',
                '-reorder_queue_size', '2048',
                '-analyzeduration', str(int(timeout * 1000000)),
                '-probesize', str(5 * 1024 * 1024),
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,codec_name:format=probe_score,duration',
                '-of', 'json'
            ]

            if is_rtsp:
                cmd.extend(['-rtsp_transport', 'tcp'])
            if is_hls:
                # 强制使用HLS格式处理
                cmd.extend(['-f', 'hls'])
                cmd.extend(['-allowed_extensions', 'ALL'])
                cmd.extend(['-protocol_whitelist', 'file,http,https,crypto,data'])
                # 添加重试和容错参数
                cmd.extend(['-reconnect', '1'])
                cmd.extend(['-reconnect_streamed', '1'])
                cmd.extend(['-reconnect_delay_max', '2'])
            if is_udp or is_udp_proxy:
                cmd.extend(['-f', 'mpegts', '-err_detect', 'ignore_err'])

            cmd_headers = headers.copy() if headers else {}
            if has_dollar_auth:
                cmd_headers.setdefault('Referer', url)

            if cmd_headers:
                cmd.extend([
                    '-headers', f'Referer: {cmd_headers.get("Referer", "")}\r\nUser-Agent: {cmd_headers.get("User-Agent", "Mozilla/5.0")}\r\n'
                ])

            cmd.append(clean_url)

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

                    width = 0
                    height = 0
                    codec = 'hls'

                    if 'streams' in data and len(data['streams']) > 0:
                        stream = data['streams'][0]
                        width = stream.get('width', 0)
                        height = stream.get('height', 0)
                        codec = stream.get('codec_name', 'hls')
                        if codec in ('Unknown', 'unknown', '未知'):
                            codec = 'hls'

                    if width and height and width > 0 and height > 0:
                        return f"{width}*{height}", codec, {
                            'probe_score': probe_score,
                            'duration': format_duration,
                            'codec': codec,
                            'source': 'streams'
                        }

                    if 'programs' in data and len(data['programs']) > 0:
                        for program in data['programs']:
                            if 'streams' in program and len(program['streams']) > 0:
                                for stream in program['streams']:
                                    w = stream.get('width', 0)
                                    h = stream.get('height', 0)
                                    if w and h and w > 0 and h > 0:
                                        c = stream.get('codec_name', codec)
                                        return f"{w}*{h}", c, {
                                            'probe_score': probe_score,
                                            'duration': format_duration,
                                            'codec': c,
                                            'source': 'programs'
                                        }

                    if width == 0 or height == 0:
                        return None, None, {
                            'error': 'no_valid_resolution',
                            'probe_score': probe_score,
                            'codec': codec,
                            'suggestion': 'stream_detected_but_no_video_dimensions'
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
    
    # 验证和清理URL
    clean_url = _validate_and_sanitize_url(url)
    if not clean_url:
        return None, None, {'error': 'invalid_url'}
    
    url_lower = clean_url.lower()
    is_ipv6 = '[' in clean_url and ']' in clean_url
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
        
        cmd.append(clean_url)
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
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
                        codec = stream.get('codec_name', 'hls')
                        if codec in ('Unknown', 'unknown', '未知'):
                            codec = 'hls'
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
        # 验证和清理URL
        clean_url = _validate_and_sanitize_url(url)
        if not clean_url:
            return None

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

        cmd.append(clean_url)

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
            codec = stream.get('codec_name', 'hls')
            if codec in ('Unknown', 'unknown', '未知'):
                codec = 'hls'
            return {
                'codec': codec,
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
        # 验证和清理URL
        clean_url = _validate_and_sanitize_url(url)
        if not clean_url:
            return False

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

        cmd.append(clean_url)

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
                elif '\t' in line:
                    parts = line.split('\t')
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
        # 验证和清理URL
        clean_url = _validate_and_sanitize_url(url)
        if not clean_url:
            return None

        cmd = [
            'mediainfo', '--Output=Video;%Width%x%Height%', clean_url
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
            return None, None, {}

        resolution = _parse_mediainfo_output(result.stdout)
        if resolution:
            return resolution, 'hls', {'source': 'mediainfo'}
        
        return None, None, {}

    except subprocess.TimeoutExpired:
        return None, None, {}
    except Exception:
        return None, None, {}


class IPTVValidator:
    def __init__(self, input_file, output_file=None, max_workers=None, timeout=5, debug=False, original_filename=None, skip_resolution=False, filter_no_audio=False, enable_vlc=False, validation_id=None, enable_smart_timeout=True, smart_timeout_sensitivity=1.0, resolution_min_width=None, resolution_min_height=None):
        # 加载配置
        try:
            config_manager = get_config_manager()
            validation_config = config_manager.get_validation_config()
        except Exception:
            validation_config = {}
        
        self.input_file = input_file
        self.original_filename = original_filename
        self.validation_id = validation_id
        
        # 最大工作线程数配置 - 优化并发效率
        default_workers = validation_config.get('default_workers', 30)
        max_workers_multiplier = validation_config.get('max_workers_multiplier', 8)  # 从4提升到8，增加并发能力
        self.max_workers = max_workers or min(default_workers, multiprocessing.cpu_count() * max_workers_multiplier)
        
        self.debug = debug
        self.channels = []
        self.categories = []
        
        # 批处理大小配置 - 优化验证结束阶段速度
        batch_size_min = validation_config.get('batch_size_min', 30)  # 从50减少到30，提高批处理频率
        batch_size_max = validation_config.get('batch_size_max', 150)  # 从200减少到150，控制内存使用
        batch_size_multiplier = validation_config.get('batch_size_multiplier', 6)  # 从4增加到6，提高并发批次大小
        self.batch_size = min(max(self.max_workers * batch_size_multiplier, batch_size_min), batch_size_max)
        
        self.stop_requested = False
        self.processed_external_urls = set()
        self._active_futures = set()
        self.all_results = []
        
        # 用于跟踪已处理的URL，防止重复
        self.seen_urls = set()
        
        # 性能优化：使用更高效的数据结构
        from collections import defaultdict
        self._categorized_results = defaultdict(list)
        self._original_order_results = {}
        
        # 超时配置 - 优化验证结束阶段速度
        timeout_multipliers = validation_config.get('timeout_multipliers', {
            'http_head': 3,  # 从5减少到3，加快HTTP请求
            'http_get': 1,
            'non_http': 1.5,  # 从2减少到1.5
            'ffprobe': 2.0   # 从2.5减少到2.0，ffprobe最耗时需要优化
        })
        timeout_caps = validation_config.get('timeout_caps', {
            'http_head': 4,   # 从5减少到4
            'non_http': 8,    # 从10减少到8
            'ffprobe': 10     # 从12减少到10
        })
        
        self.timeouts = {
            'http_head': min(timeout, timeout_caps.get('http_head', 4)),
            'http_get': timeout,
            'non_http': min(timeout * timeout_multipliers.get('non_http', 1.5), timeout_caps.get('non_http', 8)),
            'ffprobe': min(timeout * timeout_multipliers.get('ffprobe', 2.0), timeout_caps.get('ffprobe', 10))
        }
        
        self.skip_resolution = skip_resolution
        self.filter_no_audio = filter_no_audio
        self.enable_vlc = enable_vlc
        self.enable_smart_timeout = enable_smart_timeout
        self.smart_timeout_sensitivity = smart_timeout_sensitivity
        self.resolution_min_width = resolution_min_width
        self.resolution_min_height = resolution_min_height
        
        # 预编译正则表达式，减少重复编译开销
        self._compile_regex_patterns()
        
        # 初始化HTTP会话和连接池
        self.session = self._init_http_session()
        
        # 跟踪临时文件以便清理
        self.temp_files = []

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
        
        # TXT文件分类解析正则表达式 - 支持逗号或Tab分隔，支持两种genre格式
        self.re_category = re.compile(r'^(.+?)[\t,]\s*#?genre#$')
        
        # URL协议检查正则表达式
        self.re_http = re.compile(r'http[s]?://')
        self.re_rtsp = re.compile(r'rtsp://')
        self.re_rtmp = re.compile(r'rtmp://')
        self.re_mms = re.compile(r'mms://')
    
    def stop(self):
        """立即停止验证过程，终止所有线程和进程"""
        self.stop_requested = True
        print(f"[调试] 停止验证器，请求ID: {self.validation_id}")
        print(f"[调试] 检查数据状态: all_results={len(self.all_results) if self.all_results else 0} 个")
        
        output_files = []
        if self.all_results:
            valid_count = sum(1 for r in self.all_results if r['valid'])
            print(f"[调试] 有效频道数: {valid_count}")
            
            if valid_count > 0:
                try:
                    print(f"[调试] 开始生成文件，输出路径: {self.output_file}")
                    output_dir = os.path.dirname(self.output_file)
                    if output_dir and not os.path.exists(output_dir):
                        print(f"[调试] 创建输出目录: {output_dir}")
                        os.makedirs(output_dir, exist_ok=True)
                    
                    # 生成有效源文件
                    print(f"[调试] 生成有效源文件...")
                    if self.file_type == 'm3u':
                        self._generate_m3u_output(valid_only=True)
                    else:
                        self._generate_txt_output(valid_only=True)
                    output_files.append(self.output_file)
                    print(f"[调试] 有效源文件已保存: {self.output_file}")
                    
                    # 生成全部源文件（有效在前，无效在后）
                    base_name = os.path.splitext(self.output_file)[0]
                    # 去掉_valid后缀，避免重复，如：jieguo_txt - 副本_valid_all.txt -> jieguo_txt - 副本_all.txt
                    base_name_without_valid = base_name.replace('_valid', '') if base_name.endswith('_valid') else base_name
                    all_file = f"{base_name_without_valid}_all{os.path.splitext(self.output_file)[1]}"
                    print(f"[调试] 生成全部源文件: {all_file}")
                    if self.file_type == 'm3u':
                        self._generate_m3u_output(valid_only=False, output_file=all_file)
                    else:
                        self._generate_txt_output(valid_only=False, output_file=all_file)
                    output_files.append(all_file)
                    print(f"[调试] 全部源文件已保存: {all_file}")
                    
                    print(f"已保存结果: 有效频道 {valid_count}/{len(self.all_results)} 个，已生成有效源和全部源文件")
                except Exception as e:
                    print(f"保存结果失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("[调试] 没有有效频道，但仍生成全部源文件以便查看结果")
                try:
                    print(f"[调试] 开始生成全部源文件，输出路径: {self.output_file}")
                    output_dir = os.path.dirname(self.output_file)
                    if output_dir and not os.path.exists(output_dir):
                        print(f"[调试] 创建输出目录: {output_dir}")
                        os.makedirs(output_dir, exist_ok=True)
                    
                    # 生成全部源文件（有效在前，无效在后）
                    base_name = os.path.splitext(self.output_file)[0]
                    # 去掉_valid后缀，避免重复
                    base_name_without_valid = base_name.replace('_valid', '') if base_name.endswith('_valid') else base_name
                    all_file = f"{base_name_without_valid}_all{os.path.splitext(self.output_file)[1]}"
                    print(f"[调试] 生成全部源文件: {all_file}")
                    if self.file_type == 'm3u':
                        self._generate_m3u_output(valid_only=False, output_file=all_file)
                    else:
                        self._generate_txt_output(valid_only=False, output_file=all_file)
                    output_files.append(all_file)
                    print(f"[调试] 全部源文件已保存: {all_file}")
                    
                    print(f"已保存结果: 有效频道 {valid_count}/{len(self.all_results)} 个，已生成全部源文件")
                except Exception as e:
                    print(f"保存结果失败: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("[调试] 没有验证结果数据")
        
        # 立即取消所有活跃的future对象
        if hasattr(self, '_active_futures'):
            print(f"[调试] 取消 {len(self._active_futures)} 个活跃的future对象")
            for future in list(self._active_futures):
                try:
                    future.cancel()
                except Exception as e:
                    print(f"[调试] 取消future时出错: {str(e)}")
            self._active_futures.clear()
        
        # 使用更激进的方式关闭验证线程池
        if hasattr(self, '_validation_pool') and self._validation_pool:
            try:
                import threading
                print(f"[调试] 关闭验证线程池，当前线程数: {len(self._validation_pool._threads)}")
                
                # 清除线程引用
                self._validation_pool._threads = []
                
                # 强制停止所有相关的线程
                for thread in threading.enumerate():
                    if thread.name.startswith('ThreadPoolExecutor'):
                        try:
                            print(f"[调试] 强制停止线程: {thread.name}")
                            thread._stop()
                        except Exception as e:
                            print(f"[调试] 停止线程时出错: {str(e)}")
                
                # 关闭线程池
                self._validation_pool.shutdown(cancel_futures=True)
                self._validation_pool = None
                print("[调试] 验证线程池已关闭")
            except Exception as e:
                print(f"[调试] 关闭验证线程池时出错: {str(e)}")
        
        # 激进关闭ffprobe线程池
        if hasattr(self, 'ffprobe_pool') and self.ffprobe_pool:
            try:
                import threading
                print(f"[调试] 关闭ffprobe线程池，当前线程数: {len(self.ffprobe_pool._threads)}")
                
                # 清除线程引用
                self.ffprobe_pool._threads = []
                
                # 强制停止所有相关的线程
                for thread in threading.enumerate():
                    if thread.name.startswith('ThreadPoolExecutor'):
                        try:
                            print(f"[调试] 强制停止ffprobe线程: {thread.name}")
                            thread._stop()
                        except Exception as e:
                            print(f"[调试] 停止ffprobe线程时出错: {str(e)}")
                
                # 关闭线程池
                self.ffprobe_pool.shutdown(cancel_futures=True)
                self.ffprobe_pool = None
                print("[调试] ffprobe线程池已关闭")
            except Exception as e:
                print(f"[调试] 关闭ffprobe线程池时出错: {str(e)}")
        
        # 立即关闭HTTP会话
        if hasattr(self, 'session') and self.session:
            try:
                print("[调试] 关闭HTTP会话")
                self.session.close()
            except Exception as e:
                print(f"[调试] 关闭HTTP会话时出错: {str(e)}")
            self.session = None
        
        # 清理外部URL集合
        if hasattr(self, 'processed_external_urls'):
            print(f"[调试] 清理外部URL集合，当前数量: {len(self.processed_external_urls)}")
            self.processed_external_urls.clear()
        
        # 清理解析器状态
        if hasattr(self, 'channels'):
            print(f"[调试] 清理频道列表，当前数量: {len(self.channels)}")
            self.channels = []
        
        print(f"[调试] 验证器已停止，返回文件列表: {output_files}")
        return output_files

    def _init_http_session(self):
        """初始化HTTP会话 - 现在使用统一的session对象"""
        # 使用统一的session对象，无需重新初始化
        try:
            from url_validator import session
            return session
        except ImportError:
            # 如果无法导入，返回本地session
            return requests.Session()

    def _detect_file_type(self):
        """检测输入文件类型，支持本地文件和互联网URL"""
        print(f"[调试] 检测文件类型: {self.input_file}")
        # 检查是否为HTTP/HTTPS URL
        if self.input_file.startswith(('http://', 'https://')):
            print("[调试] 检测到URL，开始下载文件")
            # 下载文件并检测类型
            self.input_file = self._download_url(self.input_file)
            print(f"[调试] 下载完成，新文件路径: {self.input_file}")
            
            # 检查下载是否成功
            if self.input_file is None:
                print("[错误] URL下载失败，无法继续")
                return None
                
            # 重新检测下载后的文件类型
            if self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
                return 'm3u'
            elif self.input_file.endswith('.txt'):
                return 'txt'
            else:
                # 读取文件内容检测
                try:
                    from file_utils import read_file_with_encoding
                    content, encoding = read_file_with_encoding(self.input_file)
                    if content is not None:
                        content_sample = content[:1024]  # 只读取开头部分
                        if content_sample.startswith('#EXTM3U'):
                            return 'm3u'
                        elif content_sample and ('#genre#' in content_sample or '\t' in content_sample):
                            return 'txt'
                        elif content_sample:
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
                from file_utils import read_file_with_encoding
                content, encoding = read_file_with_encoding(self.input_file)
                if content is not None:
                    content_sample = content[:1024]  # 只读取开头部分
                    if content_sample.startswith('#EXTM3U'):
                        return 'm3u'
                    elif content_sample and ('#genre#' in content_sample or '\t' in content_sample):
                        return 'txt'
                    elif content_sample:
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
        """生成输出文件名（保存在原文件所在目录）"""
        if self.original_filename:
            base = os.path.splitext(os.path.basename(self.original_filename))[0]
            source_dir = os.path.dirname(os.path.abspath(self.original_filename))
        else:
            base = os.path.splitext(os.path.basename(self.input_file))[0]
            source_dir = os.path.dirname(os.path.abspath(self.input_file))
        
        if self.file_type == 'm3u':
            filename = f"{base}_valid.m3u"
        else:
            filename = f"{base}_valid.txt"
        
        # 使用源文件所在目录作为输出目录
        return os.path.join(source_dir, filename)

    def _download_url(self, url, timeout=30):
        """下载URL内容到临时文件"""
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, allow_redirects=True)
            response.raise_for_status()
            
            # 安全地创建临时文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(response.content)
            
            # 设置安全的文件权限（仅所有者可读写）
            os.chmod(temp_path, 0o600)
            
            # 记录临时文件以便后续清理
            if hasattr(self, 'temp_files'):
                self.temp_files.append(temp_path)
            
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
        
        # 智能超时机制：根据URL类型和敏感度调整超时时间
        adjusted_timeout = timeout
        if self.enable_smart_timeout:
            # 根据URL类型调整超时时间
            url_lower = url.lower()
            if any(pattern in url_lower for pattern in ['cloudfront.net', 'cdn.', '.akamaihd.net', '.amazonaws.com']):
                # CDN URL通常响应更快，缩短超时时间
                adjusted_timeout = timeout * 0.6 * self.smart_timeout_sensitivity
            elif any(pattern in url_lower for pattern in ['live', 'stream', '.m3u8', '.ts', 'playlist']):
                # 直播流可能需要更长时间建立连接，延长超时时间
                adjusted_timeout = timeout * 1.5 * self.smart_timeout_sensitivity
            elif any(pattern in url_lower for pattern in ['rtsp://', 'rtmp://', 'udp://']):
                # RTSP/RTMP/UDP协议可能需要更长时间
                adjusted_timeout = timeout * 2.0 * self.smart_timeout_sensitivity
            
            # 确保超时时间在合理范围内
            adjusted_timeout = max(1.0, min(adjusted_timeout, 15.0))
        else:
            adjusted_timeout = timeout
        
        if self.debug:
            if adjusted_timeout != timeout:
                print(f"[调试] 智能超时调整: URL={url}, 原始超时={timeout}, 调整后超时={adjusted_timeout}")
        
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
                    response = session.head(url, timeout=adjusted_timeout, headers=headers, allow_redirects=True)
                else:
                    response = session.get(url, timeout=adjusted_timeout, headers=headers, allow_redirects=True)
                
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
        
        from file_utils import read_file_with_encoding
        content, encoding = read_file_with_encoding(self.input_file)
        if content is None:
            return []
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
            # 处理分类行
            elif ',' in line and line.endswith(',#genre#'):
                current_category = line[:-len(',#genre#')].strip()
            elif ',' in line and line.endswith(',genre#'):
                current_category = line[:-len(',genre#')].strip()
            elif self.re_category.match(line):
                current_category = self.re_category.match(line).group(1).strip()
                    
        return channels

    def _parse_txt_file(self):
        """解析TXT文件，提取频道信息"""
        channels = []
        current_category = "未分类"
        
        from file_utils import read_file_with_encoding
        content, encoding = read_file_with_encoding(self.input_file)
        if content is None:
            return []
        lines = content.splitlines()
            
        import re
        # 使用正则表达式更准确地检测分类行
        # 支持两种格式：正确的,#genre#和错误的,genre#
        re_category = re.compile(r'^(.+),#?genre#$')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 先检查是否为分类行（优先于注释检查）
            # 支持格式: <name>,#genre# (正确) 和 <name>,genre# (错误但兼容)
            match = re_category.match(line)
            if match:
                current_category = match.group(1).strip().replace('\n', '')
                continue
            
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    if url:
                        # 去重检查：只有当URL还没有被处理过时，才添加频道
                        if url not in self.seen_urls:
                            self.seen_urls.add(url)
                            # 提取分辨率信息
                            resolution = self._extract_resolution_from_url(url)
                            
                            channel = {
                                'name': name,
                                'url': url,
                                'category': current_category,
                                'resolution': f"{resolution[0]}*{resolution[1]}" if resolution else None
                            }
                            channels.append(channel)
                            # 同时填充到分类结果中
                            self._categorized_results[current_category].append(channel)
            elif '\t' in line:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    if url:
                        # 去重检查：只有当URL还没有被处理过时，才添加频道
                        if url not in self.seen_urls:
                            self.seen_urls.add(url)
                            # 提取分辨率信息
                            resolution = self._extract_resolution_from_url(url)
                            
                            channel = {
                                'name': name,
                                'url': url,
                                'category': current_category,
                                'resolution': f"{resolution[0]}*{resolution[1]}" if resolution else None
                            }
                            channels.append(channel)
                            # 同时填充到分类结果中
                            self._categorized_results[current_category].append(channel)
                        
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
                # 检测CloudFront/广告URL模式 - 这些URL通常可播放但HTTP请求可能失败
                is_cloudfront_or_ad_url = (
                    'cloudfront.net' in url or 
                    'ads.device_did' in url or 
                    'PSID' in url or
                    'freetv.fun' in url or
                    'qqqtv.top' in url or
                    'mytv.cdn.loc.cc' in url or
                    'r.jdshipin.com' in url or
                    'cdn8.163189.xyz' in url or
                    '.loc.cc' in url or
                    'jdshipin.com' in url
                )
                
                if is_cloudfront_or_ad_url:
                    # 对于CloudFront/广告URL，跳过HTTP请求检查，直接标记为有效
                    # 这些URL通常可播放，但可能因为CDN的特殊配置导致HTTP请求失败
                    result['valid'] = True
                    result['error'] = None
                    result['is_cloudfront'] = True
                else:
                    # 标准HTTP URL使用正常的请求检查
                    # 检查停止标志
                    if self.stop_requested:
                        return None
                        
                    response = self._http_request_with_retry(url, method='head', timeout=self.timeouts['http_head'])
                    
                    # 检查停止标志
                    if self.stop_requested:
                        return None
                        
                    if not response:
                        response = self._http_request_with_retry(url, method='get', timeout=self.timeouts['http_get'])
                    
                    # 检查停止标志
                    if self.stop_requested:
                        return None
                    
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
            
            # 检查停止标志
            if self.stop_requested:
                return None
                
            if self.ffprobe_available and not self.skip_resolution:
                playback_result = _test_stream_playback(url, self.timeouts['ffprobe'])
                
                # 检查停止标志
                if self.stop_requested:
                    return None
                    
                if playback_result and playback_result[0]:
                    result['valid'] = True
                    result['error'] = None
                    result['resolution'], result['codec'], result['audio'] = playback_result
                    if result['resolution']:
                        res_str = str(result['resolution'])
                        res_parts = res_str.split('*')
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
            
            # 检查停止标志
            if self.stop_requested:
                return None
                
            if self.ffprobe_available and not self.skip_resolution:
                playback_result = _test_stream_playback(url, self.timeouts['ffprobe'])
                
                # 检查停止标志
                if self.stop_requested:
                    return None
                    
                if playback_result and playback_result[0]:
                    result['valid'] = True
                    result['error'] = None
                    result['resolution'], result['codec'], result['audio'] = playback_result
                    if result['resolution']:
                        res_str = str(result['resolution'])
                        res_parts = res_str.split('*')
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
                if isinstance(resolution_info, tuple) and len(resolution_info) >= 2:
                    result['resolution'], result['codec'], result['audio'] = resolution_info[0], resolution_info[1], resolution_info[2] if len(resolution_info) > 2 else None
                else:
                    result['resolution'], result['codec'], result['audio'] = resolution_info, None, None
                if result['resolution']:
                    res_str = str(result['resolution'])
                    res_parts = res_str.split('*')
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
        
        # 测速（对所有URL进行，measure_response_time会处理不同协议）
        try:
            speed_result = measure_response_time(url, timeout=5, retry=2)
            if speed_result and speed_result.get('response_time') and speed_result.get('response_time') < 10000:
                result['response_time'] = speed_result['response_time']
                # 测速成功说明频道有效，更新验证结果
                if not result.get('valid', False):
                    result['valid'] = True
                    result['error'] = None
        except Exception:
            pass
        
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
        
        # 方法3: 如果是M3U8文件且ffprobe失败，尝试基于内容的检测
        if url.endswith('.m3u8') or url.endswith('.m3u'):
            resolution = _get_resolution_from_m3u8_content(url, timeout)
            if resolution and resolution[0]:
                return resolution
        
        # 检查停止标志
        if self.stop_requested:
            return None
        
        # 方法4: 使用VLC检测（更强的协议支持）
        try:
            # 安全的VLC导入，支持模块化运行
            try:
                from .vlc_detector import detect_with_vlc
            except ImportError:
                from vlc_detector import detect_with_vlc
                
            resolution, codec, info = detect_with_vlc(url, timeout)
            if resolution:
                return resolution, codec, {**info, 'fallback_level': 4}
        except ImportError:
            pass
        except Exception as e:
            if self.debug:
                print(f"[调试] VLC检测失败: {e}")
        
        # 检查停止标志
        if self.stop_requested:
            return None
        
        # 方法5: 如果有MediaInfo作为备选
        if self.mediainfo_available:
            resolution = _mediainfo_get_resolution(url, timeout)
            if resolution:
                return resolution
        
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
        
        # 先发送所有频道的初始信息（用于显示在中间窗口）
        if progress_callback:
            for idx, channel in enumerate(self.channels):
                channel_info = {
                    'name': channel.get('name', '未知频道') or '未知频道',
                    'url': channel.get('url', '') or '',
                    'valid': None,
                    'resolution': '',
                    'response_time': None,
                    'error': '',
                    'status': '待验证',
                    'original_index': idx,
                    'display_index': idx + 1,
                    'category': channel.get('category', '')
                }
                progress_callback({
                    'progress': 5,
                    'total_channels': total_channels,
                    'processed': idx,
                    'message': f'正在加载频道列表: {channel_info["name"]}',
                    'stage': 'loading_channels',
                    'channel': channel_info
                })
                time.sleep(0.01)  # 短暂延迟，确保前端能处理
        
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
        
        print(f"[调试] 线程池创建完成，共提交 {len(self.channels)} 个频道任务")
        
        try:
            futures = []
            for idx, channel in enumerate(self.channels):
                if self.stop_requested:
                    break
                channel['original_index'] = idx
                future = self._validation_pool.submit(self._validate_url, channel)
                futures.append(future)
                self._active_futures.add(future)
            
            print(f"[调试] 所有任务已提交，开始收集结果...")
            
            # 收集结果并发送进度更新 - 优化结束阶段速度
            processed_count = 0
            last_progress_update = 0  # 减少进度更新频率
            
            for future in concurrent.futures.as_completed(futures):
                self._active_futures.discard(future)
                print(f"[调试] 收到一个结果，已处理 {processed_count + 1}/{len(futures)}")
                
                # 检查停止标志，如果已请求停止则立即退出
                if self.stop_requested:
                    print("[调试] 检测到停止请求，立即退出验证")
                    # 立即取消所有剩余的future
                    for remaining_future in futures:
                        if remaining_future not in self._active_futures:
                            continue
                        try:
                            remaining_future.cancel()
                            self._active_futures.discard(remaining_future)
                        except Exception:
                            pass
                    break
                    
                try:
                    result = future.result()
                    processed_count += 1
                    
                    if result:
                        # 性能优化：在验证过程中维护有序结果，避免后期排序
                        idx = result.get('original_index', 0)
                        self._original_order_results[idx] = result
                        
                        # 性能优化：即时分类，避免后期双重循环
                        if result['valid']:
                            category = result['category'] or '未分类'
                            self._categorized_results[category].append(result)
                    
                    # 每次验证完成都发送进度更新
                    current_progress = int(processed_count / total_channels * 80)
                    if True:  # 每次验证完成都更新
                        last_progress_update = current_progress
                        if progress_callback:
                            try:
                                # 创建简化的频道信息，避免发送复杂对象
                                channel_info = {
                                    'name': result.get('name', '') if result else '',
                                    'url': result.get('url', '') if result else '',
                                    'valid': result.get('valid', False) if result else False,
                                    'resolution': str(result.get('resolution', '')) if result and result.get('resolution') else '',
                                    'resolution_width': result.get('resolution_width') if result else None,
                                    'resolution_height': result.get('resolution_height') if result else None,
                                    'response_time': result.get('response_time') if result else None,
                                    'error': result.get('error', '') if result else '',
                                    'status': '有效' if result and result.get('valid') else '无效' if result else '未知',
                                    'original_index': result.get('original_index', 0) if result else 0
                                }
                                progress_callback({
                                    'progress': 10 + current_progress,
                                    'total_channels': total_channels,
                                    'processed': processed_count,
                                    'message': f'验证中: {channel_info.get("name", "未知频道")} - {channel_info.get("status", "")}',
                                    'stage': 'validation',
                                    'channel': channel_info
                                })
                            except Exception as callback_err:
                                print(f"[调试] 进度回调出错: {str(callback_err)}")
                except Exception as e:
                    print(f"[调试] 验证过程出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    processed_count += 1
                    # 错误情况下也减少进度更新频率
                    current_progress = int(processed_count / total_channels * 80)
                    if current_progress - last_progress_update >= 10:  # 错误时更新频率更低
                        last_progress_update = current_progress
                        if progress_callback:
                            progress_callback({
                                'progress': 10 + current_progress,
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
        
        # 性能优化：转换为有序列表而非排序
        self.all_results = [self._original_order_results[i] for i in sorted(self._original_order_results.keys())]
        
        # 发送验证完成进度
        if progress_callback:
            progress_callback({
                'progress': 100,
                'total_channels': total_channels,
                'processed': total_channels,
                'message': f'验证完成，有效频道: {sum(1 for r in self.all_results if r["valid"])}/{len(self.all_results)}',
                'stage': 'validation_completed'
            })
        
        # 添加性能监控信息
        print(f"验证完成，有效频道: {sum(1 for r in self.all_results if r['valid'])}/{len(self.all_results)}")
        print(f"分类统计: {dict(self._categorized_results)}")

    def _generate_m3u_output(self, valid_only=True, output_file=None):
        """生成M3U格式输出文件
        
        Args:
            valid_only: 如果为True，只保存有效频道；如果为False，保存所有频道（有效在前，无效在后）
            output_file: 指定输出文件路径，如果为None则使用默认路径
        """
        if output_file is None:
            output_file = self.output_file
            
        output_lines = ['#EXTM3U']
        
        # 分别处理有效和无效频道 - 从所有结果中分离，而不是从分类结果中分离
        valid_channels = []
        invalid_channels = []
        
        # 直接从all_results分离，保持分类逻辑性能
        for result in self.all_results:
            if result.get('valid', False):
                valid_channels.append(result)
            else:
                invalid_channels.append(result)
        
        if valid_only:
            # 只保存有效频道
            channels_to_save = valid_channels
            # 按分类组织频道
            categorized_channels = {}
            for channel in channels_to_save:
                category = channel.get('category', '未分类')
                if category not in categorized_channels:
                    categorized_channels[category] = []
                categorized_channels[category].append(channel)
            
            # 生成输出内容
            for category, channels in sorted(categorized_channels.items()):
                for channel in channels:
                    extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                    resolution = channel.get('resolution')
                    
                    # 检查分辨率是否有效（不是None且不是(None, None)）
                    if resolution and resolution != (None, None):
                        # 将元组格式化为字符串 "宽度x高度"
                        resolution_str = f"{resolution[0]}x{resolution[1]}"
                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str}]'
                    else:
                        extinf += f',{channel["name"]}'
                    output_lines.append(extinf)
                    output_lines.append(channel['url'])
        else:
            # 保存所有频道（有效在前，无效在后）
            
            # 先处理有效频道
            valid_categorized = {}
            for channel in valid_channels:
                category = channel.get('category', '未分类')
                if category not in valid_categorized:
                    valid_categorized[category] = []
                valid_categorized[category].append(channel)
            
            for category, channels in sorted(valid_categorized.items()):
                for channel in channels:
                    extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                    resolution = channel.get('resolution')
                    
                    # 检查分辨率是否有效（不是None且不是(None, None)）
                    if resolution and resolution != (None, None):
                        # 将元组格式化为字符串 "宽度x高度"
                        resolution_str = f"{resolution[0]}x{resolution[1]}"
                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str}]'
                    else:
                        extinf += f',{channel["name"]}'
                    output_lines.append(extinf)
                    output_lines.append(channel['url'])
            
            # 添加分界标记 - 增强版
            if invalid_channels:
                output_lines.append("")
                output_lines.append("#" + "=" * 50)
                output_lines.append(f"# === 无效频道开始 ({len(invalid_channels)} 个) ===")
                output_lines.append("#" + "=" * 50)
                output_lines.append("")
                
                # 再处理无效频道
                invalid_categorized = {}
                for channel in invalid_channels:
                    category = channel.get('category', '未分类')
                    if category not in invalid_categorized:
                        invalid_categorized[category] = []
                    invalid_categorized[category].append(channel)
                
                for category, channels in sorted(invalid_categorized.items()):
                    for channel in channels:
                        extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                        resolution = channel.get('resolution')
                        
                        # 检查分辨率是否有效（不是None且不是(None, None)）
                        if resolution and resolution != (None, None):
                            # 将元组格式化为字符串 "宽度x高度"
                            resolution_str = f"{resolution[0]}x{resolution[1]}"
                            extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str}]'
                        else:
                            extinf += f',{channel["name"]}'
                        output_lines.append(extinf)
                        output_lines.append(channel['url'])
        
        from file_utils import write_file_with_encoding
        write_file_with_encoding(output_file, '\n'.join(output_lines))
        
        print(f"M3U输出已保存到: {output_file}")

    def _generate_txt_output(self, valid_only=True, output_file=None):
        """生成TXT格式输出文件
        
        Args:
            valid_only: 如果为True，只保存有效频道；如果为False，保存所有频道（有效在前，无效在后）
            output_file: 指定输出文件路径，如果为None则使用默认路径
        """
        if output_file is None:
            output_file = self.output_file
            
        output_lines = []
        
        # 分别处理有效和无效频道 - 从所有结果中分离，而不是从分类结果中分离
        valid_channels = []
        invalid_channels = []
        
        # 直接从all_results分离，保持分类逻辑性能
        for result in self.all_results:
            if result.get('valid', False):
                valid_channels.append(result)
            else:
                invalid_channels.append(result)
        
        if valid_only:
            # 只保存有效频道
            channels_to_save = valid_channels
            # 按分类组织频道
            categorized_channels = {}
            for channel in channels_to_save:
                category = channel.get('category', '未分类')
                if category not in categorized_channels:
                    categorized_channels[category] = []
                categorized_channels[category].append(channel)
            
            # 生成输出内容
            for category, channels in sorted(categorized_channels.items()):
                output_lines.append(f"{category},#genre#")
                for channel in channels:
                    resolution = channel['resolution']
                    if resolution and resolution != (None, None):
                        output_lines.append(f'{channel["name"]}[{resolution}],{channel["url"]}')
                    else:
                        output_lines.append(f'{channel["name"]},{channel["url"]}')
                output_lines.append("")
        else:
            # 保存所有频道（有效在前，无效在后）
            
            # 先处理有效频道
            valid_categorized = {}
            for channel in valid_channels:
                category = channel.get('category', '未分类')
                if category not in valid_categorized:
                    valid_categorized[category] = []
                valid_categorized[category].append(channel)
            
            for category, channels in sorted(valid_categorized.items()):
                output_lines.append(f"{category},#genre#")
                for channel in channels:
                    resolution = channel['resolution']
                    if resolution and resolution != (None, None):
                        output_lines.append(f'{channel["name"]}[{resolution}],{channel["url"]}')
                    else:
                        output_lines.append(f'{channel["name"]},{channel["url"]}')
                output_lines.append("")
            
            # 添加分界标记 - 增强版
            if invalid_channels:
                output_lines.append("")
                output_lines.append("=" * 60)
                output_lines.append(f"=== 无效频道开始 ({len(invalid_channels)} 个) ===")
                output_lines.append("=" * 60)
                output_lines.append("")
                
                # 再处理无效频道
                invalid_categorized = {}
                for channel in invalid_channels:
                    category = channel.get('category', '未分类')
                    if category not in invalid_categorized:
                        invalid_categorized[category] = []
                    invalid_categorized[category].append(channel)
                
                for category, channels in sorted(invalid_categorized.items()):
                    output_lines.append(f"{category},#genre#")
                    for channel in channels:
                        resolution = channel['resolution']
                        if resolution and resolution != (None, None):
                            output_lines.append(f'{channel["name"]}[{resolution}],{channel["url"]}')
                        else:
                            output_lines.append(f'{channel["name"]},{channel["url"]}')
                    output_lines.append("")
        
        from file_utils import write_file_with_encoding
        write_file_with_encoding(output_file, '\n'.join(output_lines))
        
        print(f"TXT输出已保存到: {output_file}")

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
            from file_utils import read_json_with_encoding
            data = read_json_with_encoding(self.input_file)
            
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
                'progress': 100,
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
        # 性能优化：返回预分类结果
        return dict(self._categorized_results)


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
    # 加载配置
    try:
        config_manager = get_config_manager()
        validation_config = config_manager.get_validation_config()
    except Exception:
        validation_config = {}
    
    # 使用配置中的默认值，如果用户没有提供参数
    if timeout == 5 and validation_config.get('default_timeout'):
        timeout = validation_config.get('default_timeout')
    
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
            for res, count in sorted(summary['resolution_stats'].items(), key=lambda x: int(str(x[0]).split('*')[1]) if '*' in str(x[0]) else 0, reverse=True):
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
