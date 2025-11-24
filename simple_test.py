# 简化的测试脚本，直接验证低分辨率过滤功能

# 模拟主脚本中的低分辨率检测逻辑
def is_low_resolution(line, channel_name):
    """判断是否为低分辨率线路
    识别并过滤576p等低分辨率线路
    """
    line_lower = line.lower()
    name_lower = channel_name.lower()
    
    # 明确标记的低分辨率
    if '576p' in line_lower or '576p' in name_lower:
        print(f"过滤576p线路: {channel_name}")
        return True
    
    # 其他低分辨率标记
    if '标清' in line or '标清' in channel_name:
        print(f"过滤标清线路: {channel_name}")
        return True
    
    # 明确的低质量标记
    if 'sd' in line_lower or '480p' in line_lower:
        print(f"过滤SD/480p线路: {channel_name}")
        return True
    
    print(f"保留线路: {channel_name}")
    return False

# 测试用例
test_cases = [
    ("http://example.com/hls/25/index.m3u8", "甘肃卫视 (576p)"),
    ("http://example.com/gitv/live1/G_GUIZHOU/G_GUIZHOU", "贵州卫视 (576p)"),
    ("http://example.com/hd/cctv1.m3u8", "CCTV1 高清"),
    ("http://example.com/sd/cctv2.m3u8", "CCTV2"),
    ("http://example.com/4k/cctv4k.m3u8", "CCTV 4K"),
    ("http://example.com/channel/btv1080p.m3u8", "北京卫视 1080p"),
    ("http://example.com/channel/stv_sd.m3u8", "山东卫视 标清")
]

print("=== 开始测试低分辨率过滤功能 ===")
for url, channel in test_cases:
    is_low = is_low_resolution(url, channel)
    print(f"测试结果: {channel}, 低分辨率: {is_low}\n")

print("=== 测试完成 ===")
