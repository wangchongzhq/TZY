import os
import sys
import time
import requests
import re
import statistics
from typing import Dict, List, Tuple, Optional
import concurrent.futures

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# 测速配置
SPEED_TEST_CONFIG = {
    'timeout': 10,           # 请求超时时间（秒）
    'test_duration': 5,      # 测速持续时间（秒）
    'max_workers': 10,       # 并发工作线程数
    'min_download_size': 1024 * 1024,  # 最小下载大小（字节）
    'speed_test_enabled': True  # 是否启用测速功能
}

# 验证URL是否有效并测速
def test_url_speed(url, timeout=10):
    """测试URL的速度，返回有效性和速度信息"""
    try:
        start_time = time.time()
        downloaded_size = 0
        chunks = []

        # 对GitHub原始文件URL添加ghfast.top前缀
        if url.startswith('https://raw.githubusercontent.com/'):
            test_url = f"https://ghfast.top/{url}"
        else:
            test_url = url

        # 使用stream模式获取响应
        response = requests.get(test_url, headers=HEADERS, timeout=timeout, stream=True)

        if response.status_code != 200:
            response.close()
            return False, None

        # 读取数据块，计算速度
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                chunks.append(len(chunk))
                downloaded_size += len(chunk)

                # 如果已经下载了足够的数据或者超过了测试时间，停止测试
                if downloaded_size >= SPEED_TEST_CONFIG['min_download_size'] or \
                   time.time() - start_time >= SPEED_TEST_CONFIG['test_duration']:
                    break

        response.close()

        # 计算速度（KB/s）
        if downloaded_size > 0:
            duration = time.time() - start_time
            speed_kbps = (downloaded_size / 1024) / duration

            # 如果有多个数据块，计算稳定性（标准差与均值的比率）
            if len(chunks) > 1:
                chunk_speeds = [len(c) / (time.time() - start_time) * 1024 for c in chunks]
                stability = statistics.stdev(chunk_speeds) / statistics.mean(chunk_speeds) if len(chunk_speeds) > 1 else 0
            else:
                stability = 0

            return True, {
                'speed_kbps': speed_kbps,
                'downloaded_size': downloaded_size,
                'duration': duration,
                'stability': 1 - stability,  # 稳定性值，1表示最稳定
                'test_url': test_url
            }
        else:
            return True, None
    except Exception as e:
        return False, None

# 批量测试URL速度
def batch_test_urls(urls: List[str]) -> Dict[str, Dict]:
    """批量测试URL列表的速度"""
    results = {}

    start_time = time.time()

    # 使用线程池并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=SPEED_TEST_CONFIG['max_workers']) as executor:
        future_to_url = {executor.submit(test_url_speed, url): url for url in urls}

        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                is_valid, speed_info = future.result()
                results[url] = {
                    'valid': is_valid,
                    'speed_info': speed_info
                }

                # 显示进度
                if (i + 1) % 10 == 0 or i + 1 == len(urls):
            except Exception as e:
                results[url] = {
                    'valid': False,
                    'speed_info': None
                }

    total_time = time.time() - start_time

    # 统计结果
    valid_count = sum(1 for r in results.values() if r['valid'])
    speed_count = sum(1 for r in results.values() if r['valid'] and r['speed_info'])

    return results

# 读取文件内容
def read_file():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            return f.readlines()
    except:
        sys.exit(1)

# 写入文件内容
def write_file(lines):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except:
        sys.exit(1)

