#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直播源有效性验证工具 - 整合版 (改进版)
功能：整合多个窗口功能为单一EXE应用程序
特点：包含文件选择、验证设置、进度显示、结果展示等所有功能
改进：融合iptv_validator.py的强大检测方法

检测方法升级：
1. 多协议支持 (HTTP, HTTPS, RTSP, RTMP, UDP, RTP)
2. 完善的HTTP请求处理 (HEAD/GET重试机制)
3. IPv6地址支持
4. 网络代理支持
5. 音频检测功能
6. VLC检测支持
7. 更好的错误处理和超时控制
8. 分辨率检测增强
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import copy
import json
import tempfile
import logging
import subprocess
import re
import requests
from datetime import datetime
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入核心验证模块
try:
    # 从当前目录导入，因为current_dir已经是validator目录
    from iptv_validator import IPTVValidator, validate_ipTV
    from vlc_detector import VLCStreamDetectorV2
    
    # 导入quick_url_checker（需要添加父目录到路径）
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    from quick_url_checker import QuickURLChecker, create_quick_checker
    QUICK_CHECKER_AVAILABLE = True
except ImportError as e:
    print(f"导入警告: {e}")
    QUICK_CHECKER_AVAILABLE = False


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
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(measure_response_time, url, timeout): url for url in urls}
        
        for future in as_completed(future_to_url):
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


