# 测试购物频道过滤功能

# 导入所需的过滤函数
import sys
import os

# 将当前目录添加到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试数据
channels_to_test = [
    "CCTV1",
    "CCTV中视购物",
    "CDTV8购物",
    "湖南卫视",
    "南方购物",
    "内蒙古购物",
    "浙江卫视",
    "家有购物",
    "时尚购物",
    "东方卫视"
]

urls_to_test = [
    "http://example.com/channel1",
    "http://demo.com/channel2",
    "http://sample.com/channel3",
    "http://tv.example.com/channel4",
    "http://valid.com/channel5",
    "http://test.com/channel6"
]

# 测试过滤逻辑
print("=== 测试购物频道过滤功能 ===")

# 测试 IP-TV.py 中的过滤函数
print("\n1. 测试 IP-TV.py 中的过滤函数:")
try:
    import IP-TV
    for channel in channels_to_test:
        excluded = IP-TV.should_exclude_channel(channel)
        print(f"  {channel}: {'排除' if excluded else '保留'}")
    for url in urls_to_test:
        excluded = IP-TV.should_exclude_url(url)
        print(f"  {url}: {'排除' if excluded else '保留'}")
except ImportError:
    print("  无法导入 IP-TV.py")

# 测试 tvzy.py 中的过滤函数
print("\n2. 测试 tvzy.py 中的过滤函数:")
try:
    import tvzy
    for channel in channels_to_test:
        excluded = tvzy.should_exclude_channel(channel)
        print(f"  {channel}: {'排除' if excluded else '保留'}")
    for url in urls_to_test:
        excluded = tvzy.should_exclude_url(url)
        print(f"  {url}: {'排除' if excluded else '保留'}")
except ImportError:
    print("  无法导入 tvzy.py")

# 测试 ipzyauto.py 中的过滤函数
print("\n3. 测试 ipzyauto.py 中的过滤函数:")
try:
    import ipzyauto
    for channel in channels_to_test:
        excluded = ipzyauto.should_exclude_channel(channel)
        print(f"  {channel}: {'排除' if excluded else '保留'}")
    for url in urls_to_test:
        excluded = ipzyauto.should_exclude_url(url)
        print(f"  {url}: {'排除' if excluded else '保留'}")
except ImportError:
    print("  无法导入 ipzyauto.py")

print("\n=== 测试完成 ===")
