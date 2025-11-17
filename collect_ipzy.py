import requests
import re
from datetime import datetime
import os
import time
from collections import defaultdict

# 定义多个数据源 - 增加更多IPTV源以获取同一频道的多个线路
SOURCES = [
    # 主要数据源
    {"name": "iptv-org-cn", "url": "https://iptv-org.github.io/iptv/countries/cn.m3u"},
    {"name": "iptv-org-hk", "url": "https://iptv-org.github.io/iptv/countries/hk.m3u"},
    {"name": "iptv-org-mo", "url": "https://iptv-org.github.io/iptv/countries/mo.m3u"},
    {"name": "iptv-org-tw", "url": "https://iptv-org.github.io/iptv/countries/tw.m3u"},
    {"name": "iptv-org-backup", "url": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"},
    
    # 额外数据源 - 用于获取更多线路
    {"name": "fanmingming", "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u"},
    {"name": "yangjian", "url": "https://raw.githubusercontent.com/YanG-1989/m3u/main/Adult.m3u"},
    {"name": "free-iptv", "url": "https://raw.githubusercontent.com/Free-IPTV/Countries/master/China.m3u"},
    {"name": "iptv-china", "url": "https://raw.githubusercontent.com/iptvmax/iptv/main/China.m3u"},
    
    # 备用数据源
    {"name": "backup1", "url": "https://raw.githubusercontent.com/ImMaX2/IPTV-ASIA/master/ASIA.m3u"},
    {"name": "backup2", "url": "https://raw.githubusercontent.com/mitv/iptv/master/China.m3u"},
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
        r'澳門', r'台灣', r'台湾', r'HK', r'Hong Kong', r'Macau', r'Taiwan'
    ],
    "影视剧": [
        r'电影', r'剧场', r'影院', r'影视', r'剧集', r'MOVIE', r'DRAMA',
        r'CHC', r'黑莓', r'好莱坞', r'华语电影', r'家庭影院', r'戏剧'
    ],
    "4K": [
        r'4K', r'4k', r'UHD', r'超高清', r'2160P', r'2160p', r'HEVC', r'4K超高清'
    ],
    "音乐": [
        r'音乐', r'MUSIC', r'MTV', r'流行音乐', r'经典音乐', r'音乐台',
        r'风云音乐', r'卡拉OK', r'KTV', r'演唱会'
    ]
}

