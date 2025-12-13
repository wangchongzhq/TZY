import re
import chardet

def extract_4k_channels(filename):
    """测试从temp_live.txt提取4K频道"""
    # 读取文件内容并检测编码
    with open(filename, 'rb') as f:
        raw_content = f.read()
    detected_encoding = chardet.detect(raw_content)['encoding']
    print(f"检测到的文件编码: {detected_encoding}")
    
    # 解码文件内容
    content = raw_content.decode(detected_encoding, errors='replace')
    lines = content.split('\n')
    
    # 提取4K频道
    fourk_channels = []
    
    for line in lines:
        line = line.strip()
        if not line or '#' in line:
            continue
        
        # 检查是否包含4K相关标识
        if re.search(r'(4K|4k|8K|8k|超高清|2160)', line):
            # 分割频道名和URL
            parts = line.split(',', 1)
            if len(parts) >= 2:
                channel_name, channel_url = parts[0].strip(), parts[1].strip()
                fourk_channels.append((channel_name, channel_url))
    
    return fourk_channels

# 运行测试
channels = extract_4k_channels('temp_live.txt')
print(f"\n从temp_live.txt提取到的4K频道数量: {len(channels)}")
print("\n前10个4K频道:")
for i, (name, url) in enumerate(channels[:10]):
    print(f"{i+1}. {name} -> {url}")
