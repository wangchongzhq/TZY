#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os

def check_4k_channels():
    print("=== 检查生成的M3U文件中的4K频道 ===")
    
    # 检查文件是否存在，支持新旧文件名
    m3u_file = "jieguo.m3u"
    if not os.path.exists(m3u_file):
        # 尝试使用新的文件名
        m3u_file = "ip-tv.m3u"
        if not os.path.exists(m3u_file):
            print("❌ 未找到 jieguo.m3u 或 ip-tv.m3u 文件")
            return
        
    print(f"✅ 找到 {m3u_file} 文件")
    print(f"📁 文件大小: {os.path.getsize(m3u_file)} 字节")
    
    # 读取文件内容
    try:
        with open(m3u_file, "r", encoding="utf-8") as f:
            content = f.read()
        print("✅ 成功读取文件内容")
    except Exception as e:
        print(f"❌ 读取文件失败: {str(e)}")
        return
    
    print("\n=== 搜索4K频道分类 ===")
    
    # 更简单的方法来处理频道信息
    lines = content.split('\n')
    group_4k_channels = []
    name_4k_channels = []
    groups = set()
    
    # 遍历所有行
    for i in range(len(lines)):
        if lines[i].startswith('#EXTINF:-1'):
            line = lines[i]
            # 提取group-title
            group_match = re.search(r'group-title="([^"]+)"', line)
            if group_match:
                group_title = group_match.group(1)
                groups.add(group_title)
                
                # 提取频道名称
                name_match = re.search(r',([^\n]+)$', line)
                if name_match:
                    channel_name = name_match.group(1)
                    # 获取URL
                    if i+1 < len(lines):
                        url = lines[i+1]
                        
                        # 检查是否属于4K频道分类
                        if group_title == "4K频道":
                            group_4k_channels.append((channel_name, url))
                        
                        # 检查名称是否包含4K
                        if "4K" in channel_name or "UHD" in channel_name:
                            name_4k_channels.append((channel_name, group_title, url))
    
    print(f"📊 找到 {len(groups)} 个分类")
    
    if group_4k_channels:
        print("✅ 找到'4K频道'分类")
        print(f"📺 4K频道数量: {len(group_4k_channels)}")
        print(f"📋 前50个4K频道:")
        for i, (channel_name, url) in enumerate(group_4k_channels[:50]):
            print(f"  {i+1}. {channel_name}")
        if len(group_4k_channels) > 50:
            print(f"  ... 还有 {len(group_4k_channels) - 50} 个4K频道")
    else:
        print("❌ 未找到'4K频道'分类")
    
    print("\n=== 搜索名称包含4K的频道 ===")
    
    if name_4k_channels:
        print(f"✅ 找到 {len(name_4k_channels)} 个名称包含4K的频道")
        print("📋 名称包含4K的频道（显示频道名称和分类）:")
        for i, (channel_name, group_title, url) in enumerate(name_4k_channels[:50]):
            print(f"  {i+1}. '{channel_name}' -> 分类: '{group_title}'")
        if len(name_4k_channels) > 50:
            print(f"  ... 还有 {len(name_4k_channels) - 50} 个类似频道")
    else:
        print("❌ 未找到名称包含4K的频道")
    
    # 搜索特定的4K频道
    print("\n=== 搜索用户提到的特定4K频道 ===")
    target_channels = ['北京卫视4K', '浙江卫视4K', '东方卫视4K', '山东卫视4K', '湖南卫视4K', '江苏卫视4K']
    found_targets = []
    
    for channel_name, url in group_4k_channels:
        for target in target_channels:
            if target in channel_name:
                found_targets.append((channel_name, url))
    
    if found_targets:
        print(f"✅ 找到 {len(found_targets)} 个用户提到的4K频道:")
        for channel_name, url in found_targets:
            print(f"  - {channel_name} -> {url[:100]}...")
    else:
        print("❌ 未找到用户提到的4K频道")
    
    print("\n=== 检查完成 ===")

if __name__ == "__main__":
    check_4k_channels()
