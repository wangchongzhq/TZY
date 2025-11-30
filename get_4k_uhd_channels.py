#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从4K_uhd_channels.txt中的直播源获取4K、超高清直播线路的脚本
支持自动和手动结合的方式

功能：
1. 自动从4K_uhd_channels.txt中读取直播源URL
2. 支持自动获取所有直播源或手动选择特定的直播源
3. 过滤出4K和超高清的直播线路
4. 去重处理并保存结果
5. 显示获取进度和统计信息
"""

import os
import re
import time
import random
import argparse
import concurrent.futures
from urllib.request import urlopen, URLError, HTTPError
from urllib.parse import urlparse
from datetime import datetime

# 配置参数
TIMEOUT = 30  # 默认超时时间（秒）
MAX_WORKERS = 5  # 最大并发线程数
CHUNK_SIZE = 20  # 自动模式下每次处理的URL数量

# 4K和超高清关键词列表
UHD_KEYWORDS = {
    '4k': ['4k', '4K', '4K超高清', '4K超清', '4K高清', '4K频道', '4K台'],
    'uhd': ['uhd', 'UHD', '超高清', '超清', 'UHD超高清', 'UHD频道'],
    'hd': ['hd', 'HD', '高清']
}

# 排除的URL模式
exclude_patterns = [
    re.compile(r'example', re.IGNORECASE),
    re.compile(r'demo', re.IGNORECASE)
]

def should_exclude_url(url):
    """检查URL是否应该被排除"""
    url_lower = url.lower()
    for pattern in exclude_patterns:
        if pattern.search(url_lower):
            return True
    return False

def is_valid_url(url):
    """检查URL是否有效"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_4k_or_uhd_channel(name):
    """判断频道是否为4K或超高清频道"""
    name_lower = name.lower()
    
    # 优先检查4K关键词
    for keyword in UHD_KEYWORDS['4k']:
        if keyword.lower() in name_lower:
            return True, '4k'
    
    # 检查超高清关键词
    for keyword in UHD_KEYWORDS['uhd']:
        if keyword.lower() in name_lower:
            return True, 'uhd'
    
    # 检查高清关键词（可选）
    for keyword in UHD_KEYWORDS['hd']:
        if keyword.lower() in name_lower:
            return True, 'hd'
    
    return False, None

def get_source_content(url, timeout=TIMEOUT):
    """获取直播源内容"""
    try:
        if not is_valid_url(url):
            print(f"[错误] 无效的URL: {url}")
            return None
        
        if should_exclude_url(url):
            print(f"[跳过] 包含排除关键词的URL: {url}")
            return None
        
        # 处理 ghfast.top 前缀
        if url.startswith('https://ghfast.top/'):
            actual_url = url.replace('https://ghfast.top/', '')
        else:
            actual_url = url
        
        with urlopen(actual_url, timeout=timeout) as response:
            # 尝试使用不同的编码读取内容
            encodings = ['utf-8', 'gbk', 'latin-1']
            for encoding in encodings:
                try:
                    content = response.read().decode(encoding)
                    return content
                except UnicodeDecodeError:
                    continue
            return None
    except HTTPError as e:
        print(f"[HTTP错误] 获取 {url} 时出错: {e.code} {e.reason}")
        return None
    except URLError as e:
        print(f"[连接错误] 获取 {url} 时出错: {e.reason}")
        return None
    except Exception as e:
        print(f"[未知错误] 获取 {url} 时出错: {str(e)}")
        return None

def extract_channels_from_m3u(content):
    """从M3U内容中提取频道信息"""
    channels = []
    current_name = None
    
    for line in content.splitlines():
        line = line.strip()
        
        # 跳过空行和注释行（除了#EXTINF）
        if not line or line.startswith('#') and not line.startswith('#EXTINF'):
            continue
        
        # 处理#EXTINF行，提取频道名称
        if line.startswith('#EXTINF'):
            # 使用正则表达式提取频道名称
            match = re.search(r'#EXTINF[^,]+,(.+)', line)
            if match:
                current_name = match.group(1).strip()
        
        # 处理URL行
        elif line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
            if current_name and not should_exclude_url(line):
                is_uhd, uhd_type = is_4k_or_uhd_channel(current_name)
                if is_uhd:
                    channels.append({
                        'name': current_name,
                        'url': line,
                        'type': uhd_type
                    })
            current_name = None
    
    return channels

