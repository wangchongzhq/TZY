# 测试频道名称规范化

import re
import sys

# 模拟CHANNEL_MAPPING和ALIAS_TO_STANDARD
CHANNEL_MAPPING = {
    "北京卫视": ["北京卫视 HD", "北京台", "北京卫视高清"],
    "湖南卫视": ["湖南卫视 HD", "湖南台", "湖南卫视高清"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4 中文国际", "CCTV-4 中文国际"],
}

# 创建反向映射
ALIAS_TO_STANDARD = {}
for standard_name, aliases in CHANNEL_MAPPING.items():
    ALIAS_TO_STANDARD[standard_name] = standard_name
    for alias in aliases:
        ALIAS_TO_STANDARD[alias] = standard_name

# 模拟normalize_channel_name函数的关键部分
def test_normalize(name):
    if not name:
        return None
    
    original_name = name
    
    # 去除前后空格
    name = name.strip()
    
    # 替换常见的特殊字符和分隔符
    name = re.sub(r'[\s_\-\.]+', ' ', name)
    
    # 去除多余的空格
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 去除常见的前缀后缀
    prefixes = [r'[\s\[\(]*(高清|HD|标清|SD|超清|蓝光)[\s\]\)]*', r'[\s\[\(]*(直播)[\s\]\)]*']
    for prefix in prefixes:
        name = re.sub(r'^' + prefix, '', name, flags=re.IGNORECASE)
        name = re.sub(r'' + prefix + '$', '', name, flags=re.IGNORECASE)
    
    # 去除多余的空格
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 使用反向映射
    result = ALIAS_TO_STANDARD.get(name, name)
    
    print(f"'{original_name}' -> '{name}' -> '{result}'")
    return result

# 测试各种频道名称
print("=== 测试频道名称规范化 ===")
test_names = [
    "北京卫视",
    "北京卫视 HD",
    "北京台",
    "北京卫视高清",
    "湖南卫视",
    "湖南卫视 HD",
    "湖南台",
    "湖南卫视高清",
    "CCTV4",
    "CCTV-4",
    "CCTV-4 HD",
    "CCTV4 中文国际",
    # 测试可能的问题格式
    "北京卫视-HD",
    "北京卫视_HD",
    "北京卫视.HD",
    "湖南卫视-HD",
    "湖南卫视_HD",
    "湖南卫视.HD",
    # 测试带空格的情况
    " 北京卫视 HD  ",
    " 湖南卫视 HD  ",
]

for name in test_names:
    test_normalize(name)

# 打印ALIAS_TO_STANDARD的内容
print("\n=== ALIAS_TO_STANDARD映射 ===")
for alias, standard in sorted(ALIAS_TO_STANDARD.items()):
    print(f"'{alias}' -> '{standard}'")
