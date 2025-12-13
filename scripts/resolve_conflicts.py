# 解决所有Git冲突文件
# 保留HEAD中的内容，删除冲突标记

import os
import re

# 导入核心模块
from core import file_exists, read_file, write_file

def resolve_conflicts(file_path):
    """解决单个文件中的Git冲突"""
    if not file_exists(file_path):
        print(f"文件不存在: {file_path}")
        return
        
    content = read_file(file_path)
    if not content:
        print(f"无法读取文件: {file_path}")
        return
    
    # 替换所有冲突块，保留HEAD内容
    # 匹配冲突模式：
    # 1. 标准格式：<<<<<<< HEAD\ncontent\n=======\nother_content\n>>>>>>> commit_hash
    # 2. 特殊格式：<<<<<<< HEAD:filename\ncontent\n=======\nother_content\n>>>>>>> commit_hash
    pattern = r'<<<<<<< HEAD(?::.*?)?\n(.*?)\n=======.*?\n>>>>>>> [0-9a-f]+'
    resolved_content = re.sub(pattern, r'\1', content, flags=re.DOTALL)
    
    if write_file(file_path, resolved_content):
        print(f"已解决{file_path}中的所有冲突")
    else:
        print(f"无法写入文件: {file_path}")

if __name__ == "__main__":
    # 冲突文件列表
    conflict_files = [
        "ipzyauto.m3u"
    ]
    
    # 项目根目录
    root_dir = r"c:\Users\Administrator\Documents\GitHub\TZY"
    
    # 解决所有冲突文件
    for file_name in conflict_files:
        file_path = os.path.join(root_dir, file_name)
        resolve_conflicts(file_path)
    
    print("所有冲突文件已处理完成！")