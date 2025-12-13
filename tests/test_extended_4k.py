# 测试扩展后的4K频道识别逻辑
from collections import defaultdict

# 模拟get_channel_category函数的修复后逻辑
def get_channel_category(channel_name):
    """获取频道所属的分类"""
    # 首先检查是否包含4K/8K/超高清/2160数字，如果包含则直接归类为4K频道
    if ('4K' in channel_name or '4k' in channel_name or 
        '8K' in channel_name or '8k' in channel_name or
        '超高清' in channel_name or '2160' in channel_name):
        return "4K频道"
    # 默认返回其他频道
    return "其他频道"

# 模拟extract_channels_from_txt函数的修复后逻辑
def extract_channels_from_txt(file_path):
    """从本地TXT文件提取频道信息"""
    channels = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 跳过格式不正确的分组标题行（如"4K频道,#genre#"）
                if line.endswith(',#genre#') or line.endswith(',genre#'):
                    continue
                
                # 解析频道信息（格式：频道名称,URL）
                if ',' in line:
                    channel_name, url = line.split(',', 1)
                    channel_name = channel_name.strip()
                    url = url.strip()
                    
                    # 跳过无效的URL
                    if not url.startswith(('http://', 'https://')):
                        continue
                    
                    # 这里简化处理，直接检查频道名
                    # 检查频道名是否包含4K/8K/超高清/2160数字
                    if ("4K" in channel_name or "4k" in channel_name or 
                        "8K" in channel_name or "8k" in channel_name or
                        "超高清" in channel_name or "2160" in channel_name):
                        channels["4K频道"].append((channel_name, url))
                    else:
                        # 不含4K的频道放在其他频道
                        channels["其他频道"].append((channel_name, url))
    except Exception as e:
        print(f"解析本地文件 {file_path} 时出错: {e}")
    
    return channels

# 测试get_channel_category函数
print("=== 测试get_channel_category函数 ===")
test_cases = [
    "CCTV4K",
    "cctv4k",
    "CCTV8K",
    "cctv8k",
    "CCTV超高清",
    "CCTV-2160",
    "深圳卫视超高清",
    "北京卫视8K",
    "东方卫视2160",
    "普通频道"
]

for channel_name in test_cases:
    category = get_channel_category(channel_name)
    print(f"频道: {channel_name} -> 分类: {category}")

# 测试extract_channels_from_txt函数（模拟数据）
print("\n=== 测试extract_channels_from_txt函数 ===")

# 创建一个临时测试文件
test_content = """
# 测试直播源
CCTV4K,http://example.com/cctv4k.m3u8
cctv4k,http://example.com/cctv4k_lower.m3u8
CCTV8K,http://example.com/cctv8k.m3u8
cctv8k,http://example.com/cctv8k_lower.m3u8
CCTV超高清,http://example.com/cctv_hd.m3u8
CCTV-2160,http://example.com/cctv_2160.m3u8
深圳卫视超高清,http://example.com/sz_hd.m3u8
北京卫视8K,http://example.com/bj_8k.m3u8
东方卫视2160,http://example.com/df_2160.m3u8
普通频道,http://example.com/normal.m3u8
"""

with open("test_extended_4k.txt", "w", encoding="utf-8") as f:
    f.write(test_content)

# 测试函数
channels = extract_channels_from_txt("test_extended_4k.txt")

# 打印结果
for category, channel_list in channels.items():
    print(f"\n分类: {category} ({len(channel_list)}个频道)")
    for channel_name, url in channel_list:
        print(f"  - {channel_name}")

# 清理临时文件
import os
os.remove("test_extended_4k.txt")

print("\n=== 测试完成 ===")
