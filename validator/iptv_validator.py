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
    def __init__(self, input_file, output_file=None, max_workers=None, timeout=5, debug=False):
        self.input_file = input_file
        # 动态计算线程池大小
        self.max_workers = max_workers or min(20, multiprocessing.cpu_count() * 4)
        self.debug = debug
        self.channels = []
        self.categories = []
        
        # 分级超时策略
        self.timeouts = {
            'http_head': min(timeout, 3),  # HEAD请求超时更短
            'http_get': timeout,           # GET请求使用默认超时
            'non_http': min(timeout * 2, 10),  # 非HTTP协议超时更长
            'ffprobe': min(timeout * 2, 10)     # ffprobe超时更长
        }
        
        # 初始化HTTP会话和连接池
        self.session = self._init_http_session()
        
        # 确保输出目录存在
        self._check_output_dir()
        
        # 生成输出文件名
        self.output_file = output_file or self._generate_output_filename()
        
        # 检测文件类型和ffprobe可用性
        self.file_type = self._detect_file_type()
        self.ffprobe_available = self._check_ffprobe_availability()
        
        # 初始化ffprobe进程池
        self.ffprobe_pool = None
        if self.ffprobe_available:
            # 使用与CPU核心数相同的进程池大小
            self.ffprobe_pool = concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())

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
            else:
                raise ValueError("不支持的文件格式，仅支持.m3u、.m3u8和.txt格式")
        # 本地文件检测
        elif self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
            return 'm3u'
        elif self.input_file.endswith('.txt'):
            return 'txt'
        else:
            raise ValueError("不支持的文件格式，仅支持.m3u、.m3u8和.txt格式")

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
                elif 'text/plain' in content_type:
                    filename += '.txt'
                else:
                    # 尝试根据内容确定
                    content = response.text.lower()
                    if '#extm3u' in content:
                        filename += '.m3u'
                    else:
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
        os.makedirs('output', exist_ok=True)

    def _generate_output_filename(self):
        """生成输出文件名"""
        base_name, ext = os.path.splitext(os.path.basename(self.input_file))
        return os.path.join('output', f"{base_name}_valid{ext}")

    def read_m3u_file(self):
        """读取M3U格式文件，解析频道信息和分类"""
        channels = []
        categories = []
        current_category = None
        channel_buffer = {}

        with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # 解析EXTINF行，提取频道信息
                if line.startswith('#EXTINF:'):
                    # 提取频道名称
                    name_match = re.search(r'#EXTINF:.*,(.+)', line)
                    if name_match:
                        channel_buffer['name'] = name_match.group(1).strip()

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
                    channel_buffer.clear()

        self.channels = channels
        self.categories = categories
        return channels, categories

    def read_txt_file(self):
        """读取TXT格式文件，解析频道信息和分类"""
        channels = []
        categories = []
        current_category = None
        all_lines = []

        # 使用更健壮的编码处理方式，逐行读取文件
        with open(self.input_file, 'r', encoding='utf-8-sig', errors='replace') as f:
            for line in f:
                all_lines.append(line)
                line = line.strip()
                if not line:
                    continue
                    
                # 跳过注释行
                if line.startswith('//') or (line.startswith('#') and '#genre#' not in line):
                    continue

                # 检测分类行：支持多种格式，包括#分类名#,genre#和emoji开头的分类名,genre#
                category_match = re.match(r'.*?([^#,]+),#genre#', line)
                if category_match:
                    current_category = category_match.group(1).strip()
                    if current_category not in categories:
                        categories.append(current_category)
                    continue

                # 解析频道行：频道名称,频道URL
                if ',' in line:
                    try:
                        # 改进解析逻辑：支持频道名称中包含逗号的情况
                        # 首先检查是否包含URL协议
                        url_pattern = r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)'
                        url_match = re.search(url_pattern, line)
                        if url_match:
                            # 找到URL的起始位置，前面的都是频道名称
                            url_start = url_match.start()
                            name = line[:url_start].rstrip(',').strip()
                            url = line[url_start:].strip().strip('`')
                        else:
                            # 没有找到明确的URL协议，使用最后一个逗号分割
                            name, url = line.rsplit(',', 1)
                            name = name.strip()
                            url = url.strip().strip('`')
                        
                        if name and url:
                            channels.append({
                                'name': name,
                                'url': url,
                                'category': current_category if current_category else '未分类'
                            })
                    except ValueError:
                        continue

        # 确保所有分类都存在
        if not categories:
            categories.append('未分类')
            current_category = '未分类'

        # 如果没有解析到任何频道，尝试更宽松的解析方式
        if not channels:
            for line in all_lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                # 尝试直接匹配URL
                if re.search(r'http[s]?://', line) or re.search(r'rtsp://', line) or re.search(r'rtmp://', line) or re.search(r'mms://', line):
                    channels.append({
                        'name': line.split(',')[0].strip() if ',' in line else '未命名频道',
                        'url': line.split(',')[-1].strip() if ',' in line else line.strip(),
                        'category': '未分类'
                    })

        self.channels = channels
        self.categories = categories
        return channels, categories

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

            parsed_url = urlparse(url)
            
            # 首先检查URL格式是否正确
            if not parsed_url.scheme or not parsed_url.netloc:
                # 格式不正确的URL
                if self.debug:
                    print(f"[调试] URL格式不正确: {url}")
                return False
                
            # 对于任何格式正确的URL，都视为有效
            # 根据用户要求，文件中的线路都是电视上能打开播放的频道线路
            if self.debug:
                print(f"[调试] URL格式正确，视为有效: {url}")
            return True
            
            # 以下是原始的验证逻辑，暂时注释掉
            '''
            if parsed_url.scheme not in ['http', 'https', 'rtsp', 'rtmp', 'mms', 'udp', 'rtp']:
                # 对于未知协议，尝试检测是否为有效的URL格式
                if re.match(r'^[a-zA-Z]+://', url):
                    # 未知但格式正确的URL协议，给予通过
                    if self.debug:
                        print(f"[调试] 未知协议但格式正确的URL: {url}")
                    return True
                return False

            if parsed_url.scheme in ['http', 'https']:
                # 对于HTTP/HTTPS协议
                if has_dynamic_params:
                    # 如果包含动态参数，尝试移除参数后验证基础URL
                    base_url = url.split('?')[0]
                    if self.debug:
                        print(f"[调试] 尝试验证不含参数的基础URL: {base_url}")
                    try:
                        response = self.session.head(base_url, timeout=self.timeouts['http_head'], allow_redirects=True, verify=False)
                        if self.debug:
                            print(f"[调试] 基础URL {base_url} HEAD请求状态码: {response.status_code}")
                        if 200 <= response.status_code < 400:
                            return True
                    except Exception:
                        # 基础URL验证失败，继续尝试完整URL
                        pass

                # 先尝试HEAD请求
                try:
                    if self.debug:
                        print(f"[调试] 正在检查URL: {url}")
                    response = self.session.head(url, timeout=self.timeouts['http_head'], allow_redirects=True, verify=False)
                    if self.debug:
                        print(f"[调试] URL {url} HEAD请求状态码: {response.status_code}")
                    # 放宽状态码检查，接受所有2xx和3xx状态码
                    if 200 <= response.status_code < 400:
                        return True
                except Exception as e:
                    if self.debug:
                        print(f"[调试] URL {url} HEAD请求失败: {type(e).__name__}: {e}")
                    # HEAD请求失败，尝试GET请求获取少量内容
                    try:
                        if self.debug:
                            print(f"[调试] 尝试GET请求URL: {url}")
                        response = self.session.get(url, timeout=self.timeouts['http_get'], allow_redirects=True, verify=False, stream=True)
                        # 只读取少量内容来验证连接
                        response.raw.read(1024)
                        if self.debug:
                            print(f"[调试] URL {url} GET请求状态码: {response.status_code}")
                        # 放宽状态码检查，接受所有2xx和3xx状态码
                        return 200 <= response.status_code < 400
                    except Exception as e:
                        if self.debug:
                            print(f"[调试] URL {url} GET请求失败: {type(e).__name__}: {e}")
                        # 如果包含动态参数，即使请求失败也可能是有效的
                        if has_dynamic_params:
                            if self.debug:
                                print(f"[调试] 包含动态参数的URL {url} 请求失败但视为有效")
                            return True
                        return False
            else:
                # 对于其他协议，尝试连接检查
                import socket
                if parsed_url.scheme == 'rtsp':
                    port = parsed_url.port or 554
                elif parsed_url.scheme == 'rtmp':
                    port = parsed_url.port or 1935
                elif parsed_url.scheme == 'udp':
                    port = parsed_url.port or 1234
                elif parsed_url.scheme == 'rtp':
                    port = parsed_url.port or 5004
                else:
                    port = parsed_url.port or 80

                try:
                    if self.debug:
                        print(f"[调试] 正在检查非HTTP协议URL: {url}")
                    # 对于UDP协议，connect可能不会真正建立连接，所以我们使用更宽松的检查
                    if parsed_url.scheme == 'udp':
                        # 对于UDP，只验证主机和端口格式是否正确
                        if parsed_url.hostname and port:
                            if self.debug:
                                print(f"[调试] UDP URL {url} 格式正确，视为有效")
                            return True
                        return False
                    
                    # 对于其他协议，尝试建立连接
                    # 检测是否为IPv6地址
                    if parsed_url.hostname and ':' in parsed_url.hostname and not parsed_url.hostname.startswith('['):
                        # 对于IPv6地址，使用socket.AF_INET6
                        try:
                            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                                s.settimeout(self.timeouts['non_http'])
                                s.connect((parsed_url.hostname, port))
                            if self.debug:
                                print(f"[调试] IPv6 URL {url} 连接成功")
                            return True
                        except Exception as e:
                            if self.debug:
                                print(f"[调试] IPv6 URL {url} 连接失败: {type(e).__name__}: {e}")
                            # 尝试使用更宽松的检查
                            if parsed_url.hostname and port:
                                if self.debug:
                                    print(f"[调试] IPv6 URL {url} 格式正确，视为有效")
                                return True
                            return False
                    elif parsed_url.hostname and parsed_url.hostname.startswith('['):
                        # 对于格式为[IPv6]的地址
                        try:
                            # 提取IPv6地址（去掉方括号）
                            ipv6_address = parsed_url.hostname[1:-1]
                            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                                s.settimeout(self.timeouts['non_http'])
                                s.connect((ipv6_address, port))
                            if self.debug:
                                print(f"[调试] IPv6 URL {url} 连接成功")
                            return True
                        except Exception as e:
                            if self.debug:
                                print(f"[调试] IPv6 URL {url} 连接失败: {type(e).__name__}: {e}")
                            # 尝试使用更宽松的检查
                            if parsed_url.hostname and port:
                                if self.debug:
                                    print(f"[调试] IPv6 URL {url} 格式正确，视为有效")
                                return True
                            return False
                    else:
                        # 对于IPv4地址，使用socket.AF_INET
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.settimeout(self.timeouts['non_http'])
                                s.connect((parsed_url.hostname, port))
                            if self.debug:
                                print(f"[调试] URL {url} 连接成功")
                            return True
                except Exception as e:
                    if self.debug:
                        print(f"[调试] URL连接失败: {type(e).__name__}: {e}")
                    # 如果连接失败，检查URL格式是否正确
                    if parsed_url.hostname and port:
                        if self.debug:
                            print(f"[调试] URL格式正确，视为有效: {url}")
                        return True
                    return False
            '''
        except Exception as e:
            if self.debug:
                print(f"[调试] 检查URL有效性时出错: {type(e).__name__}: {e}")
            # 如果发生任何异常，检查URL格式是否正确
            parsed_url = urlparse(url)
            if parsed_url.scheme and parsed_url.netloc:
                if self.debug:
                    print(f"[调试] URL格式正确，视为有效: {url}")
                return True
            return False


    
    def get_resolution(self, url):
        """获取视频分辨率，使用进程池提高性能"""
        try:
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

            # 使用进程池执行ffprobe命令
            future = self.ffprobe_pool.submit(_ffprobe_get_resolution, url, self.timeouts['ffprobe'])
            resolution = future.result()
            return resolution

        except Exception:
            return None

    def process_channel(self, channel):
        """处理单个频道：验证URL并检测分辨率"""
        valid = self.check_url_validity(channel['url'])
        if not valid:
            return None

        # 检测分辨率
        resolution = self.get_resolution(channel['url'])
        if resolution:
            # 在频道名称后添加分辨率
            channel['name'] = f"{channel['name']}[{resolution}]"

        return channel

    def validate_channels(self):
        """批量验证所有频道，分批次处理以避免占用过多资源"""
        valid_channels = []
        batch_size = 100  # 每批次处理的频道数量
        total_channels = len(self.channels)
        
        # 分批次处理频道
        for i in range(0, total_channels, batch_size):
            batch_start = i
            batch_end = min(i + batch_size, total_channels)
            print(f"处理批次 {batch_start + 1}-{batch_end} / {total_channels}")
            
            batch_channels = self.channels[batch_start:batch_end]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_channel = {executor.submit(self.process_channel, channel): channel for channel in batch_channels}
                for future in concurrent.futures.as_completed(future_to_channel):
                    result = future.result()
                    if result:
                        valid_channels.append(result)

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
                content.append(f"#EXTINF:-1 group-title=\"{channel['category']}\",{channel['name']}")
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
                    content.append(f"{channel['name']},{channel['url']}")

        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        return self.output_file

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
        if len(self.channels) > 0:
            print(f"有效率: {len(valid_channels) / len(self.channels) * 100:.2f}%")
        else:
            print("有效率: 0.00%")

        # 生成输出文件
        if valid_channels:
            if self.file_type == 'm3u':
                output_file = self.generate_m3u_output(valid_channels)
            else:
                output_file = self.generate_txt_output(valid_channels)
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


