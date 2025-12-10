import os
import re

def find_file_references(directory):
    # 正则表达式匹配文件名引用（支持包含路径）
    pattern = re.compile(r'["\']([\w./\\-]+\.(txt|m3u|json|py))["\']')
    
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
    
    # 检查文件是否存在的辅助函数
    def file_exists(file_name):
        # 直接检查路径
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            return True
        
        # 如果文件名不包含路径，检查是否在某个子目录下存在
        if '/' not in file_name and '\\' not in file_name:
            for root, dirs, files in os.walk(directory):
                if file_name in files:
                    return True
        
        return False
    
    for file_name in file_list:
        if not file_exists(file_name):
            missing_files.append(file_name)
    
    return missing_files

if __name__ == "__main__":
    directory = os.getcwd()
    print(f"正在检查目录: {directory}")
    
    # 查找所有文件引用
    file_references = find_file_references(directory)
    print(f"找到 {len(file_references)} 个文件引用")
    # 打印所有检测到的文件引用
    print("检测到的文件引用:")
    for file in sorted(file_references):
        print(f"  - {file}")
    
    # 检查这些文件是否存在
    missing_files = check_files_exist(file_references, directory)
    
    if missing_files:
        print(f"发现 {len(missing_files)} 个缺失文件:")
        for file in missing_files:
            print(f"- {file}")
    else:
        print("所有引用的文件都存在")
