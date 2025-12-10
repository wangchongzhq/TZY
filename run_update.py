import sys
import os

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 导入IP-TV模块
print("正在导入IP-TV模块...")

# 动态导入IP-TV.py
import importlib.util
spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
ip_tv = importlib.util.module_from_spec(spec)
sys.modules["ip_tv"] = ip_tv
spec.loader.exec_module(ip_tv)

print("\n开始运行update_iptv_sources函数...")
print("=" * 60)

# 运行函数
result = ip_tv.update_iptv_sources()

print("\n" + "=" * 60)
print(f"函数返回结果: {result}")
print("" * 60)

# 检查生成的文件
print("\n检查生成的文件:")
print("-" * 40)

# 检查当前目录
files = os.listdir(".")
for file in files:
    if file.startswith('jieguo'):
        file_path = os.path.join(".", file)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        print(f"  {file} - {file_size} 字节")

print("\n运行完成")