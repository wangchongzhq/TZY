import os
import sys
import time
import requests
import re

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# 验证URL是否有效
def validate_url(url, timeout=10):
    """使用requests库验证URL是否可以访问，返回是否有效"""
    try:
        # 对GitHub原始文件URL添加ghfast.top前缀
        if url.startswith('https://raw.githubusercontent.com/'):
            proxied_url = f"https://ghfast.top/{url}"
            response = requests.get(proxied_url, headers=HEADERS, timeout=15, stream=True)
        else:
            response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        
        # 只检查响应头，不下载整个内容
        response.close()
        
        return response.status_code == 200
    except:
        return False

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
    """处理4K频道列表，验证URL有效性并更新时间戳"""
    processed_lines = []
    valid_channels = []
    github_sources_section = False
    channel_section = False
    
    # 添加文件头部信息（只添加一次）
    processed_lines.append("# 4K超高清直播源列表\n")
    processed_lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d')}\n")
    processed_lines.append(f"# 共包含 0 个4K超高清频道\n")
    processed_lines.append("\n")
    
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
                # 提取URL并添加前缀
                match = re.search(r'(# \d+\.) (https://raw\.githubusercontent\.com/.+)', line)
                if match:
                    prefix = match.group(1)
                    url = match.group(2)
                    # 添加ghfast.top前缀
                    proxied_url = f"https://ghfast.top/{url}"
                    # 无论验证结果如何，都将带有前缀的URL写入文件
                    processed_lines.append(f"{prefix} {proxied_url}\n")
                    # 验证带有前缀的URL，只有验证通过才计入有效频道
                    if validate_url(proxied_url):
                        valid_channels.append((f"GitHub源建议", proxied_url))
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
                    # 无论验证结果如何，都将带有前缀的URL写入文件
                    processed_lines.append(f"{channel_name},{proxied_url}\n")
                    # 验证带有前缀的URL，只有验证通过才计入有效频道
                    if validate_url(proxied_url):
                        valid_channels.append((channel_name, proxied_url))
                else:
                    # 验证原始URL
                    if validate_url(url):
                        valid_channels.append((channel_name, url))
                        processed_lines.append(f"{channel_name},{url}\n")
        # 处理GitHub源建议中的直接URL行
        elif line.startswith('https://raw.githubusercontent.com/'):
            # 为直接URL添加前缀
            proxied_url = f"https://ghfast.top/{line}"
            # 无论验证结果如何，都将带有前缀的URL写入文件
            processed_lines.append(proxied_url + '\n')
            # 验证带有前缀的URL，只有验证通过才计入有效频道
            if validate_url(proxied_url):
                valid_channels.append((f"GitHub源建议", proxied_url))
        # 保留其他行
        else:
            processed_lines.append(line + '\n')
    
    # 更新频道数量
    for i, line in enumerate(processed_lines):
        if line.startswith('# 共包含'):
            processed_lines[i] = f"# 共包含 {len(valid_channels)} 个4K超高清频道\n"
            break
    
    return processed_lines

# 主函数
def main():
    print("🚀 4K直播源处理工具启动")
    
    # 读取文件内容
    lines = read_file()
    
    # 处理4K频道，验证URL并更新时间戳
    processed_lines = process_uhd_channels(lines)
    
    # 写入处理后的内容
    write_file(processed_lines)
    
    print("\n🏆 4K频道处理任务完成！")

# 测试脚本
if __name__ == "__main__":
    main()
