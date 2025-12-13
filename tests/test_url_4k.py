import re

# 手动实现我们的修复逻辑
def fix_channel_name(channel_name, url):
    # 检查名称或URL中是否包含4K标识
    has_4k_in_name = ("4K" in channel_name or "4k" in channel_name or 
                      "8K" in channel_name or "8k" in channel_name)
    has_4k_in_url = ("4K" in url or "4k" in url or 
                     "8K" in url or "8k" in url)
    
    processed_name = channel_name
    if has_4k_in_url and not has_4k_in_name:
        if re.match(r'^CCTV\d+$', channel_name):
            if "cctv4k" in url.lower():
                processed_name = "CCTV4K"
            elif "cctv8k" in url.lower():
                processed_name = "CCTV8K"
            elif "4k" in url.lower():
                processed_name = f"{channel_name}-4K"
            elif "8k" in url.lower():
                processed_name = f"{channel_name}-8K"
    
    return processed_name

# 测试用例
def test_fix_channel_name():
    test_cases = [
        # 测试用例1: CCTV4频道，URL包含cctv4k
        ("CCTV4", "http://aiony.top:35455/nptv/cctv4k.m3u8"),
        # 测试用例2: CCTV8频道，URL包含cctv8k
        ("CCTV8", "http://aiony.top:35455/nptv/cctv8k.m3u8"),
        # 测试用例3: CCTV1频道，URL包含4k
        ("CCTV1", "http://example.com/cctv1_4k.m3u8"),
        # 测试用例4: CCTV5频道，URL包含8k
        ("CCTV5", "http://example.com/cctv5_8k.m3u8"),
        # 测试用例5: CCTV4K，名称直接包含4K
        ("CCTV4K", "http://example.com/cctv4k.m3u8"),
    ]
    
    print("测试URL中4K标识的修复逻辑:")
    print("=" * 60)
    
    for channel_name, url in test_cases:
        processed_name = fix_channel_name(channel_name, url)
        print(f"原始频道名: {channel_name}")
        print(f"URL: {url}")
        print(f"修复后的频道名: {processed_name}")
        print("-" * 60)

if __name__ == "__main__":
    test_fix_channel_name()