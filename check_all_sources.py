import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的函数
from collect_ipzy import collect_from_source, standardize_channel_name
from unified_sources import SOURCES_WITH_NAMES

# 测试所有数据源
for name, url in SOURCES_WITH_NAMES:
    print(f"\n\n=== 测试数据源: {name} ===")
    print(f"URL: {url}")
    
    try:
        source = {"name": name, "url": url}
        channels = collect_from_source(source)
        print(f"收集到的频道数: {len(channels)}")
        
        # 查找CCTV频道
        cctv_channels = [ch for ch in channels if 'CCTV' in ch['name']]
        print(f"CCTV频道数: {len(cctv_channels)}")
        
        # 标准化并去重
        cctv_names = set()
        for ch in cctv_channels:
            std_name = standardize_channel_name(ch['name'])
            cctv_names.add(std_name)
        
        if cctv_names:
            print(f"不同的CCTV频道 ({len(cctv_names)}个):")
            for std_name in sorted(cctv_names):
                print(f"  - {std_name}")
        
    except Exception as e:
        print(f"错误: {e}")
        # 只打印简单错误，不打印完整堆栈