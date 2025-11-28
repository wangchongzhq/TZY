import os
import sys

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

# 读取文件内容
def read_file():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)

# 写入文件内容
def write_file(lines):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"写入文件时出错: {e}")
        sys.exit(1)

# 主函数
def main():
    print(f"开始处理文件: {FILE_PATH}")
    
    # 读取文件内容
    lines = read_file()
    print(f"读取到 {len(lines)} 行内容")
    
    # 写入处理后的内容
    if write_file(lines):
        print(f"文件处理完成: {FILE_PATH}")

if __name__ == "__main__":
    main()