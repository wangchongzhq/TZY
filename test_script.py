# 简单的测试脚本
import sys
import os
print("=== 测试脚本开始 ===")
print("Python版本:", sys.version)
print("当前目录:", os.getcwd())
print("文件列表:", os.listdir(".")[:5])  # 只显示前5个文件

# 测试文件读取
try:
    with open('get_cgq_sources.py', 'r', encoding='utf-8') as f:
        content = f.read()
    print("文件读取成功，行数:", len(content.split('\n')))
    print("前100个字符:", content[:100])
except Exception as e:
    print("文件读取失败:", e)

print("=== 测试脚本结束 ===")