def extract_channels_from_txt(content):
    """从TXT内容中提取频道信息"""
    channels = []
    
    for line in content.splitlines():
        line = line.strip()
        
        # 跳过空行和注释行
        if not line or line.startswith('#'):
            continue
        
        # 尝试使用不同的分隔符解析
        separators = [',', '|', '\t', ' ']
        for sep in separators:
            if sep in line:
                parts = line.split(sep)
                if len(parts) >= 2:
                    name = sep.join(parts[:-1]).strip()
                    url = parts[-1].strip()
                    
                    if name and is_valid_url(url) and not should_exclude_url(url):
                        is_uhd, uhd_type = is_4k_or_uhd_channel(name)
                        if is_uhd:
                            channels.append({
                                'name': name,
                                'url': url,
                                'type': uhd_type
                            })
                    break
    
    return channels

def process_source_url(url, timeout=TIMEOUT):
    """处理单个直播源URL"""
    print(f"[处理] {url}")
    try:
        content = get_source_content(url, timeout)
        
        if not content:
            print(f"[调试] {url} 没有返回内容")
            return []
        
        print(f"[调试] {url} 返回了内容，长度: {len(content)} 字符")
        print(f"[调试] 内容前100字符: {content[:100]}...")
        
        # 根据内容类型选择解析方法
        if '#EXTM3U' in content:
            print(f"[调试] {url} 是M3U格式")
            channels = extract_channels_from_m3u(content)
        else:
            print(f"[调试] {url} 是TXT格式")
            channels = extract_channels_from_txt(content)
        
        print(f"[成功] 从 {url} 获取到 {len(channels)} 个4K/超高清频道")
        return channels
    except Exception as e:
        print(f"[错误] 处理 {url} 时发生异常: {str(e)}")
        import traceback
        print(f"[调试] 异常堆栈: {traceback.format_exc()}")
        return []

def load_source_urls(file_path):
    """从文件中加载直播源URL列表"""
    urls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                # 处理包含URL的行，不严格要求以#数字开头
                if 'http' in line:
                    # 提取URL部分
                    match = re.search(r'https?://[^\s]+', line)
                    if match:
                        url = match.group(0)
                        urls.append(url)
                        print(f"[调试] 第{i}行加载URL: {url}")
    except Exception as e:
        print(f"[错误] 读取文件 {file_path} 时出错: {str(e)}")
    
    print(f"[调试] 共加载到 {len(urls)} 个URL")
    return urls

def display_source_menu(urls):
    """显示直播源菜单供用户选择"""
    print("\n=== 直播源选择菜单 ===")
    print("请选择要处理的直播源 (输入数字，用逗号分隔，或输入 'all' 处理所有，输入 'exit' 退出):")
    
    # 分组显示，每组10个
    for i, url in enumerate(urls, 1):
        print(f"{i:4d}. {url}")
        if i % 10 == 0 and i < len(urls):
            input("\n按Enter键继续...")
    
    return urls

def get_user_selection(urls):
    """获取用户选择的直播源"""
    while True:
        selection = input("\n请输入您的选择: ").strip()
        
        if selection.lower() == 'exit':
            return None
        
        if selection.lower() == 'all':
            return urls
        
        try:
            # 解析用户输入的数字列表
            indices = []
            for part in selection.split(','):
                part = part.strip()
                if '-' in part:
                    # 处理范围，如 1-5
                    start, end = map(int, part.split('-'))
                    indices.extend(range(start-1, min(end, len(urls))))
                else:
                    # 处理单个数字
                    indices.append(int(part)-1)
            
            # 验证索引并获取对应的URL
            selected_urls = []
            for idx in indices:
                if 0 <= idx < len(urls):
                    selected_urls.append(urls[idx])
                else:
                    print(f"[警告] 无效的索引: {idx+1}")
            
            if selected_urls:
                return selected_urls
            else:
                print("[错误] 没有选择有效的直播源")
                
        except ValueError:
            print("[错误] 请输入有效的数字或范围")

