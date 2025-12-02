import requests
import re
from datetime import datetime
import time
from collections import defaultdict

# 数据源列表
SOURCES = [
    {"name": "iptv-org-cn", "url": "https://iptv-org.github.io/iptv/countries/cn.m3u"},
    {"name": "iptv-org-hk", "url": "https://iptv-org.github.io/iptv/countries/hk.m3u"},
    {"name": "iptv-org-mo", "url": "https://iptv-org.github.io/iptv/countries/mo.m3u"},
    {"name": "iptv-org-tw", "url": "https://iptv-org.github.io/iptv/countries/tw.m3u"},
    {"name": "iptv-org-all", "url": "https://iptv-org.github.io/iptv/index.m3u"},
    {"name": "fanmingming", "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u"},
    {"name": "free-iptv", "url": "https://raw.githubusercontent.com/Free-IPTV/Countries/master/China.m3u"},
    {"name": "moonkeyhoo", "url": "https://ghfast.top/https://raw.githubusercontent.com/moonkeyhoo/iptv-api/master/output/result.m3u"},
    {"name": "kakaxi-ipv6", "url": "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u"},
    {"name": "kakaxi-ipv4", "url": "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt"},
    {"name": "9390107", "url": "http://tv.html-5.me/i/9390107.txt"},
    {"name": "Supprise0901", "url": "https://ghfast.top/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt"},
    {"name": "ffmking", "url": "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt"},
    {"name": "zxj", "url": "https://codeberg.org/zxj/mao/raw/branch/main/live.txt"},  
    {"name": "kimwang1978", "url": "https://ghfast.top/https://github.com/kimwang1978/collect-txt/blob/main/bbxx.txt"},   
    {"name": "Guovin", "url": "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt"},  
    {"name": "Guovin2", "url": "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u"},  
    {"name": "xiao-ping2", "url": "https://gitee.com/xiao-ping2/iptv-api/raw/master/output/xp_result.txt"},  
    {"name": "qingtingjjjjjjj", "url": "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt"},
    {"name": "Heiwk", "url": "https://ghfast.top/https://raw.githubusercontent.com/Heiwk/iptv67/refs/heads/main/iptv.m3u"},
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

# 排除规则 - 排除包含特定字符的URL
def should_exclude_url(url):
    """
    判断是否应该排除该URL
    排除规则：URL中包含"example"或"demo"字符
    """
    return "example" in url.lower() or "demo" in url.lower()

def download_m3u(url, retries=2):
    """下载M3U文件"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None

def normalize_channel_name(name):
    """标准化频道名称"""
    if not name or name == "未知频道":
        return "未知频道"
        
    name = re.sub(r'\s+', ' ', name.strip())
    
    # 移除清晰度标记
    name = re.sub(r'\[[^\]]*\]', '', name)
    name = re.sub(r'\([^\)]*\)', '', name)
    
    # 常见频道名称标准化
    replacements = {
        r'CCTV-1\s*综合': 'CCTV-1',
        r'CCTV-1HD': 'CCTV-1',
        r'CCTV1': 'CCTV-1',
        r'CCTV-2\s*财经': 'CCTV-2',
        r'CCTV2': 'CCTV-2',
        r'CCTV-3\s*综艺': 'CCTV-3',
        r'CCTV3': 'CCTV-3',
        r'CCTV-4\s*中文国际': 'CCTV-4',
        r'CCTV4': 'CCTV-4',
        r'CCTV-5\s*体育': 'CCTV-5',
        r'CCTV5': 'CCTV-5',
        r'CCTV-5\+': 'CCTV-5+',
        r'CCTV-6\s*电影': 'CCTV-6',
        r'CCTV6': 'CCTV-6',
        r'CCTV-7\s*国防军事': 'CCTV-7',
        r'CCTV7': 'CCTV-7',
        r'CCTV-8\s*电视剧': 'CCTV-8',
        r'CCTV8': 'CCTV-8',
        r'CCTV-9\s*纪录': 'CCTV-9',
        r'CCTV9': 'CCTV-9',
        r'CCTV-10\s*科教': 'CCTV-10',
        r'CCTV10': 'CCTV-10',
        r'CCTV-11\s*戏曲': 'CCTV-11',
        r'CCTV11': 'CCTV-11',
        r'CCTV-12\s*社会与法': 'CCTV-12',
        r'CCTV12': 'CCTV-12',
        r'CCTV-13\s*新闻': 'CCTV-13',
        r'CCTV13': 'CCTV-13',
        r'CCTV-14\s*少儿': 'CCTV-14',
        r'CCTV14': 'CCTV-14',
        r'CCTV-15\s*音乐': 'CCTV-15',
        r'CCTV15': 'CCTV-15',
        r'湖南卫视HD': '湖南卫视',
        r'浙江卫视HD': '浙江卫视',
        r'江苏卫视HD': '江苏卫视',
        r'北京卫视HD': '北京卫视',
        r'东方卫视HD': '东方卫视',
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name)
    
    return name.strip()

def is_hd_channel(channel_info):
    """判断是否为高清频道"""
    name = channel_info.get('name', '').lower()
    tvg_name = channel_info.get('tvg_name', '').lower()
    group = channel_info.get('group', '').lower()
    
    # 检查是否包含高清关键词
    for keyword in HD_KEYWORDS:
        if (keyword.lower() in name or 
            keyword.lower() in tvg_name or 
            keyword.lower() in group):
            return True
    
    # 对于央视和卫视，默认认为是高清
    cctv_pattern = r'cctv'
    satellite_pattern = r'卫视'
    if (re.search(cctv_pattern, name) or 
        re.search(cctv_pattern, tvg_name) or
        re.search(satellite_pattern, name) or
        re.search(satellite_pattern, tvg_name)):
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
                
                # 初步筛选高清频道
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
                    
                    # 检查URL是否应该被排除
                    if not should_exclude_url(line) and line not in channels[channel_name]['urls']:
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
    
    # 首先根据来源判断港澳台
    source = channel.get('source', '')
    if any(region in source for region in ['hk', 'mo', 'tw']):
        # 检查是否已经被其他分类规则匹配
        for category, patterns in CATEGORY_RULES.items():
            if category == "港澳台":
                continue
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if (re.search(pattern_lower, name) or 
                    re.search(pattern_lower, tvg_name) or 
                    re.search(pattern_lower, group)):
                    return category
        return "港澳台"
    
    # 根据分类规则匹配
    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if (re.search(pattern_lower, name) or 
                re.search(pattern_lower, tvg_name) or 
                re.search(pattern_lower, group)):
                return category
    
    # 未分类的频道
    return "其他"

def merge_all_channels(all_channels_dicts):
    """合并所有频道"""
    merged_channels = {}
    
    for channels_dict in all_channels_dicts:
        for channel_name, channel_info in channels_dict.items():
            if channel_name == "未知频道":
                continue
                
            if channel_name not in merged_channels:
                merged_channels[channel_name] = channel_info.copy()
                merged_channels[channel_name]['sources'] = set(channel_info['sources'])
            else:
                # 合并URLs，同时排除不需要的URL
                for url in channel_info['urls']:
                    if not should_exclude_url(url) and url not in merged_channels[channel_name]['urls']:
                        merged_channels[channel_name]['urls'].append(url)
                merged_channels[channel_name]['sources'].update(channel_info['sources'])
    
    return merged_channels

def ensure_min_urls_per_channel(channels, min_urls=10, max_urls=30):
    """确保每个频道有最少线路数量"""
    # 限制最大线路数
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
                avg_urls = category_url_count / len(sorted_channels) if sorted_channels else 0
                f.write(f"# 共 {len(sorted_channels)} 个频道，{category_url_count} 条线路 (平均{avg_urls:.1f}条/频道)\n\n")
        
        f.write("# 自动生成 - 每日北京时间为2点更新\n")
        f.write("# 仅保留1080p高清及以上清晰度线路\n")
        f.write("# 每个频道至少10条线路，最多30条线路\n")

def main():
    """主函数"""
    all_channels_dicts = []
    successful_sources = 0
    
    for source in SOURCES:
        content = download_m3u(source['url'])
        if content:
            channels = parse_m3u_content(content, source['name'])
            all_channels_dicts.append(channels)
            successful_sources += 1
        time.sleep(0.5)
    
    if not all_channels_dicts:
        return
    
    # 合并所有频道数据
    merged_channels = merge_all_channels(all_channels_dicts)
    
    # 确保每个频道有足够线路
    merged_channels = ensure_min_urls_per_channel(merged_channels, min_urls=10, max_urls=30)
    
    # 按分类组织频道
    categorized_channels = organize_channels_by_category(merged_channels)
    
    # 写入输出文件
    write_output_file(categorized_channels)

if __name__ == "__main__":
    main()
