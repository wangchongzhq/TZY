#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4K超高清直播源处理脚本
功能：
1. 从4K_uhd_channels.txt中提取所有.m3u结尾的直播源URL
2. 将这些.m3u格式的直播源转换为.txt格式
3. 提取4K_uhd_channels.txt中所有.txt结尾的直播源URL
4. 合并所有直播源并去重
5. 输出到4K_uhd_hb.txt文件

可以手动运行，也可以通过GitHub Actions自动运行
"""

import os
import re
import requests
import time
from datetime import datetime
from urllib.parse import urlparse

# 配置参数
TIMEOUT = 10  # 超时时间（秒）
MAX_RETRIES = 3  # 最大重试次数
OUTPUT_FILE = '4K_uhd_hb.txt'  # 输出文件名
INPUT_FILE = '4K_uhd_channels.txt'  # 输入文件名
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
MAX_URLS = 5  # 测试时限制处理的URL数量，设置为None表示处理全部URL

# 日志记录
def log_message(message):
    """记录日志信息"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')

# 下载文件内容
def download_content(url, retries=MAX_RETRIES):
    """下载URL内容，支持重试"""
    headers = {'User-Agent': USER_AGENT}
    
    for attempt in range(1, retries + 1):
        try:
            log_message(f'正在下载: {url} (尝试 {attempt}/{retries})')
            response = requests.get(url, timeout=TIMEOUT, headers=headers)
            
            # 对于404错误，直接放弃，不重试
            if response.status_code == 404:
                log_message(f'资源不存在 (404): {url}，直接放弃')
                return None
                
            response.raise_for_status()
            log_message(f'成功下载: {url}')
            return response.text
        except requests.exceptions.RequestException as e:
            log_message(f'下载失败: {url} - {e}')
            # 对于404错误，不重试
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                log_message(f'资源不存在 (404): {url}，直接放弃')
                return None
            
            if attempt < retries:
                wait_time = min(2 ** attempt, 10)
                log_message(f'{wait_time}秒后重试...')
                time.sleep(wait_time)
            else:
                log_message(f'达到最大重试次数，放弃下载: {url}')
    return None

# 从M3U内容提取频道
def extract_channels_from_m3u(m3u_content, source_url):
    """从M3U格式内容中提取频道信息"""
    channels = []
    lines = m3u_content.splitlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 查找包含频道信息的行
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            name_match = re.search(r',(.+)', line)
            if name_match:
                channel_name = name_match.group(1).strip()
                # 检查下一行是否为URL
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith(('http://', 'https://')):
                        channel_url = next_line
                        # 排除示例或演示URL
                        if 'example' not in channel_url.lower() and 'demo' not in channel_url.lower():
                            channels.append((channel_name, channel_url))
                            i += 1  # 跳过下一行的URL
        
        i += 1
    
    log_message(f'从 {source_url} 提取了 {len(channels)} 个频道')
    return channels

# 从TXT内容提取频道
def extract_channels_from_txt(txt_content, source_url):
    """从TXT格式内容中提取频道信息（格式：名称,URL）"""
    channels = []
    lines = txt_content.splitlines()
    
    for line in lines:
        line = line.strip()
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
        
        # 分割名称和URL（支持逗号分隔）
        parts = line.split(',', 1)
        if len(parts) == 2:
            channel_name = parts[0].strip()
            channel_url = parts[1].strip()
            # 排除示例或演示URL
            if channel_url.startswith(('http://', 'https://')) and \
               'example' not in channel_url.lower() and 'demo' not in channel_url.lower():
                channels.append((channel_name, channel_url))
    
    log_message(f'从 {source_url} 提取了 {len(channels)} 个频道')
    return channels

# 从输入文件提取直播源URL
def extract_source_urls(input_file):
    """从输入文件中提取.m3u和.txt结尾的直播源URL"""
    m3u_urls = []
    txt_urls = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配所有URL（以http://或https://开头，以.m3u或.txt结尾）
        url_pattern = r'https?://[^\s#]+'
        urls = re.findall(url_pattern, content)
        
        for url in urls:
            if url.endswith('.m3u'):
                m3u_urls.append(url)
            elif url.endswith('.txt'):
                txt_urls.append(url)
        
        log_message(f'从 {input_file} 提取了 {len(m3u_urls)} 个.m3u URL 和 {len(txt_urls)} 个.txt URL')
        return m3u_urls, txt_urls
    
    except Exception as e:
        log_message(f'读取输入文件失败: {input_file} - {e}')
        return [], []

