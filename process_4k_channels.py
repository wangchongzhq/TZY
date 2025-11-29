import os
import sys
import time
import requests
from urllib.request import urlopen, Request

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# 验证URL是否有效
def validate_url(url, timeout=10):
    """验证URL是否可以访问，返回是否有效"""
    try:
        print(f"验证URL: {url}")
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if status_code == 200:
                print(f"URL有效: {url}")
                return True
            else:
                print(f"URL返回状态码: {status_code}, {url}")
                return False
    except Exception as e:
        print(f"URL验证失败: {str(e)}, {url}")
        return False

# 读取文件内容
def read_file():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)

# 写入文件内容
def write_file(lines):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"写入文件时出错: {e}")
        sys.exit(1)

# 处理4K频道URL，验证并更新
def process_uhd_channels(lines):
    """处理4K频道列表，验证URL有效性并更新时间戳"""
    processed_lines = []
    valid_channels = []
    current_section = None
    
    # 更新文件头部信息
    processed_lines.append("# 4K超高清直播源列表\n")
    processed_lines.append(f"# 更新时间: {time.strftime('%Y-%m-%d')}\n")
    
    for line in lines:
        line = line.strip()
        
        # 保留注释行和空行
        if line.startswith('#') or not line:
            processed_lines.append(line + '\n')
            
            # 检查是否为新的分类
            if line.startswith('# 4K'):
                current_section = line
        # 处理频道行（格式：频道名称,URL）
        elif ',' in line:
            parts = line.split(',')
            if len(parts) >= 2:
                channel_name = parts[0].strip()
                url = parts[1].strip()
                
                # 验证URL
                if validate_url(url):
                    valid_channels.append((channel_name, url))
                    processed_lines.append(f"{channel_name},{url}\n")
    
    # 更新频道数量
    for i, line in enumerate(processed_lines):
        if line.startswith('# 共包含'):
            processed_lines[i] = f"# 共包含 {len(valid_channels)} 个4K超高清频道\n"
            break
    
    print(f"验证完成，有效频道数量: {len(valid_channels)}")
    return processed_lines

# 主函数
def main():
    print(f"开始处理文件: {FILE_PATH}")
    
    # 读取文件内容
    lines = read_file()
    print(f"读取到 {len(lines)} 行内容")
    
    # 处理4K频道，验证URL并更新时间戳
    processed_lines = process_uhd_channels(lines)
    
    # 写入处理后的内容
    if write_file(processed_lines):
        print(f"文件处理完成: {FILE_PATH}")
        print(f"更新时间已设置为: {time.strftime('%Y-%m-%d')}")
        print(f"URL验证完成，移除了无效的URL")

if __name__ == "__main__":
    main()