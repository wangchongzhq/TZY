import sys
import os
from collections import defaultdict

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的函数
from core.network import fetch_content
from core.channel_utils import normalize_channel_name
from core.parser import parse_m3u_content, parse_txt_content

# 从统一播放源文件导入
try:
    from unified_sources import SOURCES_WITH_NAMES
    print(f"✅ 成功从unified_sources.py导入 {len(SOURCES_WITH_NAMES)} 个播放源")
except ImportError as e:
    print(f"❌ 导入unified_sources.py失败: {e}")
    # 如果导入失败，使用一些默认的播放源
    SOURCES_WITH_NAMES = [
        ("小皮直播", "https://gitee.com/xiao-ping2/iptv-api/raw/master/output/xp_result.txt"),
        ("国V直播", "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt")
    ]
    print(f"⚠️ 使用默认播放源列表，共 {len(SOURCES_WITH_NAMES)} 个播放源")

# 替代collect_from_source的函数
def collect_from_source(source):
    """从源URL收集频道信息"""
    url = source['url']
    content = fetch_content(url)
    if not content:
        return []
    
    # 尝试解析为M3U格式
    try:
        channels = parse_m3u_content(content)
        if channels:
            # 转换为与原函数兼容的格式
            return [{'name': ch.name, 'url': ch.url, 'category': ch.group} for ch in channels]
    except Exception:
        pass
    
    # 尝试解析为TXT格式
    try:
        channels = parse_txt_content(content)
        if channels:
            # 转换为与原函数兼容的格式
            return [{'name': ch.name, 'url': ch.url, 'category': ch.group} for ch in channels]
    except Exception:
        pass
    
    # 手动解析简单的TXT格式（频道名,URL）
    try:
        channels = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                if ',' in line:
                    name, url = line.split(',', 1)
                    channels.append({
                        'name': name.strip(),
                        'url': url.strip(),
                        'category': None
                    })
        return channels
    except Exception:
        pass
    
    return []

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
            std_name = normalize_channel_name(ch['name'])
            cctv_names.add(std_name)
        
        if cctv_names:
            print(f"不同的CCTV频道 ({len(cctv_names)}个):")
            for std_name in sorted(cctv_names):
                print(f"  - {std_name}")
        
    except Exception as e:
        print(f"错误: {e}")
        # 只打印简单错误，不打印完整堆栈