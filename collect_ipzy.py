import requests
import re
from datetime import datetime
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 定义多个数据源
SOURCES = [
    {"name": "iptv-org-cn", "url": "https://iptv-org.github.io/iptv/countries/cn.m3u"},
    {"name": "iptv-org-hk", "url": "https://iptv-org.github.io/iptv/countries/hk.m3u"},
    {"name": "iptv-org-mo", "url": "https://iptv-org.github.io/iptv/countries/mo.m3u"},
    {"name": "iptv-org-tw", "url": "https://iptv-org.github.io/iptv/countries/tw.m3u"},
    {"name": "iptv-org-backup", "url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"},
    {"name": "fanmingming", "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u"},
]

# 分类规则
CATEGORY_RULES = {
    "央视": [
        r'CCTV', r'中央电视台', r'CGTN', r'央视'
    ],
    "卫视": [
        r'卫视', r'湖南卫视', r'浙江卫视', r'东方卫视', r'北京卫视', r'江苏卫视',
        r'安徽卫视', r'重庆卫视', r'东南卫视', r'甘肃卫视', r'广东卫视',
        r'广西卫视', r'贵州卫视', r'海南卫视', r'河北卫视', r'黑龙江卫视',
        r'河南卫视', r'湖北卫视', r'江西卫视', r'吉林卫视', r'辽宁卫视',
        r'山东卫视', r'深圳卫视', r'四川卫视', r'天津卫视', r'云南卫视'
    ],
    "港澳台": [
        r'凤凰', r'TVB', r'翡翠', r'明珠', r'本港', r'国际', r'澳视', r'澳门',
        r'华视', r'中视', r'台视', r'民视', r'三立', r'东森', r'星空', r'香港',
        r'澳門', r'台灣', r'台湾'
    ],
    "影视剧": [
        r'电影', r'剧场', r'影院', r'影视', r'剧集', r'MOVIE', r'DRAMA',
        r'CHC', r'黑莓', r'好莱坞', r'华语电影', r'家庭影院'
    ],
    "4K": [
        r'4K', r'4k', r'UHD', r'超高清', r'2160P', r'2160p'
    ],
    "音乐": [
        r'音乐', r'MUSIC', r'MTV', r'流行音乐', r'经典音乐', r'音乐台',
        r'风云音乐', r'卡拉OK'
    ]
}

# 高清关键词
HD_KEYWORDS = [
    r'1080', r'1080p', r'1080P', r'高清', r'HD', r'High Definition', 
    r'FHD', r'Full HD', r'超清', r'4K', r'4k', r'UHD', r'2160'
]

