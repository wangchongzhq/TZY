#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4K超高清直播源合并转换工具
功能：从4K_uhd_channels.txt中提取.m3u直播源URL，合并内容，转换为频道名称,URL格式的.txt文件
作者：AI Assistant
日期：2024-01-18
"""

import os
import re
import sys
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class UHDChannelMerger:
    """4K超高清直播源合并器"""
    
    def __init__(self):
        """初始化合并器"""
        self.input_file = "4K_uhd_channels.txt"
        self.output_file = "4K_uhd_hb.txt"
        self.url_pattern = re.compile(r'(https?://|file://)[^\s"\'\n]+\.m3u')
        self.encoding_patterns = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'iso-8859-1']
        self.visited_urls = set()
        self.channel_map = {}  # 用于去重和存储频道名称与URL的映射 {url: channel_name}
        self.total_channels = 0
        self.success_channels = 0
        self.failed_channels = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.lock = threading.Lock()
        self.max_workers = min(10, os.cpu_count() * 2)  # 线程池大小
    
    def set_input_output_files(self, input_file, output_file):
        """设置输入输出文件"""
        self.input_file = input_file
        self.output_file = output_file
    
    def extract_m3u_urls(self):
        """从输入文件中提取.m3u URL"""
        print(f"� 正在读取输入文件: {self.input_file}")
        urls = set()  # 使用集合自动去重
        
        try:
            with open(self.input_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
                # 提取HTTP/HTTPS URL
                http_urls = re.findall(r'https?://[^\s"\'\n]+\.m3u', content, re.IGNORECASE)
                urls.update(http_urls)
                
                # 提取本地文件URL
                file_urls = re.findall(r'file://[^\s"\'\n]+\.m3u', content, re.IGNORECASE)
                urls.update(file_urls)
            
            urls = sorted(urls)
            print(f"📊 找到 {len(urls)} 个.m3u直播源URL")
            
            # 显示找到的URL
            for i, url in enumerate(urls, 1):
                print(f"   {i}. {url}")
            
            return urls
            
        except FileNotFoundError:
            print(f"❌ 输入文件 {self.input_file} 不存在")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 读取输入文件时发生错误: {e}")
            sys.exit(1)
    
    def detect_encoding(self, file_path):
        """检测文件编码"""
        for encoding in self.encoding_patterns:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'  # 默认编码
    
    def download_m3u_content(self, url):
        """下载M3U内容（支持HTTP和本地文件）"""
        print(f"🌐 正在获取: {url}")
        
        if url.startswith('file://'):
            # 处理本地文件
            try:
                # 转换file:// URL为本地文件路径
                file_path = url[7:]  # 移除file://前缀
                
                # Windows路径修复
                if file_path.startswith('/'):
                    file_path = file_path[1:]  # 移除开头的/
                file_path = file_path.replace('/', '\\')
                
                # 检测文件编码
                encoding = self.detect_encoding(file_path)
                
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                print(f"✅ 成功读取本地文件: {file_path}")
                return content
                
            except Exception as e:
                print(f"❌ 读取本地文件时发生错误: {e}")
                return None
        else:
            # 处理HTTP/HTTPS URL
            retries = 0
            max_retries = 3
            
            while retries < max_retries:
                try:
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        # 尝试多种编码
                        for encoding in self.encoding_patterns:
                            try:
                                content = response.content.decode(encoding)
                                print(f"✅ 成功下载: {url}")
                                return content
                            except UnicodeDecodeError:
                                continue
                        
                        # 如果所有编码都失败，使用默认编码
                        content = response.text
                        print(f"✅ 成功下载（默认编码）: {url}")
                        return content
                    else:
                        print(f"❌ 下载失败 (状态码: {response.status_code}): {url}")
                        retries += 1
                        if retries < max_retries:
                            print(f"🔄 重试 ({retries}/{max_retries})...")
                            time.sleep(2)
                
                except requests.RequestException as e:
                    print(f"❌ 请求错误: {e} - {url}")
                    retries += 1
                    if retries < max_retries:
                        print(f"🔄 重试 ({retries}/{max_retries})...")
                        time.sleep(2)
            
            print(f"🚫 放弃下载: {url}")
            return None
    
    def parse_m3u_content(self, content, source_url):
        """解析M3U内容，提取频道信息（只保留频道名称和URL）"""
        parsed_channels = []
        
        try:
            lines = content.splitlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('#EXTINF:'):
                    # 提取频道名称（通常在最后一个逗号后）
                    if ',' in line:
                        channel_name = line.split(',')[-1].strip()
                    else:
                        channel_name = f"Channel_{len(parsed_channels) + 1}"
                    
                    # 下一行应该是URL
                    if i + 1 < len(lines):
                        url_line = lines[i + 1].strip()
                        if url_line.startswith(('http://', 'https://')):
                            channel_url = url_line
                            
                            # 使用URL作为键，频道名称作为值，用于去重
                            with self.lock:
                                if channel_url not in self.channel_map:
                                    self.channel_map[channel_url] = channel_name
                                    parsed_channels.append((channel_name, channel_url))
                                    print(f"    📡 频道: {channel_name} -> URL: {channel_url}")
                                else:
                                    print(f"    ⚠️  跳过重复频道 (URL已存在): {channel_name} -> URL: {channel_url}")
                            
                            i += 2  # 跳过URL行
                            continue
                    
                i += 1
            
            print(f"� 从{source_url}解析到 {len(parsed_channels)} 个频道")
            return parsed_channels
            
        except Exception as e:
            print(f"❌ 解析M3U内容时发生错误: {e}")
            return []
    
    def process_single_m3u(self, url):
        """处理单个M3U文件"""
        try:
            # 检查URL是否已处理过
            if url in self.visited_urls:
                print(f"🔄 跳过已处理的URL: {url}")
                return []
            
            self.visited_urls.add(url)
            
            # 下载或读取M3U内容
            content = self.download_m3u_content(url)
            
            if not content:
                print(f"🚫 无法获取{url}的内容")
                return []
            
            # 解析M3U内容
            channels = self.parse_m3u_content(content, url)
            
            return channels
            
        except Exception as e:
            print(f"❌ 处理{url}时发生错误: {e}")
            return []
    
    def save_results(self):
        """保存处理结果到文件（格式：频道名称,URL）"""
        try:
            # 从channel_map中获取所有频道（已自动去重）
            unique_channels = [f"{name},{url}" for url, name in self.channel_map.items()]
            unique_channels.sort()  # 按频道名称排序
            
            with open(self.output_file, 'w', encoding='utf-8-sig') as f:
                # 写入文件头信息
                f.write("# 4K超高清直播源合并列表\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 频道总数: {len(unique_channels)}\n")
                f.write(f"# 来源: {self.input_file}\n")
                f.write("\n")
                f.write("# 频道列表（格式：频道名称,频道URL）\n")
                f.write("\n")
                
                # 写入频道信息
                for channel in unique_channels:
                    f.write(f"{channel}\n")
            
            # 获取文件大小
            file_size = os.path.getsize(self.output_file) / 1024
            
            print(f"✅ 保存成功!")
            print(f"📁 文件名: {self.output_file}")
            print(f"📊 频道数: {len(unique_channels)}")
            print(f"📏 文件大小: {file_size:.2f} KB")
            
            # 显示示例内容
            print(f"\n📄 文件示例内容:")
            with open(self.output_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()[:10]  # 只显示前10行
                for line in lines:
                    print(f"   {line.rstrip()}")
            
        except Exception as e:
            print(f"❌ 保存文件时发生错误: {e}")
            sys.exit(1)
    
    def run(self):
        """主运行函数"""
        print("🚀 4K超高清直播源合并转换工具启动")
        start_time = time.time()
        
        try:
            # 1. 提取M3U URL
            m3u_urls = self.extract_m3u_urls()
            
            if not m3u_urls:
                print("🚫 没有找到.m3u直播源URL")
                sys.exit(1)
            
            # 2. 下载并解析所有M3U内容
            print("\n🔄 开始合并和转换直播源...")
            print(f"⚡ 使用 {self.max_workers} 个线程并行处理")
            
            # 使用线程池并行处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有下载任务
                future_to_url = {
                    executor.submit(self.process_single_m3u, url): url 
                    for url in m3u_urls
                }
                
                # 处理结果
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        future.result()  # 处理可能的异常
                    except Exception as e:
                        print(f"❌ 处理{url}时发生异常: {e}")
            
            # 3. 统计结果
            print("\n📊 合并统计:")
            print(f"   总处理URL数: {len(self.visited_urls)}")
            print(f"   去重后频道数: {len(self.channel_map)}")
            
            if not self.channel_map:
                print("🚫 没有解析到任何频道信息")
                sys.exit(1)
            
            # 4. 保存结果
            self.save_results()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print("\n" + "=" * 60)
            print(f"🏆 操作完成!")
            print(f"⏱️ 总耗时: {total_time:.2f} 秒")
            print(f"📝 结果文件: {self.output_file}")
            print(f"💡 提示: 可以手动或通过工作流定期运行此脚本")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断操作")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 程序运行时发生错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 检查依赖
    try:
        import requests
    except ImportError:
        print("❌ 缺少依赖库 requests")
        print("请运行: pip install requests")
        sys.exit(1)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='4K超高清直播源合并转换工具')
    parser.add_argument('-i', '--input-file', default='4K_uhd_channels.txt', help='输入文件路径')
    parser.add_argument('-o', '--output-file', default='4K_uhd_hb.txt', help='输出文件路径')
    args = parser.parse_args()
    
    # 创建合并器实例并运行
    merger = UHDChannelMerger()
    merger.set_input_output_files(args.input_file, args.output_file)
    merger.run()


if __name__ == "__main__":
    main()