# 处理4K频道URL，验证并更新
def process_uhd_channels(lines):
    """处理4K频道列表，验证URL有效性，测试速度并更新时间戳"""
    processed_lines = []
    valid_channels = []
    github_sources_section = False
    channel_section = False
    urls_to_test = []
    url_mappings = {}

    # 解析文件内容，收集需要测试的URL
    for line in lines:
        line = line.strip()

        # 跳过文件头部和空行
        if not line or line.startswith('# 更新时间') or line.startswith('# 共包含'):
            continue

        # 处理频道行（格式：频道名称,URL）
        if ',' in line:
            parts = line.split(',')
            if len(parts) >= 2:
                channel_name = parts[0].strip()
                url = parts[1].strip()

                # 如果是GitHub URL，添加前缀
                if url.startswith('https://raw.githubusercontent.com/'):
                    test_url = f"https://ghfast.top/{url}"
                else:
                    test_url = url

                urls_to_test.append(test_url)
                url_mappings[test_url] = (channel_name, url)
        # 处理GitHub源建议中的URL行
        elif line.startswith('https://raw.githubusercontent.com/'):
            test_url = f"https://ghfast.top/{line}"
            urls_to_test.append(test_url)
            url_mappings[test_url] = ("GitHub源建议", line)
        # 处理注释中的URL
        elif '# ' in line and 'https://raw.githubusercontent.com/' in line:
            match = re.search(r'(# \d+\.) (https://raw\.githubusercontent\.com/.+)', line)
            if match:
                url = match.group(2)
                test_url = f"https://ghfast.top/{url}"
                urls_to_test.append(test_url)
                url_mappings[test_url] = ("GitHub源建议", url)

    # 测试URL速度
    speed_results = {}
    if SPEED_TEST_CONFIG['speed_test_enabled'] and urls_to_test:
        speed_results = batch_test_urls(urls_to_test)

    # 添加文件头部信息
    processed_lines.append("# 4K超高清直播源列表\n")
    processed_lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d')}\n")
    processed_lines.append(f"# 共包含 0 个4K超高清频道\n")
    processed_lines.append("# 测速结果会在文件中以注释形式显示\n")
    processed_lines.append("\n")

    # 处理文件内容
    for line in lines:
        line = line.strip()

        # 跳过重复的文件头部
        if line in ['# 4K超高清直播源列表', '# 更新时间: 2024-11-24', '# 更新时间: 2025-11-29', '# 共包含 0 个4K超高清频道']:
            continue

        # 处理空行
        if not line:
            processed_lines.append('\n')
            continue

        # 处理注释行
        if line.startswith('#'):
            # 检查是否进入GitHub源建议部分
            if '建议添加到get_cgq_sources.py' in line or '以下是' in line:
                github_sources_section = True
                channel_section = False
                processed_lines.append(line + '\n')
            # 检查是否进入4K央视频道部分
            elif line == '# 4K央视频道':
                github_sources_section = False
                channel_section = True
                processed_lines.append('# 4K央视频道\n')
                processed_lines.append('\n')
            # 处理GitHub源建议中的URL注释行
            elif '# ' in line and 'https://raw.githubusercontent.com/' in line:
                match = re.search(r'(# \d+\.) (https://raw\.githubusercontent\.com/.+)', line)
                if match:
                    prefix = match.group(1)
                    url = match.group(2)
                    proxied_url = f"https://ghfast.top/{url}"

                    # 添加带有前缀的URL
                    processed_lines.append(f"{prefix} {proxied_url}\n")

                    # 添加测速结果注释
                    if SPEED_TEST_CONFIG['speed_test_enabled'] and proxied_url in speed_results:
                        result = speed_results[proxied_url]
                        if result['valid']:
                            valid_channels.append(("GitHub源建议", proxied_url))
                            if result['speed_info']:
                                speed_kbps = result['speed_info']['speed_kbps']
                                stability = result['speed_info']['stability']
                                processed_lines.append(f"#   速度: {speed_kbps:.1f} KB/s, 稳定性: {stability:.2f}\n")
                            else:
                                processed_lines.append(f"#   状态: 有效，但无法测速\n")
                        else:
                            processed_lines.append(f"#   状态: 无效\n")
                else:
                    processed_lines.append(line + '\n')
            # 保留其他注释行
            else:
                processed_lines.append(line + '\n')
        # 处理频道行（格式：频道名称,URL）
        elif ',' in line and channel_section:
            parts = line.split(',')
            if len(parts) >= 2:
                channel_name = parts[0].strip()
                url = parts[1].strip()

                # 如果是GitHub URL，添加前缀
                if url.startswith('https://raw.githubusercontent.com/'):
                    proxied_url = f"https://ghfast.top/{url}"
                    test_url = proxied_url
                else:
                    proxied_url = url
                    test_url = url

                # 检查URL是否有效
                is_valid = False
                speed_comment = ""

                if SPEED_TEST_CONFIG['speed_test_enabled'] and test_url in speed_results:
                    result = speed_results[test_url]
                    is_valid = result['valid']

                    if is_valid:
                        valid_channels.append((channel_name, proxied_url))
                        if result['speed_info']:
                            speed_kbps = result['speed_info']['speed_kbps']
                            stability = result['speed_info']['stability']
                            speed_comment = f"# 速度: {speed_kbps:.1f} KB/s, 稳定性: {stability:.2f} \n"
                        else:
                            speed_comment = f"# 状态: 有效，但无法测速 \n"
                else:
                    # 如果没有测速结果，使用传统验证方法
                    is_valid = test_url_speed(test_url)[0]
                    if is_valid:
                        valid_channels.append((channel_name, proxied_url))

                if is_valid:
                    processed_lines.append(f"{channel_name},{proxied_url}\n")
                    if speed_comment:
                        processed_lines.append(speed_comment)
        # 处理GitHub源建议中的直接URL行
        elif line.startswith('https://raw.githubusercontent.com/'):
            proxied_url = f"https://ghfast.top/{line}"

            # 添加带有前缀的URL
            processed_lines.append(proxied_url + '\n')

            # 添加测速结果注释
            if SPEED_TEST_CONFIG['speed_test_enabled'] and proxied_url in speed_results:
                result = speed_results[proxied_url]
                if result['valid']:
                    valid_channels.append(("GitHub源建议", proxied_url))
                    if result['speed_info']:
                        speed_kbps = result['speed_info']['speed_kbps']
                        stability = result['speed_info']['stability']
                        processed_lines.append(f"# 速度: {speed_kbps:.1f} KB/s, 稳定性: {stability:.2f}\n")
                    else:
                        processed_lines.append(f"# 状态: 有效，但无法测速\n")
                else:
                    processed_lines.append(f"# 状态: 无效\n")
        # 保留其他行
        else:
            processed_lines.append(line + '\n')

    # 更新频道数量
    for i, line in enumerate(processed_lines):
        if line.startswith('# 共包含'):
            processed_lines[i] = f"# 共包含 {len(valid_channels)} 个4K超高清频道\n"
            break

    # 按URL速度对频道进行排序（如果启用了测速）
    if SPEED_TEST_CONFIG['speed_test_enabled']:
        # 这里可以实现更复杂的排序逻辑
        # 为简化实现，我们保持原有的顺序，但在注释中显示速度信息

    return processed_lines

# 主函数
def main():

    start_time = time.time()

    # 读取文件内容
    lines = read_file()

    # 处理4K频道，验证URL并更新时间戳
    processed_lines = process_uhd_channels(lines)

    # 写入处理后的内容
    write_file(processed_lines)

    total_time = time.time() - start_time

    # 显示统计信息
    valid_count = 0
    for line in processed_lines:
        if ',' in line and not line.startswith('#'):
            valid_count += 1

# 测试脚本
if __name__ == "__main__":
    main()