def download_m3u(url, retries=3):
    """下载M3U文件"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"下载失败 {url} (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)
    return None

def normalize_channel_name(name):
    """标准化频道名称"""
    name = re.sub(r'\s+', ' ', name.strip())
    
    replacements = {
        r'CCTV-1\s*综合': 'CCTV-1',
        r'CCTV-1HD': 'CCTV-1',
        r'CCTV1': 'CCTV-1',
        r'CCTV-2\s*财经': 'CCTV-2',
        r'CCTV2': 'CCTV-2',
        r'湖南卫视HD': '湖南卫视',
        r'浙江卫视HD': '浙江卫视',
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name)
    
    return name

def is_hd_channel(channel_info):
    """判断是否为高清频道"""
    name = channel_info.get('name', '').lower()
    tvg_name = channel_info.get('tvg_name', '').lower()
    group = channel_info.get('group', '').lower()
    
    for keyword in HD_KEYWORDS:
        if (keyword.lower() in name or 
            keyword.lower() in tvg_name or 
            keyword.lower() in group):
            return True
    
    return False

def parse_m3u_content(content, source_name):
    """解析M3U内容"""
    if not content:
        return {}
    
    lines = content.split('\n')
    channels = {}
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            current_channel = parse_extinf_line(line, source_name)
        elif line.startswith('http'):
            if current_channel:
                current_channel['url'] = line
                
                if is_hd_channel(current_channel):
                    channel_name = normalize_channel_name(current_channel['name'])
                    
                    if channel_name not in channels:
                        channels[channel_name] = {
                            'name': channel_name,
                            'tvg_name': current_channel.get('tvg_name', channel_name),
                            'group': current_channel.get('group', '默认分组'),
                            'logo': current_channel.get('logo', ''),
                            'urls': [],
                            'sources': set()
                        }
                    
                    if line not in channels[channel_name]['urls']:
                        channels[channel_name]['urls'].append(line)
                        channels[channel_name]['sources'].add(source_name)
                
                current_channel = {}
    
    return channels

def parse_extinf_line(line, source_name):
    """解析EXTINF行"""
    channel = {'source': source_name}
    
    name_match = re.search(r',(?P<name>.+)$', line)
    if name_match:
        channel['name'] = name_match.group('name').strip()
    else:
        channel['name'] = "未知频道"
    
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
    if tvg_name_match:
        channel['tvg_name'] = tvg_name_match.group(1)
    else:
        channel['tvg_name'] = channel['name']
    
    group_match = re.search(r'group-title="([^"]*)"', line)
    if group_match:
        channel['group'] = group_match.group(1)
    else:
        channel['group'] = "默认分组"
    
    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    if logo_match:
        channel['logo'] = logo_match.group(1)
    else:
        channel['logo'] = ""
    
    return channel

def categorize_channel(channel):
    """对频道进行分类"""
    name = channel['name'].lower()
    tvg_name = channel['tvg_name'].lower()
    group = channel['group'].lower()
    
    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if (re.search(pattern_lower, name) or 
                re.search(pattern_lower, tvg_name) or 
                re.search(pattern_lower, group)):
                return category
    
    return "其他"

def merge_all_channels(all_channels_dicts):
    """合并所有频道"""
    merged_channels = {}
    
    for channels_dict in all_channels_dicts:
        for channel_name, channel_info in channels_dict.items():
            if channel_name not in merged_channels:
                merged_channels[channel_name] = channel_info.copy()
                merged_channels[channel_name]['sources'] = set(channel_info['sources'])
            else:
                for url in channel_info['urls']:
                    if url not in merged_channels[channel_name]['urls']:
                        merged_channels[channel_name]['urls'].append(url)
                merged_channels[channel_name]['sources'].update(channel_info['sources'])
    
    return merged_channels

def test_stream_quality(url, timeout=5):
    """测试流媒体质量"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def filter_high_quality_urls(channels, max_workers=5):
    """过滤高质量URL"""
    print("开始过滤高质量线路...")
    
    def test_url(args):
        channel_name, url = args
        if test_stream_quality(url):
            return (channel_name, url, True)
        return (channel_name, url, False)
    
    all_urls = []
    for channel_name, channel_info in channels.items():
        for url in channel_info['urls']:
            all_urls.append((channel_name, url))
    
    print(f"需要测试 {len(all_urls)} 个URL的质量...")
    
    valid_urls = defaultdict(list)
    
    # 限制测试数量以避免超时
    test_urls = all_urls[:500]  # 最多测试500个URL
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(test_url, url) for url in test_urls]
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"测试进度: {completed}/{len(test_urls)}")
            
            try:
                channel_name, url, is_valid = future.result()
                if is_valid:
                    valid_urls[channel_name].append(url)
            except Exception as e:
                print(f"测试URL时出错: {e}")
    
    filtered_channels = {}
    for channel_name, urls in valid_urls.items():
        if channel_name in channels and urls:
            channel_info = channels[channel_name].copy()
            channel_info['urls'] = urls[:30]
            filtered_channels[channel_name] = channel_info
    
    print(f"质量过滤完成，有效频道: {len(filtered_channels)}")
    return filtered_channels