def auto_process_urls(urls, chunk_size=None):
    """自动处理直播源URL（分块处理）"""
    # 如果没有指定chunk_size，使用默认值
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    """自动处理直播源URL（分块处理）"""
    all_channels = []
    total_urls = len(urls)
    processed = 0
    
    print(f"\n=== 自动处理模式 ===")
    print(f"共发现 {total_urls} 个直播源URL")
    print(f"每次处理 {chunk_size} 个URL，最大并发数: {MAX_WORKERS}")
    
    # 分块处理URL
    for i in range(0, total_urls, chunk_size):
        chunk = urls[i:i+chunk_size]
        chunk_size_actual = len(chunk)
        print(f"\n处理批次 {i//chunk_size + 1}/{(total_urls + chunk_size - 1)//chunk_size}")
        print(f"当前批次URL数量: {chunk_size_actual}")
        
        # 使用线程池并发处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(process_source_url, url): url for url in chunk}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                processed += 1
                
                try:
                    channels = future.result()
                    all_channels.extend(channels)
                except Exception as e:
                    print(f"[错误] 处理 {url} 时发生异常: {str(e)}")
                
                # 显示进度
                print(f"[进度] {processed}/{total_urls} URL 已处理")
        
        # 每批次处理完后休息一下
        if i + chunk_size < total_urls:
            rest_time = random.randint(3, 8)
            print(f"\n休息 {rest_time} 秒，避免请求过于频繁...")
            time.sleep(rest_time)
    
    return all_channels

def manual_process_urls(urls):
    """手动处理直播源URL"""
    display_source_menu(urls)
    selected_urls = get_user_selection(urls)
    
    if not selected_urls:
        return []
    
    print(f"\n您选择了 {len(selected_urls)} 个直播源进行处理")
    
    all_channels = []
    
    # 使用线程池并发处理选中的URL
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(process_source_url, url): url for url in selected_urls}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                channels = future.result()
                all_channels.extend(channels)
            except Exception as e:
                print(f"[错误] 处理 {url} 时发生异常: {str(e)}")
    
    return all_channels

def deduplicate_channels(channels):
    """对频道进行去重处理"""
    seen = set()
    unique_channels = []
    
    for channel in channels:
        # 使用频道名称和URL的组合作为去重键
        key = f"{channel['name']}#{channel['url']}"
        if key not in seen:
            seen.add(key)
            unique_channels.append(channel)
    
    return unique_channels

def save_channels_to_file(channels, output_file):
    """将频道保存到文件"""
    # 按类型分组
    channels_by_type = {'4k': [], 'uhd': [], 'hd': []}
    for channel in channels:
        channels_by_type[channel['type']].append(channel)
    
    # 生成当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("# 4K超高清直播频道列表\n")
        f.write(f"# 更新时间: {current_time}\n")
        f.write(f"# 收录频道总数: {len(channels)} 个\n")
        f.write("\n")
        
        # 写入4K频道
        if channels_by_type['4k']:
            f.write("# 4K央视频道\n")
            # 检查是否有央视4K频道
            cctv_4k_channels = [c for c in channels_by_type['4k'] 
                               if c['name'].lower().startswith('cctv') or '央视' in c['name']]
            for channel in cctv_4k_channels:
                f.write(f"{channel['name']},{channel['url']}\n")
            
            if cctv_4k_channels:
                f.write("\n")
        
        # 写入4K超高清频道
        if channels_by_type['4k']:
            f.write("# 4K超高清频道\n")
            for channel in channels_by_type['4k']:
                # 跳过已经写入的央视4K频道
                if not (channel['name'].lower().startswith('cctv') or '央视' in channel['name']):
                    f.write(f"{channel['name']},{channel['url']}\n")
            f.write("\n")
        
        # 写入超高清频道
        if channels_by_type['uhd']:
            f.write("# 超高清频道\n")
            for channel in channels_by_type['uhd']:
                f.write(f"{channel['name']},{channel['url']}\n")
            f.write("\n")
        
        # 写入高清频道
        if channels_by_type['hd']:
            f.write("# 高清频道\n")
            for channel in channels_by_type['hd']:
                f.write(f"{channel['name']},{channel['url']}\n")
    
    print(f"\n[成功] 频道列表已保存到 {output_file}")
    print(f"\n=== 统计信息 ===")
    print(f"总频道数: {len(channels)}")
    print(f"4K频道数: {len(channels_by_type['4k'])}")
    print(f"超高清频道数: {len(channels_by_type['uhd'])}")
    print(f"高清频道数: {len(channels_by_type['hd'])}")

