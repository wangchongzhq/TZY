import os
import re

def find_file_references(directory):
    # 正则表达式匹配文件名引用
    pattern = re.compile(r"['"]([\w.-]+\.(txt|m3u|json|py))['"]")
    
    # 存储所有引用的文件名
    file_references = set()
    
    # 遍历目录中的所有.py文件
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for match in matches:
                            file_references.add(match[0])
                except:
                    pass
    
    return file_references

def check_files_exist(file_list, directory):
    missing_files = []
    for file_name in file_list:
        file_path = os.path.join(directory, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
    
    return missing_files

if __name__ == "__main__":
    directory = os.getcwd()
    print(f"正在检查目录: {directory}")
    
    # 查找所有文件引用
    file_references = find_file_references(directory)
    print(f"找到 {len(file_references)} 个文件引用")
    
    # 检查这些文件是否存在
    missing_files = check_files_exist(file_references, directory)
    
    if missing_files:
        print(f"发现 {len(missing_files)} 个缺失文件:")
        for file in missing_files:
            print(f"- {file}")
    else:
        print("所有引用的文件都存在")
