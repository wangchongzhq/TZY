#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单脚本用于处理4K_uhd_channels.txt文件
限制raw.githubusercontent.com域名下相同用户名/仓库名组合的URL数量不超过5个
"""

import re
import os

# 使用绝对路径
FILE_PATH = os.path.abspath('4K_uhd_channels.txt')
print(f"处理文件: {FILE_PATH}")
print(f"文件存在: {os.path.exists(FILE_PATH)}")

# 读取文件内容
try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"读取成功，共 {len(lines)} 行")
except Exception as e:
    print(f"读取文件错误: {e}")
    exit(1)

# 处理GitHub URL
header = []
github_urls = []
footer = []
in_github_section = False
repo_counter = {}

for line in lines:
    line_strip = line.strip()
    
    # 检查是否进入GitHub URL部分
    if '# 建议添加到get_cgq_sources.py的LIVE_SOURCES列表中的GitHub直播源URL：' in line:
        print("进入GitHub URL部分")
        in_github_section = True
        header.append(line)
    elif in_github_section:
        # 检查是否是GitHub URL
        if line_strip.startswith('# ') and 'raw.githubusercontent.com' in line_strip:
            # 提取用户名/仓库名组合
            match = re.search(r'raw\.githubusercontent\.com/([^/]+/[^/]+)/', line_strip)
            if match:
                repo = match.group(1)
                print(f"找到URL: {line_strip} -> 仓库: {repo}")
                
                # 计数
                if repo not in repo_counter:
                    repo_counter[repo] = 0
                
                if repo_counter[repo] < 5:
                    github_urls.append(line)
                    repo_counter[repo] += 1
                    print(f"  保留（计数: {repo_counter[repo]}/5）")
                else:
                    print(f"  跳过（已达上限5个）")
            else:
                github_urls.append(line)
                print(f"  非标准URL，保留: {line_strip}")
        elif line_strip == '':
            print("GitHub URL部分结束")
            in_github_section = False
            footer.append(line)
        else:
            header.append(line)
            print(f"  添加到头部: {line_strip}")
    else:
        header.append(line)

# 合并结果
result = header + github_urls + footer
print(f"处理完成，结果共 {len(result)} 行")
print("仓库统计:")
for repo, count in repo_counter.items():
    print(f"- {repo}: {count} 个URL")

# 写入文件
try:
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines(result)
    print("文件写入成功！")
except Exception as e:
    print(f"写入文件错误: {e}")
    exit(1)

print("任务完成！")