def limit_channel_urls(channels, max_urls=30):
    """限制每个频道的URL数量"""
    for channel_name, channel_info in channels.items():
        urls = channel_info['urls']
        if len(urls) > max_urls:
            channel_info['urls'] = urls[:max_urls]
    return channels

def organize_channels_by_category(channels):
    """按分类组织频道"""
    categorized = defaultdict(list)
    
    for channel_name, channel_info in channels.items():
        category = categorize_channel(channel_info)
        categorized[category].append(channel_info)
    
    return categorized

def write_output_file(channels_by_category):
    """写入输出TXT文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_channels = sum(len(channels) for channels in channels_by_category.values())
    total_urls = sum(sum(len(channel['urls']) for channel in channels) for channels in channels_by_category.values())
    
    with open('ipzy_channels.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 中国境内电视直播线路 (仅限1080p高清以上)\n")
        f.write(f"# 更新时间: {timestamp}\n")
        f.write(f"# 数据来源: 多个GitHub IPTV项目\n")
        f.write(f"# 频道总数: {total_channels}\n")
        f.write(f"# 线路总数: {total_urls}\n")
        f.write(f"# 清晰度要求: 仅保留1080p高清及以上线路\n")
        f.write("#" * 60 + "\n\n")
        
        category_order = ["央视", "卫视", "港澳台", "影视剧", "4K", "音乐", "其他"]
        
        for category in category_order:
            if category in channels_by_category and channels_by_category[category]:
                f.write(f"{category},#genre#\n")
                
                sorted_channels = sorted(channels_by_category[category], key=lambda x: x['name'])
                
                for channel in sorted_channels:
                    for url in channel['urls']:
                        f.write(f"{channel['name']},{url}\n")
                
                category_url_count = sum(len(channel['urls']) for channel in sorted_channels)
                f.write(f"# 共 {len(sorted_channels)} 个频道，{category_url_count} 条线路\n\n")
        
        f.write("# 自动生成 - 每日北京时间为2点更新\n")
        f.write("# 仅保留1080p高清及以上清晰度线路\n")
        f.write("# 每个频道最多保留30条线路\n")

def main():
    """主函数"""
    print("开始收集IPZY高清直播线路...")
    print("清晰度要求: 仅保留1080p高清及以上线路")
    
    all_channels_dicts = []
    
    for source in SOURCES:
        print(f"处理源: {source['name']}")
        content = download_m3u(source['url'])
        if content:
            channels = parse_m3u_content(content, source['name'])
            all_channels_dicts.append(channels)
            print(f"  从 {source['name']} 获取了 {len(channels)} 个高清频道")
        else:
            print(f"  无法从 {source['name']} 获取数据")
        
        time.sleep(1)
    
    print("合并所有频道数据...")
    merged_channels = merge_all_channels(all_channels_dicts)
    
    print(f"初步筛选后共有 {len(merged_channels)} 个高清频道")
    
    # 可选：进行质量检测（会显著增加运行时间）
    use_quality_check = False  # 设置为True启用质量检测
    
    if use_quality_check:
        filtered_channels = filter_high_quality_urls(merged_channels, max_workers=5)
    else:
        filtered_channels = merged_channels
    
    filtered_channels = limit_channel_urls(filtered_channels, max_urls=30)
    
    categorized_channels = organize_channels_by_category(filtered_channels)
    
    print("高清频道收集完成，开始写入文件...")
    
    write_output_file(categorized_channels)
    
    total_channels = sum(len(channels) for channels in categorized_channels.values())
    total_urls = sum(sum(len(channel['urls']) for channel in channels) for channels in categorized_channels.values())
    
    print(f"任务完成！共收集 {total_channels} 个高清频道，{total_urls} 条线路")
    
    for category, channels in categorized_channels.items():
        category_url_count = sum(len(channel['urls']) for channel in channels)
        print(f"{category}: {len(channels)} 个频道，{category_url_count} 条线路")

if __name__ == "__main__":
    main()
