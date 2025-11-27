# 简单的脚本用于处理4K_uhd_channels.txt中的GitHub直播源URL
# 限制每个用户名/仓库名组合的URL数量不超过5个

import re

# 定义文件路径
file_path = '4K_uhd_channels.txt'

# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 分割内容为行
lines = content.split('\n')

# 存储结果
result_lines = []

# 跟踪每个仓库的URL数量
repo_counts = {}

# 标记是否在GitHub URL部分
in_github_section = False

# 处理每一行
for line in lines:
    # 检查是否进入GitHub URL部分
    if '# 建议添加到get_cgq_sources.py的LIVE_SOURCES列表中的GitHub直播源URL：' in line:
        in_github_section = True
        result_lines.append(line)
    elif in_github_section:
        # 检查是否是GitHub URL行
        if line.strip() and line.startswith('# '):
            # 查找GitHub URL模式
            match = re.search(r'https://raw\.githubusercontent\.com/([^/]+/[^/]+)/', line)
            if match:
                repo = match.group(1)  # 提取用户名/仓库名组合
                
                # 初始化或更新计数
                if repo not in repo_counts:
                    repo_counts[repo] = 0
                
                # 如果计数小于5，保留该行
                if repo_counts[repo] < 5:
                    result_lines.append(line)
                    repo_counts[repo] += 1
                    print(f"保留: {line.strip()}")
                else:
                    print(f"跳过: {line.strip()}")
            else:
                # 不是GitHub URL，直接添加
                result_lines.append(line)
        elif line.strip() == '':
            # 遇到空行，结束GitHub URL部分
            in_github_section = False
            result_lines.append(line)
        else:
            # 其他行，直接添加
            result_lines.append(line)
    else:
        # 不在GitHub URL部分，直接添加
        result_lines.append(line)

# 合并结果行
result_content = '\n'.join(result_lines)

# 写入文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(result_content)

print("\n处理完成！")
print("仓库计数统计：")
for repo, count in repo_counts.items():
    print(f"- {repo}: {count} 个URL")
