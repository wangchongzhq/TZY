import sys
import os
import importlib.util

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 动态导入IP-TV模块
print("正在导入IP-TV模块...")
try:
    spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
    ip_tv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ip_tv)
    print("成功导入IP-TV模块")
except Exception as e:
    print(f"导入IP-TV模块失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 调用update_iptv_sources函数
print("\n开始执行update_iptv_sources函数...")
try:
    result = ip_tv.update_iptv_sources()
    print(f"\n函数返回值: {result}")
    print("执行完成")
except Exception as e:
    print(f"\n执行过程中发生错误: {e}")
    import traceback
    traceback.print_exc()