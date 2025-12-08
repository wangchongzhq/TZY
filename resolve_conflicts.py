# 解决ipzyauto.txt文件中的Git冲突
# 保留HEAD中的内容，删除冲突标记

def resolve_conflicts(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有冲突块，保留HEAD内容
    import re
    # 匹配冲突模式：<<<<<<< HEAD\ncontent\n=======\nother_content\n>>>>>>> commit_hash
    pattern = r'<<<<<<< HEAD\n(.*?)\n=======.*?\n>>>>>>> [0-9a-f]+'
    resolved_content = re.sub(pattern, r'\1', content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(resolved_content)
    
    print(f"已解决{file_path}中的所有冲突")

if __name__ == "__main__":
    resolve_conflicts(r"c:\Users\Administrator\Documents\GitHub\TZY\ipzyauto.txt")