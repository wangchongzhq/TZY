# 简单测试脚本，验证修复后的CCTV4K/CCTV8K频道识别

# 模拟M3U文件内容
m3u_content = '''#EXTINF:-1 tvg-id="cctv4" tvg-name="CCTV4" tvg-logo="http://example.com/logo.png" group-title="央视",CCTV4
http://example.com/cctv4k.m3u8
#EXTINF:-1 tvg-id="cctv8" tvg-name="CCTV8" tvg-logo="http://example.com/logo.png" group-title="央视",CCTV8
http://example.com/cctv8k.m3u8
#EXTINF:-1 tvg-id="cctv1" tvg-name="CCTV1" tvg-logo="http://example.com/logo.png" group-title="央视",CCTV1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="cctv5" tvg-name="CCTV5" tvg-logo="http://example.com/logo.png" group-title="央视",CCTV5
http://example.com/cctv5_4k.m3u8
#EXTINF:-1 tvg-id="cctv4k" tvg-name="CCTV4K" tvg-logo="http://example.com/logo.png" group-title="央视",CCTV4K
http://example.com/cctv4k.m3u8
'''

# 从IPTV.py导入函数
import sys
import os

# 设置工作目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入所需函数
from IPTV import extract_channels_from_m3u

# 测试函数
def test_cctv_4k_8k():
    print("测试CCTV4K/CCTV8K频道识别:")
    print("=" * 50)
    
    # 调用函数解析M3U内容
    channels_dict = extract_channels_from_m3u(m3u_content)
    
    # 打印4K频道
    if "4K频道" in channels_dict:
        print("识别到的4K频道:")
        print("-" * 50)
        for channel in channels_dict["4K频道"]:
            name, url = channel
            print(f"频道名: {name}")
            print(f"URL: {url}")
            print("-" * 50)
    
    # 打印其他频道
    print("识别到的其他频道:")
    print("-" * 50)
    for category, channels in channels_dict.items():
        if category != "4K频道":
            for channel in channels:
                name, url = channel
                print(f"分类: {category}")
                print(f"频道名: {name}")
                print(f"URL: {url}")
                print("-" * 50)

# 运行测试
if __name__ == "__main__":
    test_cctv_4k_8k()