class EnhancedValidationEngine:
    """增强的验证引擎 - 融合iptv_validator.py的强大检测方法"""
    
    def __init__(self, config):
        self.config = config
        self.stop_requested = False
        self.ffprobe_available = self._check_ffprobe_available()
        self.vlc_detector = VLCStreamDetectorV2() if config.get('enable_vlc', False) else None
        self.quick_checker = create_quick_checker() if config.get('enable_quick_check', True) and QUICK_CHECKER_AVAILABLE else None
        
        # 网络条件监控
        self.network_stats = {
            'response_times': [],
            'success_count': 0,
            'timeout_count': 0,
            'error_count': 0,
            'total_requests': 0
        }
        self.max_response_time_samples = 50  # 保留最近50个响应时间样本
        
        # 智能超时配置
        self.enable_smart_timeout = config.get('enable_smart_timeout', True)
        self.smart_timeout_sensitivity = config.get('smart_timeout_sensitivity', 1.0)  # 灵敏度系数，值越大调整越剧烈
        
        # 基础超时配置 - 来自iptv_validator.py的最佳实践
        self.base_timeouts = {
            'http_head': 3,
            'http_get': config.get('timeout', 5),
            'vlc_check': 8,
            'resolution_check': 10,
            'socket_connect': 2
        }
        
        # 当前超时配置（初始化为基础超时）
        self.timeouts = self.base_timeouts.copy()
        
        # 超时边界限制
        self.timeout_bounds = {
            'min': 1,  # 最小超时1秒
            'max': 30  # 最大超时30秒
        }
        
        # HTTP会话配置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        
    def _check_ffprobe_available(self):
        """检查ffprobe是否可用"""
        try:
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, 
                                  timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
    
    def update_network_stats(self, response_time, success):
        """更新网络状态统计信息"""
        self.network_stats['total_requests'] += 1
        
        if response_time and response_time > 0:
            self.network_stats['response_times'].append(response_time)
            # 只保留最近的响应时间样本
            if len(self.network_stats['response_times']) > self.max_response_time_samples:
                self.network_stats['response_times'].pop(0)
        
        if success:
            self.network_stats['success_count'] += 1
        else:
            self.network_stats['error_count'] += 1
            if 'timeout' in str(success).lower():
                self.network_stats['timeout_count'] += 1
        
        # 根据网络状态调整超时时间
        self.adjust_timeouts()
    
    def adjust_timeouts(self):
        """根据网络状态动态调整超时时间"""
        if not self.enable_smart_timeout or not self.network_stats['response_times']:
            return
        
        # 计算平均响应时间和超时率
        avg_response_time = sum(self.network_stats['response_times']) / len(self.network_stats['response_times'])
        timeout_rate = self.network_stats['timeout_count'] / self.network_stats['total_requests'] if self.network_stats['total_requests'] > 0 else 0
        success_rate = self.network_stats['success_count'] / self.network_stats['total_requests'] if self.network_stats['total_requests'] > 0 else 0
        
        # 计算调整系数
        # 如果超时率高，增加超时时间
        # 如果成功响应快，减少超时时间
        adjustment_factor = 1.0
        
        if timeout_rate > 0.3:
            # 超时率高，增加超时时间
            adjustment_factor = 1.0 + (timeout_rate - 0.3) * 2 * self.smart_timeout_sensitivity
        elif success_rate > 0.8 and avg_response_time < self.base_timeouts['http_get'] * 0.5:
            # 成功响应快，减少超时时间
            adjustment_factor = 0.8 - (self.base_timeouts['http_get'] * 0.5 - avg_response_time) / self.base_timeouts['http_get'] * self.smart_timeout_sensitivity
        
        # 应用调整系数到所有超时类型
        for timeout_type in self.timeouts:
            new_timeout = self.base_timeouts[timeout_type] * adjustment_factor
            # 确保超时在合理范围内
            new_timeout = max(self.timeout_bounds['min'], min(self.timeout_bounds['max'], new_timeout))
            # 只在变化显著时更新
            if abs(new_timeout - self.timeouts[timeout_type]) > 0.5:
                self.timeouts[timeout_type] = round(new_timeout, 1)
    
    def _http_request_with_retry(self, url, method='head', timeout=None, headers=None, retry=2):
        """HTTP请求重试机制 - 来自iptv_validator.py，添加智能超时支持"""
        if timeout is None:
            timeout = self.timeouts['http_head'] if method == 'head' else self.timeouts['http_get']
        
        # 检测IPv6地址格式
        is_ipv6 = '[' in url and ']' in url
        
        # IPv6地址跳过HTTP请求，初步标记为有效
        if is_ipv6:
            return {'status': 'ipv6', 'valid': True}
        
        # 跳过UDP代理URL
        if '/udp/' in url.lower() or '/rtp/' in url.lower() or '/rtmp/' in url.lower():
            return {'status': 'proxy', 'valid': True}
        
        for attempt in range(retry + 1):
            if self.stop_requested:
                return None
                
            start_time = time.time()
            
            try:
                # 对特定域名禁用SSL验证
                verify_ssl = True
                if '60.191.56.186' in url:
                    verify_ssl = False
                
                if method == 'head':
                    response = self.session.head(url, timeout=timeout, allow_redirects=True, headers=headers, verify=verify_ssl)
                else:
                    response = self.session.get(url, timeout=timeout, allow_redirects=True, headers=headers, verify=verify_ssl)
                    
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 对特定域名采取更宽松的验证策略
                relaxed_domains = ['go.bkpcp.top', '60.191.56.186']
                domain_match = any(domain in url for domain in relaxed_domains)
                
                if response.status_code < 400:
                    self.update_network_stats(response_time, True)
                    return {'status': 'success', 'valid': True, 'status_code': response.status_code, 'response_time': response_time}
                elif domain_match:
                    # 对于特定域名，即使返回403等状态码，也标记为有效
                    self.update_network_stats(response_time, True)
                    return {'status': 'domain_relaxed', 'valid': True, 'status_code': response.status_code, 'response_time': response_time}
                    
            except requests.exceptions.Timeout:
                response_time = timeout * 1000  # 超时，使用请求的超时时间作为响应时间
                if attempt == retry:
                    self.update_network_stats(response_time, 'timeout')
                    return {'status': 'timeout', 'valid': False, 'error': '请求超时', 'response_time': response_time}
            except requests.exceptions.ConnectionError:
                response_time = timeout * 1000
                if attempt == retry:
                    self.update_network_stats(response_time, False)
                    return {'status': 'connection_error', 'valid': False, 'error': '连接错误', 'response_time': response_time}
            except Exception as e:
                response_time = timeout * 1000
                if attempt == retry:
                    self.update_network_stats(response_time, False)
                    return {'status': 'error', 'valid': False, 'error': str(e), 'response_time': response_time}
                    
        return None
    
    def _check_socket_connection(self, host, port, timeout_sec=2):
        """检查socket连接 - 来自iptv_validator.py"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_sec)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _extract_resolution_from_url(self, url):
        """从URL中提取分辨率信息"""
        try:
            # 分辨率标注提取： [1920*1080]
            re_resolution = re.compile(r'\[(\d+\*\d+)\]')
            match = re_resolution.search(url)
            if match:
                resolution_str = match.group(1)
                parts = resolution_str.split('*')
                if len(parts) == 2:
                    width, height = parts[0], parts[1]
                    if self._is_valid_resolution(width, height):
                        return resolution_str
            
            # URL参数中的分辨率：$1920x1080
            re_dollar = re.compile(r'\$(\d+)x(\d+)')
            match = re_dollar.search(url)
            if match:
                width, height = match.group(1), match.group(2)
                if self._is_valid_resolution(width, height):
                    return f"{width}*{height}"
            
            # URL参数：?resolution=1920x1080
            re_param = re.compile(r'[?&]resolution=(\d+)[x*](\d+)', re.IGNORECASE)
            match = re_param.search(url)
            if match:
                width, height = match.group(1), match.group(2)
                if self._is_valid_resolution(width, height):
                    return f"{width}*{height}"
                    
            return None
        except Exception:
            return None
    
    def _is_valid_resolution(self, width, height):
        """验证分辨率是否有效"""
        try:
            w, h = int(width), int(height)
            
            # 检查基本有效性
            if not (w >= 320 and w <= 7680 and 
                    h >= 240 and h <= 4320 and
                    w > 0 and h > 0 and
                    0.5 <= w/h <= 4.0):
                return False
            
            # 检查最小分辨率限制
            min_width = self.config.get('resolution_min_width')
            min_height = self.config.get('resolution_min_height')
            
            if min_width is not None and w < min_width:
                return False
                
            if min_height is not None and h < min_height:
                return False
                
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_resolution_from_hls(self, url, timeout, headers=None):
        """从HLS播放列表中提取分辨率信息"""
        try:
            response = self.session.get(url, timeout=min(timeout, 15), headers=headers, allow_redirects=True)
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
        except Exception:
            return None, None, {}
    
    def _ffprobe_get_resolution(self, url, timeout, headers=None):
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
                        codec = stream.get('codec_name', 'hls')
                        if codec in ('Unknown', 'unknown', '未知'):
                            codec = 'hls'
                        if width and height and width > 0 and height > 0:
                            return f"{width}*{height}", codec, {'source': 'ffprobe'}
                except json.JSONDecodeError:
                    pass

            return None, None, {}
        except Exception:
            return None, None, {}
    
    def _check_url_has_audio(self, url, timeout, headers=None):
        """检查URL是否有音频 - 来自iptv_validator.py"""
        if not self.ffprobe_available:
            return True  # 如果无法检测，假设有音频
        
        try:
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
                '-select_streams', 'a',
                '-show_entries', 'stream=codec_name',
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
                    return 'streams' in data and len(data['streams']) > 0
                except json.JSONDecodeError:
                    pass

            return True  # 默认假设有音频
        except Exception:
            return True
    
    def validate_single_url(self, channel):
        """验证单个URL - 融合iptv_validator.py的强大检测逻辑"""
        if self.stop_requested:
            return None
            
        name = channel.get('name', '未知频道')
        url = channel.get('url', '')
        category = channel.get('category', '未分类')
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
            'error': None,
            'validation_method': 'basic',
            'response_time': None
        }
        
        # 检查URL协议支持
        if not (url.startswith(('http://', 'https://', 'rtsp://', 'rtmp://', 'udp://', 'rtp://'))):
            result['error'] = '不支持的URL协议'
            return result
        
        # HTTP(S) URL验证
        if url.startswith(('http://', 'https://')):
            # 对特定域名采取更宽松的验证策略
            relaxed_domains = ['go.bkpcp.top']
            domain_match = any(domain in url for domain in relaxed_domains)
            
            # 首先尝试HEAD请求
            response = self._http_request_with_retry(url, method='head')
            
            if not response or not response.get('valid'):
                # HEAD失败，尝试GET请求
                response = self._http_request_with_retry(url, method='get')
            
            if response:
                if response.get('status') == 'ipv6':
                    result['valid'] = True
                    result['validation_method'] = 'ipv6'
                elif response.get('status') == 'proxy':
                    result['valid'] = True
                    result['validation_method'] = 'proxy'
                elif response.get('valid'):
                    result['valid'] = True
                    result['validation_method'] = 'http'
                elif domain_match and response.get('error') == 'HTTP请求失败':
                    # 对于特定域名，即使HTTP请求返回403等错误，也尝试使用ffprobe检测
                    result['valid'] = True
                    result['validation_method'] = 'domain_relaxed'
                else:
                    result['error'] = response.get('error', 'HTTP请求失败')
                    return result
            elif domain_match:
                # 对于特定域名，即使HTTP请求失败，也尝试使用ffprobe检测
                result['valid'] = True
                result['validation_method'] = 'domain_relaxed'
            else:
                result['error'] = 'HTTP请求失败'
                return result
        
        # 其他协议的基本验证
        elif url.startswith(('rtsp://', 'rtmp://', 'udp://', 'rtp://')):
            result['valid'] = True
            result['validation_method'] = 'protocol'
        
        # 测速（仅对HTTP/HTTPS有效源进行）
        if result['valid'] and url.startswith(('http://', 'https://')):
            try:
                speed_result = measure_response_time(url, timeout=3, retry=1)
                if speed_result and speed_result.get('valid') and speed_result.get('response_time'):
                    result['response_time'] = speed_result['response_time']
            except Exception:
                pass
        
        # 分辨率检测
        if result['valid'] and self.config.get('enable_resolution_detection', True):
            try:
                # 从URL提取分辨率
                url_resolution = self._extract_resolution_from_url(url)
                if url_resolution:
                    width, height = url_resolution
                    result['resolution'] = f"{width}*{height}"
                    result['resolution_width'] = int(width)
                    result['resolution_height'] = int(height)
                else:
                    # HLS播放列表检测
                    if url.lower().endswith(('.m3u8', '.m3u')) or '/hls/' in url.lower():
                        resolution = self._get_resolution_from_hls(url, self.timeouts['resolution_check'])
                        if resolution and resolution[0]:
                            result['resolution'] = resolution[0]
                            result['codec'] = resolution[1]
                            width, height = str(resolution[0]).split('*')
                            result['resolution_width'] = int(width)
                            result['resolution_height'] = int(height)
                    
                    # ffprobe检测
                    if not result['resolution'] and self.ffprobe_available:
                        resolution = self._ffprobe_get_resolution(url, self.timeouts['resolution_check'])
                        if resolution and resolution[0]:
                            result['resolution'] = resolution[0]
                            result['codec'] = resolution[1]
                            width, height = str(resolution[0]).split('*')
                            result['resolution_width'] = int(width)
                            result['resolution_height'] = int(height)
            except Exception:
                pass
        
        # 音频检测
        if result['valid'] and self.config.get('enable_audio_check', True):
            try:
                result['audio'] = self._check_url_has_audio(url, self.timeouts['resolution_check'])
            except Exception:
                result['audio'] = True  # 默认假设有音频
        
        # VLC检测（如果启用）
        if result['valid'] and self.vlc_detector and self.config.get('enable_vlc', True):
            try:
                vlc_result = self.vlc_detector.check_stream(url, timeout=self.timeouts['vlc_check'])
                result['vlc_valid'] = vlc_result.get('valid', False)
                if not result['vlc_valid']:
                    result['error'] = 'VLC检测失败'
                    result['valid'] = False
            except Exception:
                pass
        
        # 分辨率筛选
        if result['valid'] and result['resolution_width'] and result['resolution_height']:
            min_width = self.config.get('resolution_min_width')
            min_height = self.config.get('resolution_min_height')
            
            if min_width is not None and result['resolution_width'] < min_width:
                result['valid'] = False
                result['error'] = f'分辨率宽度不足（{result["resolution_width"]} < {min_width}）'
            elif min_height is not None and result['resolution_height'] < min_height:
                result['valid'] = False
                result['error'] = f'分辨率高度不足（{result["resolution_height"]} < {min_height}）'
        
        return result

class EnhancedIntegratedValidatorApp:
    """增强的整合版直播源验证器应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("直播源有效性验证工具 - 整合版 v3.0 (增强检测)")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 验证状态
        self.is_validating = False
        self.validation_thread = None
        self.cancel_validation = False
        
        # 结果数据
        self.validation_results = []
        self.valid_channels = {}
        self.invalid_channels = {}
        self.original_channels = {}
        
        # 用于跟踪已处理的URL
        self.seen_urls = set()
        
        # 配置参数 - 优化性能设置，与Web界面保持一致
        self.config = {
            'timeout': 3,  # 优化：从5秒降低到3秒，提升验证速度
            'workers': 30,
            'enable_vlc': False,  # 保持默认关闭，提升速度
            'enable_quick_check': True,
            'enable_resolution_detection': True,
            'enable_audio_check': False,  # 优化：默认关闭音频检测以提升速度
            'batch_threshold': 50,
            'enable_smart_timeout': True,  # 启用智能超时机制
            'smart_timeout_sensitivity': 1.0  # 智能超时灵敏度系数
        }
        
        self.validation_engine = None
        self.setup_ui()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_validator.log', encoding='utf-8'),
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
        format_label = ttk.Label(file_frame, text="支持格式: M3U, M3U8, TXT | 改进检测: 多协议支持、IPv6、音频检测", foreground="gray")
        format_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 验证设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="验证设置 (增强版)", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # 第一行：超时和并发数
        ttk.Label(settings_frame, text="超时时间(秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.timeout_var = tk.IntVar(value=3)  # 优化：界面默认值与配置保持一致
        timeout_spinbox = ttk.Spinbox(settings_frame, from_=1, to=30, textvariable=self.timeout_var, width=10)
        timeout_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="并发数:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.workers_var = tk.IntVar(value=30)
        workers_spinbox = ttk.Spinbox(settings_frame, from_=1, to=100, textvariable=self.workers_var, width=10)
        workers_spinbox.grid(row=0, column=3, sticky=tk.W)
        
        # 第二行：检测选项
        options_frame = ttk.Frame(settings_frame)
        options_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.enable_vlc_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="启用VLC检测", variable=self.enable_vlc_var).pack(side=tk.LEFT, padx=(0, 15))
        
        self.enable_quick_check_var = tk.BooleanVar(value=True)
        self.quick_check_button = ttk.Checkbutton(options_frame, text="启用快速检测", variable=self.enable_quick_check_var)
        self.quick_check_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.enable_resolution_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="启用分辨率检测", variable=self.enable_resolution_var).pack(side=tk.LEFT, padx=(0, 15))
        
        self.enable_audio_var = tk.BooleanVar(value=False)  # 优化：默认不启用音频检测以提升速度
        ttk.Checkbutton(options_frame, text="启用音频检测", variable=self.enable_audio_var).pack(side=tk.LEFT, padx=(0, 15))
        
        if not QUICK_CHECKER_AVAILABLE:
            self.enable_quick_check_var.set(False)
            # 禁用Checkbutton控件，而不是BooleanVar
            self.quick_check_button.config(state="disabled")
        
        # 第三行：分辨率筛选
        resolution_filter_frame = ttk.Frame(settings_frame)
        resolution_filter_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(resolution_filter_frame, text="最小分辨率: ").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(resolution_filter_frame, text="宽: ").pack(side=tk.LEFT, padx=(0, 5))
        self.min_width_var = tk.StringVar(value="1280")
        self.min_width_entry = ttk.Entry(resolution_filter_frame, textvariable=self.min_width_var, width=8)
        self.min_width_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(resolution_filter_frame, text="高: ").pack(side=tk.LEFT, padx=(0, 5))
        self.min_height_var = tk.StringVar(value="720")
        self.min_height_entry = ttk.Entry(resolution_filter_frame, textvariable=self.min_height_var, width=8)
        self.min_height_entry.pack(side=tk.LEFT)
        
        # 检测能力状态显示
        capabilities_frame = ttk.Frame(settings_frame)
        capabilities_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.ffprobe_status_var = tk.StringVar(value="检查ffprobe状态...")
        ttk.Label(capabilities_frame, textvariable=self.ffprobe_status_var, foreground="blue").pack(side=tk.LEFT)
        
        # 智能超时设置
        smart_timeout_frame = ttk.Frame(settings_frame)
        smart_timeout_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.enable_smart_timeout_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(smart_timeout_frame, text="启用智能超时机制", variable=self.enable_smart_timeout_var).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(smart_timeout_frame, text="灵敏度: ").pack(side=tk.LEFT, padx=(0, 5))
        self.smart_timeout_sensitivity_var = tk.DoubleVar(value=1.0)
        sensitivity_scale = ttk.Scale(smart_timeout_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, 
                                     variable=self.smart_timeout_sensitivity_var, length=200)
        sensitivity_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.sensitivity_value_var = tk.StringVar(value="1.0")
        ttk.Label(smart_timeout_frame, textvariable=self.sensitivity_value_var, width=5).pack(side=tk.LEFT)
        
        # 更新灵敏度显示值
        def update_sensitivity_value(*args):
            value = round(self.smart_timeout_sensitivity_var.get(), 1)
            self.sensitivity_value_var.set(f"{value}")
        
        self.smart_timeout_sensitivity_var.trace_add("write", update_sensitivity_value)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="开始验证", command=self.start_validation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止验证", command=self.stop_validation, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存模式选择
        save_mode_frame = ttk.Frame(control_frame)
        save_mode_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(save_mode_frame, text="保存模式:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.save_mode_var = tk.StringVar(value="保存全部")  # 默认保存全部
        save_mode_combo = ttk.Combobox(save_mode_frame, textvariable=self.save_mode_var, 
                                       values=["只保存有效", "保存全部"], 
                                       state="readonly", width=12)
        save_mode_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(control_frame, text="保存结果", command=self.save_results)
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="使用说明", command=self.show_help).pack(side=tk.LEFT, padx=(20, 0))
        
        # 进度显示区域
        progress_frame = ttk.LabelFrame(main_frame, text="验证进度", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 当前检测频道显示
        self.current_channel_var = tk.StringVar(value="准备验证...")
        ttk.Label(progress_frame, textvariable=self.current_channel_var, 
                 font=('Consolas', 9), foreground='blue').grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # 统计信息
        self.stats_var = tk.StringVar(value="总频道: 0 | 有效: 0 | 无效: 0 | 检测方法: 基础")
        ttk.Label(progress_frame, textvariable=self.stats_var).grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # 结果显示区域
        results_frame = ttk.LabelFrame(main_frame, text="验证结果", padding="10")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 创建Notebook用于切换结果视图
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 实时结果标签页（类似Web版表格）
        self.realtime_frame = ttk.Frame(self.results_notebook, padding="5")
        self.results_notebook.add(self.realtime_frame, text="实时结果")
        
        # 创建Treeview表格（带序号）
        columns = ('index', 'name', 'url', 'valid', 'width', 'height', 'speed')
        self.realtime_tree = ttk.Treeview(self.realtime_frame, columns=columns, show='headings', height=20)
        self.realtime_row_count = 0
        
        self.realtime_tree.heading('index', text='序号', anchor='center')
        self.realtime_tree.heading('name', text='频道名称', anchor='w')
        self.realtime_tree.heading('url', text='播放地址', anchor='w')
        self.realtime_tree.heading('valid', text='有效性', anchor='center')
        self.realtime_tree.heading('width', text='视频宽', anchor='center')
        self.realtime_tree.heading('height', text='视频高', anchor='center')
        self.realtime_tree.heading('speed', text='响应速度', anchor='center')
        
        self.realtime_tree.column('index', width=36, minwidth=30, anchor='center')  # 序号 - 3个汉字宽度，居中显示
        self.realtime_tree.column('name', width=72, minwidth=60, anchor='w')  # 频道名称 - 6个汉字宽度
        self.realtime_tree.column('url', width=300, minwidth=200, anchor='w')
        self.realtime_tree.column('valid', width=36, minwidth=30, anchor='center')    # 有效性 - 3个汉字宽度，居中显示
        self.realtime_tree.column('width', width=36, minwidth=30, anchor='center')    # 视频宽 - 3个汉字宽度，居中显示
        self.realtime_tree.column('height', width=36, minwidth=30, anchor='center')   # 视频高 - 3个汉字宽度，居中显示
        self.realtime_tree.column('speed', width=48, minwidth=40, anchor='center')    # 响应速度 - 4个汉字宽度，居中显示
        
        # 滚动条
        tree_scroll = ttk.Scrollbar(self.realtime_frame, orient=tk.VERTICAL, command=self.realtime_tree.yview)
        self.realtime_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.realtime_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定点击事件用于复制URL
        self.realtime_tree.bind('<ButtonRelease-1>', self.on_tree_click)
        
        # 有效结果标签页
        self.valid_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.valid_text, text="有效频道")
        
        # 无效结果标签页
        self.invalid_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.invalid_text, text="无效频道")
        
        # 详细信息标签页
        self.detail_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.detail_text, text="详细信息")
        
        # 日志显示标签页
        self.log_text = scrolledtext.ScrolledText(self.results_notebook, height=15, state="disabled")
        self.results_notebook.add(self.log_text, text="运行日志")
        
        # 初始化检测能力状态
        self.update_capabilities_status()
        
    def update_capabilities_status(self):
        """更新检测能力状态"""
        if hasattr(self, 'ffprobe_status_var'):
            try:
                result = subprocess.run(['ffprobe', '-version'], 
                                      capture_output=True, text=True, 
                                      timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if result.returncode == 0:
                    self.ffprobe_status_var.set("✓ ffprobe可用 - 分辨率/音频检测增强")
                else:
                    self.ffprobe_status_var.set("✗ ffprobe不可用 - 分辨率检测将受限")
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                self.ffprobe_status_var.set("✗ ffprobe不可用 - 分辨率检测将受限")
    
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
            
    def load_channels_from_file(self, file_path):
        """从文件加载频道列表"""
        channels = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if file_path.lower().endswith(('.m3u', '.m3u8')):
                # M3U格式解析
                lines = content.splitlines()
                current_category = "未分类"
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        if line.startswith('#EXTINF:'):
                            # 解析频道信息
                            match = re.search(r'tvg-name="([^"]*)".*?group-title="([^"]*)"', line)
                            if match:
                                current_category = match.group(2)
                        continue
                        
                    if line.startswith('http://') or line.startswith('https://'):
                        # 查找前一个EXTINF行获取频道名
                        channel_name = "未知频道"
                        if i > 0:
                            prev_line = lines[i-1].strip()
                            if prev_line.startswith('#EXTINF:'):
                                name_match = re.search(r'tvg-name="([^"]*)"', prev_line)
                                if name_match:
                                    channel_name = name_match.group(1)
                                else:
                                    # 尝试从EXTINF行末尾获取名称
                                    parts = prev_line.split(',')
                                    if len(parts) > 1:
                                        channel_name = parts[-1].strip()
                        
                        channels.append({
                            'name': channel_name,
                            'url': line,
                            'category': current_category,
                            'original_index': len(channels)
                        })
            
            else:
                # TXT格式解析 - 正确实现频道识别逻辑
                lines = content.splitlines()
                current_category = "未分类"
                
                # 频道识别正则表达式
                re_category = re.compile(r'^(.+),#?genre#$')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 跳过注释行（在分类识别之前）
                    if line.startswith('//'):
                        continue
                    
                    # 检查是否为分类行（优先于其他检查）
                    # 支持格式: <name>,#genre# (正确) 和 <name>,genre# (错误但兼容)
                    match = re_category.match(line)
                    if match:
                        current_category = match.group(1).strip().replace('\n', '')
                        continue
                    
                    # 检查是否为频道行
                    if ',' in line:
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            channel_name = parts[0].strip()
                            url = parts[1].strip()
                            if url and (url.startswith('http://') or url.startswith('https://')):
                                channels.append({
                                    'name': channel_name,
                                    'url': url,
                                    'category': current_category,
                                    'original_index': len(channels)
                                })
                    elif '\t' in line:
                        parts = line.split('\t', 1)
                        if len(parts) == 2:
                            channel_name = parts[0].strip()
                            url = parts[1].strip()
                            if url and (url.startswith('http://') or url.startswith('https://')):
                                channels.append({
                                    'name': channel_name,
                                    'url': url,
                                    'category': current_category,
                                    'original_index': len(channels)
                                })
                        
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            raise
            
        return channels
    
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
        self.config['enable_audio_check'] = self.enable_audio_var.get()
        # 分辨率筛选参数
        self.config['resolution_min_width'] = int(self.min_width_var.get()) if self.min_width_var.get() else None
        self.config['resolution_min_height'] = int(self.min_height_var.get()) if self.min_height_var.get() else None
        # 智能超时参数
        self.config['enable_smart_timeout'] = self.enable_smart_timeout_var.get()
        self.config['smart_timeout_sensitivity'] = self.smart_timeout_sensitivity_var.get()
        
        # 重置状态
        self.cancel_validation = False
        self.validation_results = []
        self.valid_channels = {}
        self.invalid_channels = {}
        self.original_channels = {}
        self.seen_urls = set()
        
        # 清空实时结果表格
        self.clear_realtime_display()
        
        # 切换到实时结果标签页
        self.results_notebook.select(self.realtime_frame)
        
        # 更新UI状态
        self.is_validating = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.save_button.config(state="disabled")
        self.progress_var.set("准备验证...")
        self.progress_bar.config(value=0)
        
        # 加载频道列表
        try:
            channels = self.load_channels_from_file(file_path)
            if not channels:
                messagebox.showwarning("警告", "文件中未找到有效的频道")
                self.reset_ui_state()
                return
                
            self.logger.info(f"加载了 {len(channels)} 个频道")
            
            # 创建验证引擎
            self.validation_engine = EnhancedValidationEngine(self.config)
            
            # 启动验证线程
            self.validation_thread = threading.Thread(
                target=self.run_validation, 
                args=(channels,),
                daemon=True
            )
            self.validation_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {e}")
            self.reset_ui_state()
    
    def run_validation(self, channels):
        """运行验证"""
        try:
            total_channels = len(channels)
            processed = 0
            valid_count = 0
            invalid_count = 0
            
            # 使用线程池进行并发验证
            with ThreadPoolExecutor(max_workers=self.config['workers']) as executor:
                # 提交所有验证任务
                future_to_channel = {
                    executor.submit(self.validation_engine.validate_single_url, channel): channel 
                    for channel in channels
                }
                
                # 处理完成的验证
                for future in as_completed(future_to_channel):
                    if self.cancel_validation:
                        break
                        
                    try:
                        result = future.result()
                        if result:
                            self.validation_results.append(result)
                            
                            if result['valid']:
                                valid_count += 1
                                category = result['category']
                                if category not in self.valid_channels:
                                    self.valid_channels[category] = []
                                self.valid_channels[category].append(result)
                            else:
                                invalid_count += 1
                                category = result['category']
                                if category not in self.invalid_channels:
                                    self.invalid_channels[category] = []
                                self.invalid_channels[category].append(result)
                            
                            processed += 1
                            
                            # 更新UI - 传递当前检测的频道信息
                            progress = int((processed / total_channels) * 100)
                            self.root.after(0, self.update_progress, 
                                          processed, total_channels, valid_count, invalid_count, progress, result)
                            
                    except Exception as e:
                        self.logger.error(f"验证单个频道时出错: {e}")
                        processed += 1
            
            # 验证完成
            self.root.after(0, self.validation_completed, valid_count, invalid_count)
            
        except Exception as e:
            self.logger.error(f"验证过程出错: {e}")
            self.root.after(0, self.validation_error, str(e))
    
    def update_progress(self, processed, total, valid, invalid, progress, current_channel=None):
        """更新进度显示 - 类似Web版本的实时显示"""
        # 显示当前正在检测的频道
        if current_channel:
            channel_info = f"正在检测: {current_channel.get('name', 'Unknown')} | {current_channel.get('url', 'Unknown URL')}"
            if current_channel.get('resolution'):
                channel_info += f" | 分辨率: {current_channel['resolution']}"
            self.current_channel_var.set(channel_info)
        else:
            self.current_channel_var.set("准备验证...")
            
        self.progress_var.set(f"验证中... {processed}/{total} ({progress}%)")
        self.progress_bar.config(value=progress)
        
        detection_method = "增强检测"
        if self.validation_engine:
            if self.validation_engine.ffprobe_available:
                detection_method += "+ffprobe"
            if self.config.get('enable_audio_check'):
                detection_method += "+音频"
            if self.config.get('enable_vlc'):
                detection_method += "+VLC"
        
        self.stats_var.set(f"总频道: {total} | 有效: {valid} | 无效: {invalid} | 检测方法: {detection_method}")
        
        # 实时更新Treeview表格
        if current_channel:
            self.update_realtime_display(current_channel)
        
        # 更新其他结果视图
        self.update_results_display()
    
    def validation_completed(self, valid_count, invalid_count):
        """验证完成"""
        self.is_validating = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.save_button.config(state="normal")
        
        total = len(self.validation_results)
        self.progress_var.set(f"验证完成! 总计: {total}, 有效: {valid_count}, 无效: {invalid_count}")
        self.progress_bar.config(value=100)
        
        # 最终更新结果显示
        self.update_results_display()
        
        messagebox.showinfo("验证完成", 
                          f"验证完成!\n总计: {total} 个频道\n有效: {valid_count} 个\n无效: {invalid_count} 个")
    
    def validation_error(self, error_msg):
        """验证出错"""
        self.is_validating = False
        self.reset_ui_state()
        messagebox.showerror("验证错误", f"验证过程中出现错误:\n{error_msg}")
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.is_validating = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.save_button.config(state="normal")
        self.progress_var.set("就绪")
        self.progress_bar.config(value=0)
        self.stats_var.set("总频道: 0 | 有效: 0 | 无效: 0")
    
    def stop_validation(self):
        """停止验证"""
        if self.validation_engine:
            self.validation_engine.stop_requested = True
        self.cancel_validation = True
        self.progress_var.set("正在停止...")
        
    def update_results_display(self):
        """更新结果显示"""
        # 清除现有内容
        self.valid_text.config(state="normal")
        self.valid_text.delete(1.0, tk.END)
        self.valid_text.config(state="disabled")
        
        self.invalid_text.config(state="normal")
        self.invalid_text.delete(1.0, tk.END)
        self.invalid_text.config(state="disabled")
        
        self.detail_text.config(state="normal")
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state="disabled")
        
        # 显示有效频道
        valid_output = []
        for category, channels in self.valid_channels.items():
            valid_output.append(f"\n=== {category} ({len(channels)} 个) ===")
            for channel in channels:
                line = f"{channel['name']} | {channel['url']}"
                if channel.get('resolution'):
                    line += f" | 分辨率: {channel['resolution']}"
                if channel.get('codec'):
                    line += f" | 编码: {channel['codec']}"
                if channel.get('audio') is not None:
                    audio_status = "有音频" if channel['audio'] else "无音频"
                    line += f" | 音频: {audio_status}"
                if channel.get('validation_method'):
                    line += f" | 检测: {channel['validation_method']}"
                if channel.get('response_time') is not None:
                    line += f" | 响应速度: {channel['response_time']}ms"
                valid_output.append(line)
        
        if valid_output:
            self.valid_text.config(state="normal")
            self.valid_text.insert(1.0, '\n'.join(valid_output))
            self.valid_text.config(state="disabled")
        
        # 显示无效频道
        invalid_output = []
        for category, channels in self.invalid_channels.items():
            invalid_output.append(f"\n=== {category} ({len(channels)} 个) ===")
            for channel in channels:
                line = f"{channel['name']} | {channel['url']}"
                if channel.get('error'):
                    line += f" | 错误: {channel['error']}"
                invalid_output.append(line)
        
        if invalid_output:
            self.invalid_text.config(state="normal")
            self.invalid_text.insert(1.0, '\n'.join(invalid_output))
            self.invalid_text.config(state="disabled")
        
        # 显示详细信息
        detail_output = []
        for result in self.validation_results:
            detail_output.append(f"频道: {result['name']}")
            detail_output.append(f"URL: {result['url']}")
            detail_output.append(f"分类: {result['category']}")
            detail_output.append(f"状态: {'有效' if result['valid'] else '无效'}")
            if result.get('resolution'):
                detail_output.append(f"分辨率: {result['resolution']}")
            if result.get('codec'):
                detail_output.append(f"编码: {result['codec']}")
            if result.get('audio') is not None:
                audio_status = "有音频" if result['audio'] else "无音频"
                detail_output.append(f"音频: {audio_status}")
            if result.get('response_time') is not None:
                detail_output.append(f"响应速度: {result['response_time']}ms")
            if result.get('validation_method'):
                detail_output.append(f"检测方法: {result['validation_method']}")
            if result.get('error'):
                detail_output.append(f"错误: {result['error']}")
            detail_output.append("-" * 50)
        
        if detail_output:
            self.detail_text.config(state="normal")
            self.detail_text.insert(1.0, '\n'.join(detail_output))
            self.detail_text.config(state="disabled")
    
    def save_results(self):
        """保存结果（支持双保存模式和位置选择）"""
        if not self.validation_results:
            messagebox.showwarning("警告", "没有可保存的验证结果")
            return
            
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择源文件")
            return
        
        # 确保获取正确的源文件路径
        if not os.path.exists(file_path):
            messagebox.showwarning("警告", f"源文件不存在: {file_path}")
            return
        
        # 获取保存模式
        save_mode_text = self.save_mode_var.get()
        # 将中文文本映射为代码中使用的值
        save_mode = "valid" if save_mode_text == "只保存有效" else "all"
        mode_desc = "只保存有效源" if save_mode == "valid" else "保存全部源（有效+无效）"
        
        print(f"[调试] 保存模式文本: {save_mode_text}")
        print(f"[调试] 保存模式代码: {save_mode}")
        
        # 生成默认文件名（保持与原文件相同的扩展名）
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        # 清理文件名中的特殊字符，确保兼容性
        import re
        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)  # 替换Windows不支持的字符
        base_name = base_name.strip()  # 去除首尾空格
        
        original_ext = os.path.splitext(file_path)[1]  # 获取原文件扩展名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 默认保存到原文件所在目录
        default_dir = os.path.dirname(os.path.abspath(file_path))
        
        # 生成验证结果文件名：原文件名_验证结果_验证时间_模式
        if save_mode == "valid":
            default_filename = f"{base_name}_验证结果_有效_{timestamp}{original_ext}"
        else:
            default_filename = f"{base_name}_验证结果_全部_{timestamp}{original_ext}"
        
        print(f"[调试] 原始文件名: {os.path.basename(file_path)}")
        print(f"[调试] 清理后的文件名: {base_name}")
        print(f"[调试] 默认保存目录: {default_dir}")
        print(f"[调试] 默认文件名: {default_filename}")
        
        # 根据原文件类型设置文件类型过滤器
        if original_ext.lower() in ['.txt']:
            file_type_desc = "TXT文件"
            file_pattern = "*.txt"
        elif original_ext.lower() in ['.m3u', '.m3u8']:
            file_type_desc = "M3U文件"
            file_pattern = "*.m3u"
        else:
            file_type_desc = "所有文件"
            file_pattern = "*.*"
        
        # 弹出保存对话框
        from tkinter import filedialog
        output_path = filedialog.asksaveasfilename(
            title=f"保存{mode_desc}",
            initialdir=default_dir,
            initialfile=default_filename,
            defaultextension=original_ext,
            filetypes=[
                (file_type_desc, file_pattern),
                ("所有文件", "*.*")
            ],
            confirmoverwrite=True
        )
        
        # 用户取消保存
        if not output_path:
            print("[调试] 用户取消保存")
            return
        
        print(f"[调试] 用户选择的保存路径: {output_path}")
        print(f"[调试] 保存模式: {save_mode}")
        
        saved_files = []
        
        try:
            if save_mode == "valid":
                # 只保存有效源
                print(f"[调试] 保存有效源到: {output_path}")
                self._save_valid_only(output_path)
                saved_files.append(output_path)
            elif save_mode == "all":
                # 保存全部源（有效+无效）
                print(f"[调试] 保存全部源到: {output_path}")
                self._save_all_sources(output_path)
                saved_files.append(output_path)
            
            # 验证文件是否成功保存
            for saved_file in saved_files:
                if os.path.exists(saved_file):
                    print(f"[调试] 文件已成功保存: {saved_file}")
                else:
                    print(f"[警告] 文件保存可能失败: {saved_file}")
            
            # 显示保存成功信息
            saved_files_str = "\n".join(saved_files)
            messagebox.showinfo("保存成功", f"{mode_desc}已保存到:\n{saved_files_str}")
            
        except Exception as e:
            error_msg = f"保存结果时出错:\n{e}\n\n保存路径: {output_path}"
            print(f"[错误] {error_msg}")
            messagebox.showerror("保存失败", error_msg)
    
    def _save_valid_only(self, output_file):
        """只保存有效源（保持与原文件相同的格式）"""
        # 根据文件扩展名判断保存格式
        file_ext = os.path.splitext(output_file)[1].lower()
        
        if file_ext == '.txt':
            self._save_txt_format(output_file, valid_only=True)
        else:
            self._save_m3u_format(output_file, valid_only=True)
    
    def _save_all_sources(self, output_file):
        """保存全部源（有效+无效）（保持与原文件相同的格式）"""
        # 根据文件扩展名判断保存格式
        file_ext = os.path.splitext(output_file)[1].lower()
        
        if file_ext == '.txt':
            self._save_txt_format(output_file, valid_only=False)
        else:
            self._save_m3u_format(output_file, valid_only=False)

    def _save_txt_format(self, output_file, valid_only=True):
        """以TXT格式保存结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            if valid_only:
                # 只保存有效源
                f.write("# 有效直播源列表\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                valid_count = 0
                for category, channels in self.valid_channels.items():
                    if channels:  # 只写入有频道的分类
                        # 使用与Web版本相同的格式
                        f.write(f"{category},#genre#\n")
                        for channel in channels:
                            resolution = channel.get('resolution')
                            if resolution and resolution != (None, None):
                                if isinstance(resolution, tuple):
                                    resolution_str = f"{resolution[0]}x{resolution[1]}"
                                else:
                                    resolution_str = str(resolution)
                                f.write(f'{channel["name"]}[{resolution_str}],{channel["url"]}\n')
                            else:
                                f.write(f'{channel["name"]},{channel["url"]}\n')
                            valid_count += 1
                        f.write("\n")
                
                f.write(f"# 有效源总计: {valid_count} 个\n")
            else:
                # 保存全部源（有效+无效）
                f.write("# 直播源验证结果\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 写入有效源部分
                f.write("# ============================================\n")
                f.write("# 有效直播源\n")
                f.write("# ============================================\n")
                
                valid_count = 0
                for category, channels in self.valid_channels.items():
                    if channels:  # 只写入有频道的分类
                        # 使用与Web版本相同的格式
                        f.write(f"\n{category},#genre#\n")
                        for channel in channels:
                            resolution = channel.get('resolution')
                            if resolution and resolution != (None, None):
                                if isinstance(resolution, tuple):
                                    resolution_str = f"{resolution[0]}x{resolution[1]}"
                                else:
                                    resolution_str = str(resolution)
                                f.write(f'{channel["name"]}[{resolution_str}],{channel["url"]}\n')
                            else:
                                f.write(f'{channel["name"]},{channel["url"]}\n')
                            valid_count += 1
                        f.write("\n")
                
                f.write(f"\n# 有效源总计: {valid_count} 个\n")
                
                # 写入无效源部分
                f.write("\n# ============================================\n")
                f.write("# 无效直播源\n")
                f.write("# ============================================\n")
                
                invalid_count = 0
                for category, channels in self.invalid_channels.items():
                    if channels:  # 只写入有频道的分类
                        # 使用与Web版本相同的格式
                        f.write(f"\n{category},#genre#\n")
                        for channel in channels:
                            f.write(f"{channel['name']},{channel['url']}\n")
                            invalid_count += 1
                        f.write("\n")
                
                f.write(f"# 无效源总计: {invalid_count} 个\n")
                f.write(f"# 总计验证频道: {len(self.validation_results)} 个\n")

    def _save_m3u_format(self, output_file, valid_only=True):
        """以M3U格式保存结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            
            if valid_only:
                # 只保存有效源
                f.write("# 有效直播源列表\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                valid_count = 0
                for category, channels in self.valid_channels.items():
                    if channels:  # 只写入有频道的分类
                        f.write(f"\n{category} ({len(channels)} 个)\n")
                        for channel in channels:
                            # 使用与Web版本相同的格式
                            extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                            resolution = channel.get('resolution')
                            response_time = channel.get('response_time')
                            if resolution:
                                if resolution != (None, None):
                                    if isinstance(resolution, tuple):
                                        resolution_str = f"{resolution[0]}x{resolution[1]}"
                                    else:
                                        resolution_str = str(resolution)
                                    if response_time:
                                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str},{response_time}ms]'
                                    else:
                                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str}]'
                                else:
                                    if response_time:
                                        extinf += f',{channel["name"]}[{response_time}ms]'
                                    else:
                                        extinf += f',{channel["name"]}'
                            else:
                                if response_time:
                                    extinf += f',{channel["name"]}[{response_time}ms]'
                                else:
                                    extinf += f',{channel["name"]}'
                            f.write(extinf + "\n")
                            f.write(f"{channel['url']}\n")
                            valid_count += 1
                
                f.write(f"\n# 有效源总计: {valid_count} 个\n")
            else:
                # 保存全部源（有效+无效）
                f.write("# 直播源验证结果\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 写入有效源部分
                f.write("# ============================================\n")
                f.write("# 有效直播源\n")
                f.write("# ============================================\n")
                
                valid_count = 0
                for category, channels in self.valid_channels.items():
                    if channels:  # 只写入有频道的分类
                        f.write(f"\n{category} ({len(channels)} 个)\n")
                        for channel in channels:
                            # 使用与Web版本相同的格式
                            extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                            resolution = channel.get('resolution')
                            response_time = channel.get('response_time')
                            if resolution:
                                if resolution != (None, None):
                                    if isinstance(resolution, tuple):
                                        resolution_str = f"{resolution[0]}x{resolution[1]}"
                                    else:
                                        resolution_str = str(resolution)
                                    if response_time:
                                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str},{response_time}ms]'
                                    else:
                                        extinf += f' tvg-shift=1,{channel["name"]}[{resolution_str}]'
                                else:
                                    if response_time:
                                        extinf += f',{channel["name"]}[{response_time}ms]'
                                    else:
                                        extinf += f',{channel["name"]}'
                            else:
                                if response_time:
                                    extinf += f',{channel["name"]}[{response_time}ms]'
                                else:
                                    extinf += f',{channel["name"]}'
                            f.write(extinf + "\n")
                            f.write(f"{channel['url']}\n")
                            valid_count += 1
                
                f.write(f"\n# 有效源总计: {valid_count} 个\n")
                
                # 写入无效源部分
                f.write("\n# ============================================\n")
                f.write("# 无效直播源\n")
                f.write("# ============================================\n")
                
                invalid_count = 0
                for category, channels in self.invalid_channels.items():
                    if channels:  # 只写入有频道的分类
                        f.write(f"\n{category} ({len(channels)} 个)\n")
                        for channel in channels:
                            # 使用与Web版本相同的格式
                            extinf = f'#EXTINF:-1 tvg-name="{channel["name"]}" group-title="{category}"'
                            f.write(extinf + "\n")
                            f.write(f"{channel['url']}\n")
                            invalid_count += 1
                
                f.write(f"\n# 无效源总计: {invalid_count} 个\n")
                f.write(f"# 总计验证频道: {len(self.validation_results)} 个\n")
    
    def on_tree_click(self, event):
        """处理Treeview点击事件，点击URL列复制到剪贴板"""
        region = self.realtime_tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        column = self.realtime_tree.identify_column(event.x)
        item = self.realtime_tree.identify_row(event.y)
        
        if not item or column != '#3':  # 只处理URL列（第3列，序号是第1列）
            return
        
        values = self.realtime_tree.item(item, 'values')
        if values and len(values) > 2:
            url = values[2]
            if url and url != 'URL':
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.status_var.set(f"已复制URL: {url}")
    
    def update_realtime_display(self, channel):
        """实时更新Treeview表格 - 类似Web版的实时显示"""
        if not channel:
            return
        
        name = channel.get('name', '')
        url = channel.get('url', '')
        valid = '有效' if channel.get('valid') else '无效'
        
        # 优先使用分离的分辨率宽高信息，其次从resolution字符串中解析
        width = channel.get('resolution_width', '')
        height = channel.get('resolution_height', '')
        
        # 如果没有分离的宽高信息，则尝试从resolution字符串中解析
        if not width or not height:
            resolution = channel.get('resolution', '')
            if resolution:
                parts = resolution.split('*')
                if len(parts) == 2:
                    width = parts[0]
                    height = parts[1]
        
        speed = ''
        if channel.get('response_time'):
            speed = f"{channel['response_time']}ms"
        
        try:
            self.realtime_row_count += 1
            self.realtime_tree.insert('', tk.END, values=(self.realtime_row_count, name, url, valid, width, height, speed))
            self.realtime_tree.yview_moveto(1)
        except Exception:
            pass
    
    def clear_realtime_display(self):
        """清空实时结果表格"""
        for item in self.realtime_tree.get_children():
            self.realtime_tree.delete(item)
        self.realtime_row_count = 0
    
    def show_help(self):
        """显示使用说明"""
        help_text = """
直播源有效性验证工具 - 整合版 v3.0 (增强检测)

【新增功能】
✓ 多协议支持: HTTP, HTTPS, RTSP, RTMP, UDP, RTP
✓ IPv6地址支持
✓ 增强的HTTP请求处理 (HEAD/GET重试机制)
✓ 网络代理URL支持
✓ 音频检测功能
✓ VLC流检测
✓ 分辨率检测增强 (ffprobe + HLS解析)
✓ 实时进度显示
✓ 详细验证报告

【使用方法】
1. 选择M3U/M3U8/TXT格式的直播源文件
2. 配置验证参数 (超时时间、并发数等)
3. 选择检测选项 (VLC检测、分辨率检测、音频检测等)
4. 点击"开始验证"
5. 查看验证结果并保存报告（支持两种保存模式）

【保存模式说明】
- 只保存有效：只生成包含有效频道的M3U文件
- 保存全部：生成包含有效和无效频道的M3U文件，用分界线分隔
- 所有保存文件都会在原文件所在目录中生成

【文件格式支持】
- M3U/M3U8: 支持EXTINF标签和分类
- TXT: 支持"频道名,URL"格式

【检测方法说明】
- HTTP检测: 使用HEAD/GET请求验证连通性
- IPv6检测: 特殊处理IPv6地址格式
- 代理检测: 识别UDP/RTMP代理流
- 分辨率检测: URL解析 + HLS播放列表 + ffprobe
- 音频检测: 使用ffprobe检测音频流
- VLC检测: 使用VLC验证流播放性

【注意事项】
- 建议启用分辨率检测以获得更好的结果
- ffprobe不可用时，分辨率检测将受限
- VLC检测可能较慢但更准确
- 大量频道建议分批处理
        """
        
        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("800x600")
        help_window.resizable(True, True)
        
        help_text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state="disabled")
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("用户中断程序")
        except Exception as e:
            self.logger.error(f"程序运行出错: {e}")
            messagebox.showerror("程序错误", f"程序运行出错:\n{e}")

def main():
    """主函数"""
    try:
        app = EnhancedIntegratedValidatorApp()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()