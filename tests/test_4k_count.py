import os
import re

def count_4k_channels():
    # 检查iptv.m3u文件
    file_path = r'C:\Users\Administrator\Documents\GitHub\TZY\output\iptv.m3u'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== 测试4K频道识别 ===")
    
    # 1. 查找所有包含4K的行
    all_4k_lines = re.findall(r'^.*4K.*$', content, re.IGNORECASE | re.MULTILINE)
    print(f"\n1. 所有包含4K的行数: {len(all_4k_lines)}")
    
    # 2. 查找所有EXTINF行
    all_extinf_lines = re.findall(r'^#EXTINF:-1.*$', content, re.MULTILINE)
    print(f"2. 所有EXTINF行数量: {len(all_extinf_lines)}")
    
    # 3. 查找所有4K相关的EXTINF行
    all_4k_extinf_lines = []
    for line in all_extinf_lines:
        if '4K' in line or '4k' in line:
            all_4k_extinf_lines.append(line)
    print(f"3. 所有包含4K的EXTINF行数量: {len(all_4k_extinf_lines)}")
    
    # 4. 检查group-title
    in_4k_channel = []
    in_other_channel = []
    
    for line in all_4k_extinf_lines:
        if 'group-title="4K频道"' in line:
            in_4k_channel.append(line)
        else:
            in_other_channel.append(line)
    
    print(f"4. 在4K频道组的4K频道数量: {len(in_4k_channel)}")
    print(f"5. 在其他频道组的4K频道数量: {len(in_other_channel)}")
    
    # 6. 显示在其他频道组的4K频道
    if in_other_channel:
        print("\n6. 在其他频道组的4K频道:")
        for line in in_other_channel[:10]:  # 只显示前10个
            print(f"   {line}")
    
    # 7. 检查正则表达式匹配
    print("\n7. 正则表达式测试:")
    pattern = r'#EXTINF:-1 group-title="(?!4K频道)[^"]*",[^,]*4K[^,]*'
    regex_matches = re.findall(pattern, content, re.IGNORECASE)
    print(f"   正则表达式匹配到的数量: {len(regex_matches)}")
    
    if regex_matches:
        print("   前5个匹配:")
        for match in regex_matches[:5]:
            print(f"   {match}")

if __name__ == "__main__":
    count_4k_channels()