# 主函数
def main():
    """主函数"""
    start_time = time.time()
    log_message('开始处理4K超高清直播源...')
    
    # 提取所有直播源URL
    m3u_urls, txt_urls = extract_source_urls(INPUT_FILE)
    
    all_channels = []
    processed_urls = set()
    success_count = 0
    fail_count = 0
    
    # 处理.m3u格式的直播源
    log_message('\n开始处理.m3u格式的直播源...')
    log_message(f'总共需要处理 {len(m3u_urls)} 个.m3u URL')
    
    # 限制处理的URL数量（仅用于测试）
    urls_to_process = m3u_urls[:MAX_URLS] if MAX_URLS else m3u_urls
    if MAX_URLS:
        log_message(f'测试模式：仅处理前 {MAX_URLS} 个URL')
    
    for i, url in enumerate(urls_to_process, 1):
        log_message(f'\n处理第 {i}/{len(urls_to_process)} 个URL')
        # 避免重复处理相同的URL
        if url in processed_urls:
            log_message(f'跳过重复URL: {url}')
            fail_count += 1
            continue
        processed_urls.add(url)
        
        # 下载并解析M3U内容
        m3u_content = download_content(url)
        if m3u_content:
            channels = extract_channels_from_m3u(m3u_content, url)
            all_channels.extend(channels)
            success_count += 1
        else:
            fail_count += 1
    
    log_message(f'\n.m3u直播源处理完成:')
    log_message(f'- 成功: {success_count} 个')
    log_message(f'- 失败: {fail_count} 个')
    log_message(f'- 提取频道总数: {len(all_channels)} 个')
    
    # 重置计数器，处理.txt格式的直播源
    success_count = 0
    fail_count = 0
    
    log_message('\n开始处理.txt格式的直播源...')
    log_message(f'总共需要处理 {len(txt_urls)} 个.txt URL')
    
    # 限制处理的URL数量（仅用于测试）
    txt_urls_to_process = txt_urls[:MAX_URLS] if MAX_URLS else txt_urls
    if MAX_URLS:
        log_message(f'测试模式：仅处理前 {MAX_URLS} 个URL')
    
    for i, url in enumerate(txt_urls_to_process, 1):
        log_message(f'\n处理第 {i}/{len(txt_urls_to_process)} 个URL')
        # 避免重复处理相同的URL
        if url in processed_urls:
            log_message(f'跳过重复URL: {url}')
            fail_count += 1
            continue
        processed_urls.add(url)
        
        # 下载并解析TXT内容
        txt_content = download_content(url)
        if txt_content:
            channels = extract_channels_from_txt(txt_content, url)
            all_channels.extend(channels)
            success_count += 1
        else:
            fail_count += 1
    
    log_message(f'\n.txt直播源处理完成:')
    log_message(f'- 成功: {success_count} 个')
    log_message(f'- 失败: {fail_count} 个')
    log_message(f'- 提取频道总数: {len(all_channels)} 个')
    
    # 去重（基于URL）
    log_message(f'\n处理前总频道数: {len(all_channels)}')
    unique_channels = {}
    duplicate_count = 0
    
    for name, url in all_channels:
        if url not in unique_channels:
            unique_channels[url] = name
        else:
            duplicate_count += 1
            # 如果URL已存在，保留名称较长的频道
            if len(name) > len(unique_channels[url]):
                unique_channels[url] = name
    
    log_message(f'去重后总频道数: {len(unique_channels)}')
    log_message(f'去重的频道数: {duplicate_count}')
    
    # 简化输出内容生成逻辑
    output_lines = [
        '# 4K超高清直播源合并列表',
        f'# 更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'# 频道总数: {len(unique_channels)}',
        '',
        '# 频道列表（格式：频道名称,频道URL）',
        ''
    ]
    
    # 添加所有4K频道（如果有）
    if unique_channels:
        for url, name in unique_channels.items():
            output_lines.append(f'{name},{url}')
    else:
        output_lines.append('# 暂无可用的4K直播源')
    
    # 直接写入输出文件（使用简单的方式）
    log_message(f'\n准备写入输出文件: {OUTPUT_FILE}')
    log_message(f'输出内容行数: {len(output_lines)}')
    
    try:
        # 使用绝对路径确保文件位置正确
        absolute_path = os.path.abspath(OUTPUT_FILE)
        log_message(f'使用绝对路径: {absolute_path}')
        
        with open(absolute_path, 'w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(line + '\n')
        
        # 验证文件是否存在
        if os.path.exists(absolute_path):
            log_message(f'\n成功创建输出文件！')
            log_message(f'文件路径: {absolute_path}')
            log_message(f'文件大小: {os.path.getsize(absolute_path)} 字节')
            
            # 读取文件前几行验证内容
            with open(absolute_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            log_message(f'文件实际行数: {len(lines)}')
            log_message(f'文件前3行内容:')
            for i, line in enumerate(lines[:3]):
                log_message(f'  {i+1}: {line.strip()}')
        else:
            log_message(f'\n警告：文件创建失败！')
            
    except Exception as e:
        log_message(f'\n写入文件时发生错误: {e}')
        import traceback
        log_message(f'错误详情: {traceback.format_exc()}')
    
    if len(unique_channels) == 0:
        log_message(f'警告：没有找到任何可用的4K直播源，输出文件仅包含标题和注释')
    else:
        log_message(f'共处理 {len(all_channels)} 个频道，去重后剩余 {len(unique_channels)} 个频道')
    
    end_time = time.time()
    log_message(f'\n处理完成，总耗时: {end_time - start_time:.2f} 秒')

if __name__ == '__main__':
    main()
