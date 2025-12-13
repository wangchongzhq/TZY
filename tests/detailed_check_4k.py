def detailed_check_4k():
    """详细检查4K频道分类情况"""
    file_path = "c:/Users/Administrator/Documents/GitHub/TZY/output/iptv_ipv4.m3u"
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()
    
    # 分离文件内容为行
    lines = content.split('\n')
    
    total_channels = 0
    total_4k_channels = 0
    correct_4k_channels = 0
    wrong_4k_channels = 0
    wrong_4k_list = []
    
    i = 0
    while i < len(lines):
        if lines[i].startswith('#EXTINF:'):
            total_channels += 1
            
            # 查找下一个非空行作为URL
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            
            if j < len(lines) and (lines[j].startswith('http://') or lines[j].startswith('https://')):
                # 检查是否为4K频道
                if 'group-title="4K频道"' in lines[i]:
                    total_4k_channels += 1
                    
                    # 提取频道名称
                    channel_info = lines[i]
                    channel_name = channel_info.split(',')[-1].strip()
                    
                    # 检查频道名称是否包含4K关键词
                    has_4k_keyword = any(keyword in channel_name.lower() for keyword in ['4k', '8k', '超高清', '2160'])
                    
                    if has_4k_keyword:
                        correct_4k_channels += 1
                    else:
                        wrong_4k_channels += 1
                        wrong_4k_list.append((channel_name, lines[j].strip()))
            
            # 移动到下一个频道
            i = j + 1
        else:
            i += 1
    
    # 输出统计结果
    print("4K频道分类详细检查结果：")
    print("=" * 50)
    print(f"总频道数: {total_channels}")
    print(f"4K频道总数: {total_4k_channels}")
    print(f"正确分类的4K频道数: {correct_4k_channels}")
    print(f"错误分类的4K频道数: {wrong_4k_channels}")
    
    # 输出前几个错误分类的频道
    if wrong_4k_list:
        print(f"\n前{min(10, len(wrong_4k_list))}个错误分类的4K频道：")
        for i, (channel_name, url) in enumerate(wrong_4k_list[:10]):
            print(f"{i+1}. {channel_name}")
            print(f"   URL: {url[:100]}..." if len(url) > 100 else f"   URL: {url}")
            print()
    else:
        print("\n恭喜！没有发现错误分类的4K频道。")

if __name__ == "__main__":
    detailed_check_4k()