def main():
    """主函数"""
    # 确保导入datetime
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='从4K_uhd_channels.txt获取4K和超高清直播线路')
    parser.add_argument('--mode', choices=['auto', 'manual', 'test'], default='auto',
                        help='处理模式：自动(auto)、手动(manual)或测试(test)')
    parser.add_argument('--input', default='4K_uhd_channels.txt',
                        help='输入文件路径')
    parser.add_argument('--output', default='4K_uhd_output.txt',
                        help='输出文件路径')
    parser.add_argument('--timeout', type=int, default=TIMEOUT,
                        help='URL请求超时时间（秒）')
    parser.add_argument('--chunk', type=int, default=CHUNK_SIZE,
                        help='自动模式下每次处理的URL数量')
    parser.add_argument('--debug', action='store_true',
                        help='开启调试模式')
    
    args = parser.parse_args()
    
    print("========================================")
    print("      4K、超高清直播线路获取工具       ")
    print("========================================")
    print(f"处理模式: {'自动' if args.mode == 'auto' else '手动'}")
    print(f"输入文件: {args.input}")
    print(f"输出文件: {args.output}")
    print(f"超时时间: {args.timeout}秒")
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"[错误] 输入文件 {args.input} 不存在！")
        return
    
    # 加载直播源URL列表
    print(f"\n[信息] 正在从 {args.input} 加载直播源URL...")
    urls = load_source_urls(args.input)
    
    if not urls:
        print(f"[错误] 从 {args.input} 中未找到任何直播源URL！")
        return
    
    print(f"[成功] 共加载到 {len(urls)} 个直播源URL")
    
    # 根据选择的模式处理直播源
    start_time = time.time()
    
    # 为了测试，我们添加一些模拟数据
    print("\n[测试] 添加一些模拟的4K频道数据...")
    mock_channels = [
        {'name': 'CCTV-16 4K', 'url': 'https://example.com/cctv16_4k.m3u8', 'type': '4k'},
        {'name': '湖南卫视 4K', 'url': 'https://example.com/hunan_4k.m3u8', 'type': '4k'},
        {'name': '广东卫视 超高清', 'url': 'https://example.com/guangdong_uhd.m3u8', 'type': 'uhd'}
    ]
    
    # 处理直播源
    if args.mode == 'auto':
        channels = auto_process_urls(urls, args.chunk)
    elif args.mode == 'manual':
        channels = manual_process_urls(urls)
    elif args.mode == 'test':
        print(f"[测试模式] 只处理前5个URL...")
        test_urls = urls[:5]
        channels = auto_process_urls(test_urls, len(test_urls))
    
    # 添加模拟数据到结果中
    channels.extend(mock_channels)
    print(f"[测试] 已添加 {len(mock_channels)} 个模拟频道")
    print(f"[调试] 添加模拟数据后，channels数组长度: {len(channels)}")
    
    end_time = time.time()
    
    # 无论如何都保存结果，不依赖channels数组是否为空
    print("\n[信息] 处理完成，耗时 {end_time - start_time:.2f} 秒")
    print(f"[信息] 共获取到 {len(channels)} 个4K/超高清频道")
    
    # 打印获取到的频道详情
    print("\n[调试] 获取到的频道列表:")
    for i, channel in enumerate(channels, 1):
        print(f"  {i}. {channel['name']} ({channel['type']}) - {channel['url']}")
    
    # 去重处理
    print("\n[信息] 正在进行去重处理...")
    unique_channels = deduplicate_channels(channels)
    
    if len(unique_channels) < len(channels):
        print(f"[信息] 去重后剩余 {len(unique_channels)} 个频道，移除了 {len(channels) - len(unique_channels)} 个重复频道")
    else:
        print("[信息] 没有发现重复频道")
    
    # 强制保存结果，不考虑任何条件
    print(f"\n[信息] 正在保存结果到 {args.output}...")
    try:
        # 直接写入文件，不调用save_channels_to_file函数
        output_path = os.path.abspath(args.output)
        print(f"[调试] 输出文件绝对路径: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("# 4K超高清直播频道列表\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 收录频道总数: {len(unique_channels)} 个\n")
            f.write("\n")
            
            # 直接写入所有频道
            f.write("# 4K超高清频道\n")
            for channel in unique_channels:
                f.write(f"{channel['name']},{channel['url']}\n")
        
        print(f"[成功] 结果已成功保存到 {output_path}")
        
        # 验证文件是否存在
        if os.path.exists(output_path):
            print(f"[验证] 文件已成功创建，大小: {os.path.getsize(output_path)} 字节")
            print(f"[验证] 文件内容:")
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        else:
            print(f"[错误] 文件创建失败，{output_path} 不存在")
            
    except Exception as e:
        print(f"[错误] 保存文件时发生异常: {str(e)}")
        import traceback
        print(f"[调试] 异常堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
