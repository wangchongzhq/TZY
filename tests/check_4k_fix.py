import re

def check_4k_fix():
    file_path = "c:/Users/Administrator/Documents/GitHub/TZY/output/iptv_ipv4.m3u"
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()
    
    # 查找所有4K频道
    pattern = r'#EXTINF:.*?group-title="4K频道".*?,(.*?)\n(.*?)\n'
    matches = re.findall(pattern, content, re.DOTALL)
    
    wrong_count = 0
    for channel_name, url in matches[:20]:  # 只检查前20个
        # 检查频道名称是否包含4K关键词
        has_4k_keyword = any(keyword in channel_name.lower() for keyword in ['4k', '8k', '超高清', '2160'])
        if not has_4k_keyword:
            wrong_count += 1
            print(f"错误分类: {channel_name}, URL: {url}")
    
    print(f"\n前20个4K频道中，有{wrong_count}个错误分类（名称不含4K关键词）")

if __name__ == "__main__":
    check_4k_fix()