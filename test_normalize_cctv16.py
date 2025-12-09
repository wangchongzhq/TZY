import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入需要的函数
from IP-TV import normalize_channel_name

# 测试不同格式的CCTV16频道名称
test_cases = [
    "CCTV16",
    "CCTV16 4K",
    "CCTV16(4K)",
    "CCTV16 (4K)",
    "CCTV16-4K",
    "CCTV16奥林匹克 4K",
    "CCTV16 奧林匹克 4K",
    "CCTV16(奥林匹克4K)",
]

print("=== 测试normalize_channel_name函数对CCTV16的处理 ===")
for test_name in test_cases:
    normalized = normalize_channel_name(test_name)
    print(f"原始名称: {test_name} -> 规范化后: {normalized}")

print("\n=== 测试完成 ===")
