# 检查频道名称规范化修复效果

# 检查output/iptv.txt中的内容
print("=== 检查output/iptv.txt中的频道名称 ===")

# 读取文件内容
try:
    with open('output/iptv.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 收集频道名称
    channel_names = []
    for line in lines:
        if line.strip():
            # 分割频道名称和URL
            name_url = line.split(',', 1)
            if len(name_url) == 2:
                channel_names.append(name_url[0])
    
    # 检查特定频道
    check_channels = ['北京卫视', '湖南卫视', 'CCTV4']
    print(f"共找到 {len(channel_names)} 个频道")
    
    print("\n=== 查找特定频道 ===")
    for check_name in check_channels:
        found = [name for name in channel_names if check_name in name]
        if found:
            print(f"找到 {len(found)} 个与 '{check_name}' 相关的频道:")
            for name in found[:10]:  # 只显示前10个
                print(f"  - {name}")
        else:
            print(f"未找到与 '{check_name}' 相关的频道")
    
    # 检查频道名称规范化情况
    print("\n=== 检查频道名称规范化 ===")
    # 查找包含"卫视"但不是标准名称的频道
    卫视_channels = [name for name in channel_names if '卫视' in name and not any(standard in name for standard in ['北京卫视', '湖南卫视', '江苏卫视', '浙江卫视', '东方卫视', '广东卫视', '深圳卫视'])]
    if 卫视_channels:
        print("可能未正确规范化的卫视频道:")
        for name in 卫视_channels[:20]:
            print(f"  - {name}")
    else:
        print("卫视频道规范化良好")
        
    # 查找CCTV频道
    cctv_channels = [name for name in channel_names if name.startswith('CCTV')]
    print(f"\n找到 {len(cctv_channels)} 个CCTV频道，前20个:")
    for name in cctv_channels[:20]:
        print(f"  - {name}")
        
    # 检查4K频道
    print("\n=== 检查4K频道 ===")
    # 读取output/iptv.m3u文件查找4K频道
    try:
        with open('output/iptv.m3u', 'r', encoding='utf-8') as f:
            m3u_content = f.read()
        
        # 查找4K频道部分
        import re
        category_pattern = re.compile(r'#EXTINF:-1 tvg-id=\".*?\" tvg-name=\".*?\" tvg-logo=\".*?\" group-title=\"(.*?)\",(.*?)\n(.*?)\n', re.DOTALL)
        matches = category_pattern.findall(m3u_content)
        
        category_map = {}
        for match in matches:
            category = match[0]
            channel_name = match[1]
            url = match[2]
            if category not in category_map:
                category_map[category] = []
            category_map[category].append((channel_name, url))
        
        if '4K频道' in category_map:
            print(f"4K频道分类中有 {len(category_map['4K频道'])} 个频道")
            print("前20个4K频道:")
            for channel_name, url in category_map['4K频道'][:20]:
                print(f"  - {channel_name}")
        else:
            print("未找到4K频道分类")
            
    except Exception as e:
        print(f"读取m3u文件时出错: {e}")
        
except Exception as e:
    print(f"读取文件时出错: {e}")
