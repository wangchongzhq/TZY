import os
import sys
import re
from validator.iptv_validator import IPTVValidator

# 设置测试文件路径
test_file_path = r"C:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"

# 确保文件存在
if not os.path.exists(test_file_path):
    print(f"测试文件不存在: {test_file_path}")
    sys.exit(1)

print(f"开始测试文件解析: {test_file_path}")

# 创建验证器实例
validator = IPTVValidator(test_file_path, debug=True)

# 测试文件类型检测
print(f"\n1. 文件类型检测:")
print(f"   文件类型: {validator.file_type}")

# 手动测试文件解析（不使用验证器的read_txt_file方法，避免处理外部URL）
print(f"\n2. 手动解析测试:")
try:
    with open(test_file_path, 'rb') as f:
        content = f.read()
    
    # 检测编码
    try:
        content_str = content.decode('utf-8-sig')
        print(f"   编码: UTF-8")
    except UnicodeDecodeError:
        try:
            content_str = content.decode('gbk')
            print(f"   编码: GBK")
        except UnicodeDecodeError:
            content_str = content.decode('latin-1')
            print(f"   编码: Latin-1")
    
    lines = content_str.splitlines()
    print(f"   总行数: {len(lines)}")
    
    # 手动解析
    channels = []
    categories = []
    current_category = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过注释
        if line.startswith('//') or (line.startswith('#') and '#genre#' not in line):
            continue
        
        # 检测分类
        category_match = re.search(r'([^,]+),#genre#', line)
        if category_match:
            current_category = category_match.group(1).strip()
            if current_category not in categories:
                categories.append(current_category)
            continue
        
        # 解析频道
        if ',' in line:
            try:
                # 使用URL模式查找
                url_pattern = r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)'
                url_match = re.search(url_pattern, line)
                if url_match:
                    url_start = url_match.start()
                    name = line[:url_start].rstrip(',').strip()
                    url = line[url_start:].strip().strip('`')
                else:
                    name, url = line.rsplit(',', 1)
                    name = name.strip()
                    url = url.strip().strip('`')
                
                if name and url:
                    channels.append({
                        'name': name,
                        'url': url,
                        'category': current_category if current_category else '未分类'
                    })
            except:
                continue
    
    print(f"   找到分类: {len(categories)}")
    print(f"   找到频道: {len(channels)}")
    print(f"   分类列表: {categories}")
    
    # 打印前10个频道
    print(f"\n   前10个频道:")
    for i, channel in enumerate(channels[:10]):
        print(f"   {i+1}. {channel['name']} -> {channel['url']} (分类: {channel['category']})")
        
except Exception as e:
    print(f"   解析失败: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print(f"\n测试完成!")
