import re
from collections import defaultdict

# 复制过滤函数
def should_exclude_channel(name):
    """检查是否应该排除某个频道"""
    # 排除购物相关频道
    shopping_keywords = ['购物', '导购', '电视购物']
    for keyword in shopping_keywords:
        if keyword in name:
            return True
    return False

def should_exclude_url(url):
    """检查是否应该排除某个URL"""
    # 排除测试频道URL
    exclude_patterns = [
        r'^http://example',
        r'^https://example',
        r'demo',
        r'sample',
        r'samples'
    ]
    
    for pattern in exclude_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

# 测试购物频道过滤
test_channels = [
    "CCTV1",
    "CCTV中视购物",
    "CDTV8购物",
    "南方购物",
    "内蒙古购物",
    "浙江卫视",
    "家有购物",
    "时尚购物"
]

print("=== 测试购物频道过滤 ===")
for channel in test_channels:
    excluded = should_exclude_channel(channel)
    print(f"频道: {channel} -> {'排除' if excluded else '保留'}")

# 测试URL过滤
test_urls = [
    "http://example.com/test.m3u8",
    "https://example.org/stream",
    "http://demo.example.com/video",
    "https://test.com/sample.m3u8",
    "http://cdn.com/channel.m3u8",
    "https://tv.com/live/samples/stream.m3u8"
]

print("\n=== 测试URL过滤 ===")
for url in test_urls:
    excluded = should_exclude_url(url)
    print(f"URL: {url} -> {'排除' if excluded else '保留'}")

# 测试解析流程
def test_parse_flow():
    print("\n=== 测试解析流程 ===")
    
    # 模拟M3U内容
    test_m3u = [
        "#EXTM3U",
        "#EXTINF:-1,CCTV1",
        "http://cdn.com/cctv1.m3u8",
        "#EXTINF:-1,CCTV中视购物",
        "http://example.com/shopping.m3u8",
        "#EXTINF:-1,浙江卫视",
        "http://cdn.com/zjws.m3u8"
    ]
    
    channels_dict = defaultdict(list)
    current_name = None
    
    for i, line in enumerate(test_m3u):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("#EXTINF"):
            if "," in line:
                current_name = line.split(",")[-1].strip()
                print(f"找到M3U频道: {current_name}")
            if i + 1 < len(test_m3u):
                url = test_m3u[i + 1].strip()
                print(f"找到URL: {url}")
                if url.startswith("http://") or url.startswith("https://"):
                    # 过滤购物频道
                    if should_exclude_channel(current_name):
                        print(f"排除购物频道: {current_name}")
                    # 过滤测试URL
                    elif should_exclude_url(url):
                        print(f"排除测试URL: {url}")
                    else:
                        print(f"添加到字典: {current_name} -> {url}")
                        channels_dict[current_name].append(url)
            current_name = None
    
    print(f"\n最终频道列表: {list(channels_dict.keys())}")

test_parse_flow()