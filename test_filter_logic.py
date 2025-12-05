# 测试购物频道和测试URL过滤逻辑

# 实现过滤函数
def should_exclude_channel(channel_name):
    """检查是否应该排除购物频道"""
    # 排除购物相关频道
    shopping_keywords = ['购物', '导购', '电视购物']
    for keyword in shopping_keywords:
        if keyword in channel_name:
            return True
    return False

def should_exclude_url(url):
    """检查是否应该排除测试URL"""
    # 排除测试URL
    test_url_keywords = ['example.com', 'demo', 'sample']
    for keyword in test_url_keywords:
        if keyword in url:
            return True
    return False

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
print("=== 测试购物频道和测试URL过滤逻辑 ===")

print("\n1. 购物频道过滤测试:")
for channel in channels_to_test:
    excluded = should_exclude_channel(channel)
    print(f"  {channel}: {'排除' if excluded else '保留'}")

print("\n2. 测试URL过滤测试:")
for url in urls_to_test:
    excluded = should_exclude_url(url)
    print(f"  {url}: {'排除' if excluded else '保留'}")

print("\n=== 测试完成 ===")