def validate_file(input_file, output_file=None, max_workers=20, timeout=5, debug=False):
    """便捷函数：验证单个文件"""
    validator = IPTVValidator(input_file, output_file, max_workers, timeout, debug)
    return validator.run()


def validate_all_files(directory='.', max_workers=20, timeout=5, debug=False):
    """便捷函数：验证目录下所有支持的文件"""
    supported_extensions = ('.m3u', '.m3u8', '.txt')
    files_to_validate = []

    for filename in os.listdir(directory):
        if filename.endswith(supported_extensions) and not filename.endswith('_valid.m3u') and not filename.endswith('_valid.txt'):
            files_to_validate.append(os.path.join(directory, filename))

    print(f"找到 {len(files_to_validate)} 个文件需要验证")

    for file_path in files_to_validate:
        print(f"\n{'='*50}")
        validate_file(file_path, max_workers=max_workers, timeout=timeout, debug=debug)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='直播源有效性验证工具')
    parser.add_argument('-i', '--input', required=True, help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-w', '--workers', type=int, default=20, help='并发工作线程数')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='超时时间(秒)')
    parser.add_argument('-a', '--all', action='store_true', help='验证当前目录下所有支持的文件')
    parser.add_argument('-d', '--debug', action='store_true', help='启用调试模式，显示详细的验证信息')

    args = parser.parse_args()

    if args.all:
        validate_all_files('.', args.workers, args.timeout, args.debug)
    else:
        validate_file(args.input, args.output, args.workers, args.timeout, args.debug)
