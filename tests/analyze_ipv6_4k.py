# 分析当前生成的IPv6文件中的4K频道情况
import os

# 读取IPv6文件
txt_file = "output/iptv_ipv6.txt"
m3u_file = "output/iptv_ipv6.m3u"

print("分析IPv6文件中的4K频道情况")
print("=" * 50)

# 检查TXT文件
if os.path.exists(txt_file):
    print(f"\n1. 分析TXT文件: {txt_file}")
    with open(txt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含4K频道分类
    if "4K频道" in content or "4K棰戦亾" in content:
        print("   ✓ 找到4K频道分类")
    else:
        print("   ✗ 未找到4K频道分类")
    
    # 检查是否有实际的4K频道
    lines = content.split('\n')
    found_4k_channels = False
    in_4k_section = False
    
    for line in lines:
        line = line.strip()
        if line.startswith("#4K频道#") or line.startswith("#4K棰戦亾#"):
            in_4k_section = True
            print("   检查4K频道部分:")
            continue
        elif line.startswith("#") and ",genre#" in line:
            in_4k_section = False
        
        if in_4k_section and line and not line.startswith("#"):
            # 这是一个频道行
            print(f"      - {line}")
            found_4k_channels = True
    
    if found_4k_channels:
        print("   ✓ 找到实际的4K频道")
    else:
        print("   ✗ 未找到实际的4K频道")
    
    # 检查所有频道中是否有包含4K标识的频道
    print("\n   检查所有频道中是否有包含4K相关标识的频道:")
    found_4k_identifier = False
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "," in line:
            channel_name = line.split(',')[0]
            if any(keyword in channel_name for keyword in ["4K", "4k", "8K", "8k", "超高清", "2160"]):
                print(f"      - '{channel_name}' 包含4K标识")
                found_4k_identifier = True
    
    if not found_4k_identifier:
        print("   ✗ 没有找到包含4K标识的频道")

# 检查M3U文件
if os.path.exists(m3u_file):
    print(f"\n2. 分析M3U文件: {m3u_file}")
    with open(m3u_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有4K频道
    if "group-title=\"4K频道\"" in content:
        print("   ✓ 找到4K频道分组")
        # 计算4K频道数量
        4k_count = content.count("group-title=\"4K频道\"")
        print(f"   ✓ 共有 {4k_count} 个4K频道")
    else:
        print("   ✗ 未找到4K频道分组")

print("\n=" * 50)
print("分析完成")
