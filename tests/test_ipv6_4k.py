# 简单测试IPv6 4K频道分类

# 模拟is_ipv6函数
def is_ipv6(url):
    return '[' in url

# 测试数据
test_channels = [
    ("CCTV4K超高清", "http://[2409:8087:1e01:23::10]:8112/4k/cctv4k.m3u8"),
    ("Shenzhen Satellite TV (2160p)", "http://[2409:8087:1e01:23::10]:8112/4k/shenzhen.m3u8"),
    ("CCTV1", "http://[2409:8087:1e01:23::10]:8112/cctv1.m3u8"),
]

print("测试IPv6 4K频道分类逻辑")
print("=" * 50)

for channel_name, url in test_channels:
    is_ipv6_flag = is_ipv6(url)
    if ("4K" in channel_name or "4k" in channel_name or 
        "8K" in channel_name or "8k" in channel_name or
        "超高清" in channel_name or "2160" in channel_name):
        print(f"✓ 4K频道: {channel_name} ({'IPv6' if is_ipv6_flag else 'IPv4'}) - {url}")
    else:
        print(f"✗ 普通频道: {channel_name} ({'IPv6' if is_ipv6_flag else 'IPv4'}) - {url}")

print("\n测试完成")