def download_m3u(url, retries=3):
    """下载M3U文件，支持重试"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"下载失败 {url} (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)  # 等待后重试
    return None

def normalize_channel_name(name):
    """标准化频道名称以便更好地匹配"""
    # 移除多余空格和特殊字符
    name = re.sub(r'\s+', ' ', name.strip())
    
    # 常见频道名称标准化
    replacements = {
        r'CCTV-1\s*综合': 'CCTV-1',
        r'CCTV-1HD': 'CCTV-1',
        r'CCTV1': 'CCTV-1',
        r'CCTV-2\s*财经': 'CCTV-2',
        r'CCTV2': 'CCTV-2',
        r'湖南卫视HD': '湖南卫视',
        r'浙江卫视HD': '浙江卫视',
        r'江苏卫视HD': '江苏卫视',
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name)
    
    return name

def parse_m3u_content(content, source_name):
    """解析M3U内容并返回频道字典"""
    if not content:
        return {}
    
    lines = content.split('\n')
    channels = {}
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 解析频道信息行
            current_channel = parse_extinf_line(line, source_name)
        elif line.startswith('http'):
            # 这是URL行
            if current_channel:
                current_channel['url'] = line
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
                
                # 添加URL到频道（去重）
                if line not in channels[channel_name]['urls']:
                    channels[channel_name]['urls'].append(line)
                    channels[channel_name]['sources'].add(source_name)
                
                current_channel = {}
    
    return channels

def parse_extinf_line(line, source_name):
    """解析EXTINF行提取频道信息"""
    channel = {'source': source_name}
    
    # 提取频道名称（逗号后的部分）
    name_match = re.search(r',(?P<name>.+)$', line)
    if name_match:
        channel['name'] = name_match.group('name').strip()
    else:
        channel['name'] = "未知频道"
    
    # 提取tvg-name
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
    if tvg_name_match:
        channel['tvg_name'] = tvg_name_match.group(1)
    else:
        channel['tvg_name'] = channel['name']
    
    # 提取group-title
    group_match = re.search(r'group-title="([^"]*)"', line)
    if group_match:
        channel['group'] = group_match.group(1)
    else:
        channel['group'] = "默认分组"
    
    # 提取tvg-logo
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
    """合并来自所有源的频道并去重"""
    merged_channels = {}
    
    for channels_dict in all_channels_dicts:
        for channel_name, channel_info in channels_dict.items():
            if channel_name not in merged_channels:
                merged_channels[channel_name] = channel_info.copy()
                merged_channels[channel_name]['sources'] = set(channel_info['sources'])
            else:
                # 合并URLs
                for url in channel_info['urls']:
                    if url not in merged_channels[channel_name]['urls']:
                        merged_channels[channel_name]['urls'].append(url)
                
                # 合并来源
                merged_channels[channel_name]['sources'].update(channel_info['sources'])
    
    return merged_channels

def limit_channel_urls(channels, min_urls=10, max_urls=30):
    """限制每个频道的URL数量"""
    for channel_name, channel_info in channels.items():
        urls = channel_info['urls']
        if len(urls) > max_urls:
            # 如果URL太多，随机选择max_urls个（这里我们简单取前max_urls个）
            channel_info['urls'] = urls[:max_urls]
        # 如果URL少于min_urls，我们保留所有（不处理）
    
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
        f.write(f"# 中国境内电视直播线路\n")
        f.write(f"# 更新时间: {timestamp}\n")
        f.write(f"# 数据来源: 多个GitHub IPTV项目\n")
        f.write(f"# 频道总数: {total_channels}\n")
        f.write(f"# 线路总数: {total_urls}\n")
        f.write("#" * 50 + "\n\n")
        
        # 按固定顺序写入分类
        category_order = ["央视", "卫视", "港澳台", "影视剧", "4K", "音乐", "其他"]
        
        for category in category_order:
            if category in channels_by_category and channels_by_category[category]:
                f.write(f"{category},#genre#\n")
                
                # 按频道名称排序
                sorted_channels = sorted(channels_by_category[category], key=lambda x: x['name'])
                
                for channel in sorted_channels:
                    # 为每个频道写入多个URL
                    for url in channel['urls']:
                        f.write(f"{channel['name']},{url}\n")
                
                category_url_count = sum(len(channel['urls']) for channel in sorted_channels)
                f.write(f"# 共 {len(sorted_channels)} 个频道，{category_url_count} 条线路\n\n")
        
        f.write("# 自动生成 - 每日北京时间为2点更新\n")
        f.write("# 每个频道最多保留30条线路\n")

def test_url(url, timeout=5):
    """测试URL是否可用"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def filter_valid_urls(channels):
    """过滤有效的URL（可选功能，会增加运行时间）"""
    print("开始测试URL有效性...")
    valid_channels = {}
    
    for channel_name, channel_info in channels.items():
        valid_urls = []
        for url in channel_info['urls']:
            if test_url(url):
                valid_urls.append(url)
            # 为了节省时间，我们只测试前5个URL
            if len(valid_urls) >= 5:
                break
        
        if valid_urls:
            channel_info['urls'] = valid_urls
            valid_channels[channel_name] = channel_info
    
    print(f"URL有效性测试完成，有效频道: {len(valid_channels)}")
    return valid_channels

def main():
    """主函数"""
    print("开始收集IPZY直播线路...")
    
    all_channels_dicts = []
    
    # 从各数据源收集频道
    for source in SOURCES:
        print(f"处理源: {source['name']} - {source['url']}")
        content = download_m3u(source['url'])
        if content:
            channels = parse_m3u_content(content, source['name'])
            all_channels_dicts.append(channels)
            print(f"  从 {source['name']} 获取了 {len(channels)} 个频道")
        else:
            print(f"  无法从 {source['name']} 获取数据")
        
        # 短暂暂停以避免请求过快
        time.sleep(1)
    
    print("合并所有频道数据...")
    # 合并所有频道路径
    merged_channels = merge_all_channels(all_channels_dicts)
    
    print(f"合并后共有 {len(merged_channels)} 个唯一频道")
    
    # 限制每个频道的URL数量
    merged_channels = limit_channel_urls(merged_channels, min_urls=10, max_urls=30)
    
    # 按分类组织频道
    categorized_channels = organize_channels_by_category(merged_channels)
    
    print("频道收集完成，开始写入文件...")
    
    # 写入输出文件
    write_output_file(categorized_channels)
    
    # 统计信息
    total_channels = sum(len(channels) for channels in categorized_channels.values())
    total_urls = sum(sum(len(channel['urls']) for channel in channels) for channels in categorized_channels.values())
    
    print(f"任务完成！共收集 {total_channels} 个频道，{total_urls} 条线路")
    
    for category, channels in categorized_channels.items():
        category_url_count = sum(len(channel['urls']) for channel in channels)
        print(f"{category}: {len(channels)} 个频道，{category_url_count} 条线路")

if __name__ == "__main__":
    main()
