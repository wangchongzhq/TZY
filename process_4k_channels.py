import re
import os
import sys

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

def print_debug(message):
    """打印调试信息"""
    print(f"[DEBUG] {message}")

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

# 处理GitHub直播源URL
def process_github_urls(lines):
    # 用于存储处理后的内容
    result_lines = []  # 最终结果
    github_urls = []   # GitHub URL列表
    in_github_section = False
    
    # 用于跟踪每个用户名/仓库名组合的URL数量
    repo_counts = {}
    
    # 定义GitHub URL的正则表达式
    github_regex = r'^#\s*\d+\.\s*(https://raw.githubusercontent.com/([^/]+/[^/]+)/.+)$'
    
    # 遍历文件内容
    for line in lines:
        if '# 建议添加到get_cgq_sources.py的LIVE_SOURCES列表中的GitHub直播源URL：' in line:
            print_debug("进入GitHub URL部分")
            in_github_section = True
            result_lines.append(line)
        elif in_github_section:
            if line.startswith('# 以下是至少50个GitHub直播源URL建议：'):
                result_lines.append(line)
            # 检查是否是GitHub URL行
            elif line.strip() and line.startswith('# '):
                match = re.match(github_regex, line)
                if match:
                    url = match.group(1)
                    repo = match.group(2)  # 提取用户名/仓库名组合
                    
                    print_debug(f"找到GitHub URL: {url}, 仓库: {repo}")
                    
                    # 初始化仓库计数器
                    if repo not in repo_counts:
                        repo_counts[repo] = 0
                    
                    # 如果该仓库的URL数量小于5，保留这个URL
                    if repo_counts[repo] < 5:
                        github_urls.append(line)
                        repo_counts[repo] += 1
                        print_debug(f"保留URL，当前计数: {repo_counts[repo]}")
                    else:
                        print_debug(f"跳过URL，已达到最大计数5")
            elif line.strip() == '':
                # 如果遇到空行，说明GitHub URL部分结束
                print_debug("GitHub URL部分结束")
                in_github_section = False
                # 将处理后的GitHub URL添加到结果中
                result_lines.extend(github_urls)
                result_lines.append(line)
        else:
            # 添加非GitHub URL部分的内容
            result_lines.append(line)
    
    return result_lines

# 主函数
def main():
    print(f"开始处理文件: {FILE_PATH}")
    
    # 读取文件内容
    lines = read_file()
    print_debug(f"读取到 {len(lines)} 行内容")
    
    # 处理GitHub URL
    processed_lines = process_github_urls(lines)
    print_debug(f"处理后剩余 {len(processed_lines)} 行内容")
    
    # 写入处理后的内容
    if write_file(processed_lines):
        print(f"文件处理完成: {FILE_PATH}")
        print("已确保相同用户名/仓库名组合的GitHub直播源URL不超过5个。")

if __name__ == "__main__":
    main()