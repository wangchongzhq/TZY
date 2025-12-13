# 测试CCTV-4和4K频道的规范化

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入normalize_channel_name函数
from IPTV import normalize_channel_name

# 测试CCTV-4的各种格式
print("=== 测试CCTV-4的规范化 ===")
cctv4_test_cases = [
    "CCTV4",
    "CCTV-4",
    "CCTV 4",
    "CCTV-4 HD",
    "CCTV4 中文国际",
    "CCTV-4 中文国际",
]

for test_case in cctv4_test_cases:
    normalized = normalize_channel_name(test_case)
    print(f"'{test_case}' -> '{normalized}'")

# 测试4K频道的规范化
print("\n=== 测试4K频道的规范化 ===")
fourk_test_cases = [
    "北京卫视",
    "北京卫视4K",
    "北京卫视 4K",
    "北京卫视-4K",
    "湖南卫视",
    "湖南卫视4K",
    "湖南卫视 4K",
    "湖南卫视-4K",
]

for test_case in fourk_test_cases:
    normalized = normalize_channel_name(test_case)
    print(f"'{test_case}' -> '{normalized}'")

# 检查4K频道是否被正确分类
print("\n=== 检查4K频道分类 ===")

# 读取output/iptv.txt文件，检查4K频道
if os.path.exists("output/iptv.txt"):
    fourk_channels = []
    with open("output/iptv.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "4K" in line:
                fourk_channels.append(line)
    
    print(f"共找到 {len(fourk_channels)} 个4K频道")
    if len(fourk_channels) > 0:
        print("\n部分4K频道示例：")
        for channel in fourk_channels[:10]:
            print(f"  - {channel}")
else:
    print("output/iptv.txt文件不存在，请先运行IPTV.py")
