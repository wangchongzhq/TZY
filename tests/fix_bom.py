#!/usr/bin/env python3
"""
修复文件中的BOM字符
"""

import os

def fix_file_bom(file_path):
    """修复单个文件中的BOM字符"""
    try:
        # 以二进制模式读取文件
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 检查是否有BOM字符
        if content.startswith(b'\xef\xbb\xbf'):
            # 移除BOM字符并解码为UTF-8
            content = content[3:].decode('utf-8')
            
            # 重新写入文件，不添加BOM
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修复 {file_path} 中的BOM字符")
        else:
            print(f"ℹ️  {file_path} 没有BOM字符")
        
        return True
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        return False

# 修复所有需要处理的文件
if __name__ == "__main__":
    files_to_fix = [
        'ipzyauto.py',
        'IP-TV.py',
        'unified_sources.py'
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fix_file_bom(file_path)
        else:
            print(f"❌ 找不到文件: {file_path}")
    
    print("\n🎉 所有文件修复完成！")