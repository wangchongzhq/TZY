# 使用绝对路径直接修复4K_uhd_channels.txt文件

import os

# 获取脚本所在目录的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, '4K_uhd_channels.txt')

print(f"正在处理文件: {file_path}")

# 读取原始文件内容
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"成功读取文件，共 {len(lines)} 行")
except Exception as e:
    print(f"读取文件时出错: {e}")
    exit(1)

# 分离文件内容：头部（4K频道部分）和GitHub URL部分
header_lines = []
github_lines = []
header_done = False

for line in lines:
    stripped_line = line.strip()
    if not header_done:
        header_lines.append(line)
        # 当遇到GitHub URL建议的开始标记时，开始收集GitHub URL
        if '# 建议添加到get_cgq_sources.py的LIVE_SOURCES列表中的GitHub直播源URL：' in line:
            header_done = True
    else:
        github_lines.append(line)

print(f"头部行数: {len(header_lines)}")
print(f"GitHub URL行数: {len(github_lines)}")

# 过滤GitHub URL，限制每个仓库不超过5个
filtered_github_urls = []
repo_count = {}

for line in github_lines:
    # 跳过空行和注释行（不是GitHub URL的行）
    if not line.strip() or 'https://raw.githubusercontent.com' not in line:
        filtered_github_urls.append(line)
        continue
    
    # 提取仓库信息
    url = line.strip()
    if '//raw.githubusercontent.com/' in url:
        # 提取仓库路径部分
        repo_part = url.split('//raw.githubusercontent.com/')[1]
        if '/' in repo_part:
            # 提取用户名/仓库名组合
            repo_name = repo_part.split('/')[0] + '/' + repo_part.split('/')[1]
            
            # 初始化计数器
            if repo_name not in repo_count:
                repo_count[repo_name] = 0
            
            # 只保留前5个
            if repo_count[repo_name] < 5:
                filtered_github_urls.append(line)
                repo_count[repo_name] += 1
            else:
                print(f"跳过 {repo_name} 的URL: {url}")

# 合并头部和过滤后的GitHub URL
new_content = ''.join(header_lines) + ''.join(filtered_github_urls)

# 写入新内容
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"成功写入文件，新文件共 {len(new_content.splitlines())} 行")
    print("\n仓库URL统计:")
    for repo, count in repo_count.items():
        print(f"- {repo}: {count} 个URL")
except Exception as e:
    print(f"写入文件时出错: {e}")
    exit(1)

print("\n处理完成！所有GitHub仓库的URL数量都已限制在5个以内。")
