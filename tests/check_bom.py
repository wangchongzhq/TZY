#!/usr/bin/env python3
"""
检查Python文件中的BOM字符
"""

import os
import glob

def has_bom(file_path):
    """检查文件是否有BOM字符"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read(3)  # 读取前3个字节
        return content == b'\xef\xbb\xbf'
    except Exception as e:
        print(f"❌ 检查 {file_path} 时出错: {e}")
        return False

# 检查所有Python文件
def main():
    print("开始检查Python文件中的BOM字符...")
    
    # 获取所有Python文件
    python_files = glob.glob('*.py') + glob.glob('scripts/*.py') + glob.glob('core/*.py')
    
    files_with_bom = []
    files_without_bom = []
    
    for file_path in python_files:
        if has_bom(file_path):
            files_with_bom.append(file_path)
        else:
            files_without_bom.append(file_path)
    
    print(f"\n检查结果:")
    print(f"总Python文件数: {len(python_files)}")
    
    if files_with_bom:
        print(f"\n❌ 包含BOM字符的文件 ({len(files_with_bom)}个):")
        for file in files_with_bom:
            print(f"  - {file}")
    else:
        print(f"\n✅ 没有发现包含BOM字符的Python文件")
    
    if files_without_bom:
        print(f"\n✅ 不包含BOM字符的文件 ({len(files_without_bom)}个):")
        for file in files_without_bom:
            print(f"  - {file}")
    
    print("\n检查完成！")

if __name__ == "__main__":
    main()