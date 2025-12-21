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
from urllib.parse import urlparse


class IPTVValidator:
    def __init__(self, input_file, output_file=None, max_workers=20, timeout=5):
        self.input_file = input_file
        self.output_file = output_file or self._generate_output_filename()
        self.max_workers = max_workers
        self.timeout = timeout
        self.channels = []
        self.categories = []
        self.file_type = self._detect_file_type()
        self.ffprobe_available = self._check_ffprobe_availability()

    def _detect_file_type(self):
        """检测输入文件类型"""
        if self.input_file.endswith('.m3u') or self.input_file.endswith('.m3u8'):
            return 'm3u'
        elif self.input_file.endswith('.txt'):
            return 'txt'
        else:
            raise ValueError("不支持的文件格式，仅支持.m3u、.m3u8和.txt格式")

    def _check_ffprobe_availability(self):
        """检查ffprobe是否可用"""
        try:
            subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, shell=False)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _generate_output_filename(self):
        """生成输出文件名"""
        base_name, ext = os.path.splitext(self.input_file)
        return f"{base_name}_valid{ext}"

    def read_m3u_file(self):
        """读取M3U格式文件，解析频道信息和分类"""
        channels = []
        categories = []
        current_category = None
        channel_buffer = {}

        with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
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
                channel_buffer['url'] = line
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

        with open(self.input_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测分类行：#分类名#,genre#
            category_match = re.match(r'#(.+)#,genre#', line)
            if category_match:
                current_category = category_match.group(1)
                if current_category not in categories:
                    categories.append(current_category)
                continue

            # 解析频道行：频道名称,频道URL
            if ',' in line and current_category:
                try:
                    name, url = line.split(',', 1)
                    if name and url:
                        channels.append({
                            'name': name.strip(),
                            'url': url.strip(),
                            'category': current_category
                        })
                except ValueError:
                    continue

        self.channels = channels
        self.categories = categories
        return channels, categories

    def check_url_validity(self, url):
        """检查URL的有效性"""
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ['http', 'https', 'rtsp', 'rtmp', 'mms']:
                return False

            if parsed_url.scheme in ['http', 'https']:
                # 对于HTTP/HTTPS协议，发送HEAD请求检查
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                return response.status_code in [200, 301, 302]
            else:
                # 对于其他协议，尝试连接检查
                import socket
                if parsed_url.scheme == 'rtsp':
                    port = parsed_url.port or 554
                elif parsed_url.scheme == 'rtmp':
                    port = parsed_url.port or 1935
                else:
                    port = parsed_url.port or 80

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.timeout)
                    s.connect((parsed_url.hostname, port))
                return True

        except Exception:
            return False

    def get_resolution(self, url):
        """获取视频分辨率"""
        try:
            # 检查ffprobe是否可用
            if not self.ffprobe_available:
                return None

            # 只对支持的流格式进行分辨率检测
            if not (url.endswith('.m3u8') or 'm3u8' in url or url.startswith('rtsp://') or url.startswith('rtmp://')):
                return None

            # 使用ffprobe获取视频信息
            cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height', '-of', 'json', url
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout,
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
        """批量验证所有频道"""
        valid_channels = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_channel = {executor.submit(self.process_channel, channel): channel for channel in self.channels}
            for future in concurrent.futures.as_completed(future_to_channel):
                result = future.result()
                if result:
                    valid_channels.append(result)

        return valid_channels

    def generate_m3u_output(self, valid_channels):
        """生成M3U格式的输出文件"""
        # 按分类分组频道
        channels_by_category = {category: [] for category in self.categories}
        for channel in valid_channels:
            category = channel['category']
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
        channels_by_category = {category: [] for category in self.categories}
        for channel in valid_channels:
            category = channel['category']
            if category in channels_by_category:
                channels_by_category[category].append(channel)

        # 生成TXT内容
        content = []
        for category in self.categories:
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

        # 验证频道
        start_time = time.time()
        valid_channels = self.validate_channels()
        end_time = time.time()

        print(f"验证完成，耗时 {end_time - start_time:.2f} 秒")
        print(f"有效频道数: {len(valid_channels)}")
        print(f"有效率: {len(valid_channels) / len(self.channels) * 100:.2f}%")

        # 生成输出文件
        if valid_channels:
            if self.file_type == 'm3u':
                output_file = self.generate_m3u_output(valid_channels)
            else:
                output_file = self.generate_txt_output(valid_channels)
            print(f"输出文件已生成: {output_file}")
            return output_file
        else:
            print("没有有效的频道可输出")
            return None


def validate_file(input_file, output_file=None, max_workers=20, timeout=5):
    """便捷函数：验证单个文件"""
    validator = IPTVValidator(input_file, output_file, max_workers, timeout)
    return validator.run()


def validate_all_files(directory='.', max_workers=20, timeout=5):
    """便捷函数：验证目录下所有支持的文件"""
    supported_extensions = ('.m3u', '.m3u8', '.txt')
    files_to_validate = []

    for filename in os.listdir(directory):
        if filename.endswith(supported_extensions) and not filename.endswith('_valid.m3u') and not filename.endswith('_valid.txt'):
            files_to_validate.append(os.path.join(directory, filename))

    print(f"找到 {len(files_to_validate)} 个文件需要验证")

    for file_path in files_to_validate:
        print(f"\n{'='*50}")
        validate_file(file_path, max_workers=max_workers, timeout=timeout)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='直播源有效性验证工具')
    parser.add_argument('-i', '--input', required=True, help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-w', '--workers', type=int, default=20, help='并发工作线程数')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='超时时间(秒)')
    parser.add_argument('-a', '--all', action='store_true', help='验证当前目录下所有支持的文件')

    args = parser.parse_args()

    if args.all:
        validate_all_files('.', args.workers, args.timeout)
    else:
        validate_file(args.input, args.output, args.workers, args.timeout)
