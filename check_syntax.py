#!/usr/bin/env python3
"""
检查所有Python文件的语法错误
"""
import os
import py_compile
import glob

def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try:
        py_compile.compile(file_path, doraise=True)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """主函数"""
    print("🔍 开始检查所有Python文件的语法...")
    
    # 获取所有Python文件
    python_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"📁 找到 {len(python_files)} 个Python文件")
    
    errors = []
    success_count = 0
    
    for file_path in sorted(python_files):
        print(f"  🔎 检查: {file_path}")
        is_valid, error = check_file_syntax(file_path)
        
        if is_valid:
            print(f"    ✅ 语法正确")
            success_count += 1
        else:
            print(f"    ❌ 语法错误: {error}")
            errors.append((file_path, error))
    
    print(f"\n📊 检查结果:")
    print(f"  ✅ 语法正确的文件: {success_count}")
    print(f"  ❌ 语法错误的文件: {len(errors)}")
    
    if errors:
        print(f"\n🚨 发现语法错误:")
        for file_path, error in errors:
            print(f"  📄 {file_path}: {error}")
        return False
    else:
        print(f"\n🎉 所有文件语法正确!")
        return True

if __name__ == "__main__":
    main()