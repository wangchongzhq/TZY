# 检查频道名称规范化

import re

# 模拟从IPTV.py中提取的normalize_channel_name函数和CHANNEL_MAPPING
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

# 模拟normalize_channel_name函数的实现
def normalize_channel_name(channel_name):
    if not channel_name:
        return channel_name
    
    # 移除多余空格
    name = channel_name.strip()
    
    # 替换特殊字符和分隔符
    name = re.sub(r'[\s_\-\.]+', ' ', name)
    
    # 去除多余空格
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 去除常见的前缀后缀
    prefixes = [r'[\s\[\(]*(高清|HD|标清|SD|超清|蓝光)[\s\]\)]*', r'[\s\[\(]*(直播)[\s\]\)]*']
    for prefix in prefixes:
        name = re.sub(r'^' + prefix, '', name, flags=re.IGNORECASE)
        name = re.sub(r'' + prefix + '$', '', name, flags=re.IGNORECASE)
    
    # 去除多余空格
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 使用反向映射
    result = ALIAS_TO_STANDARD.get(name, name)
    
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
    normalized = normalize_channel_name(name)
    print(f"'{name}' -> '{normalized}'")

# 检查output/iptv.txt中的内容
print("\n=== 检查output/iptv.txt中的频道名称 ===")

try:
    with open('output/iptv.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 收集频道名称
    channel_names = []
    for line in lines:
        if line.strip():
            # 分割频道名称和URL
            name_url = line.split(',', 1)
            if len(name_url) == 2:
                channel_names.append(name_url[0])
    
    print(f"共找到 {len(channel_names)} 个频道")
    
    # 检查特定频道
    check_channels = ['北京卫视', '湖南卫视', 'CCTV4']
    for check_name in check_channels:
        found = [name for name in channel_names if check_name in name]
        if found:
            print(f"\n找到 {len(found)} 个与 '{check_name}' 相关的频道:")
            for name in found[:10]:  # 只显示前10个
                print(f"  - {name}")
        else:
            print(f"\n未找到与 '{check_name}' 相关的频道")
            
except Exception as e:
    print(f"读取文件时出错: {e}")
