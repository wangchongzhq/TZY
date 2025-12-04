# -*- coding: utf-8 -*-
import requests
import re
from datetime import datetime
import time
from collections import defaultdict

# 鏁版嵁婧愬垪琛?
# 瀵煎叆缁熶竴鏁版嵁婧愬垪琛?
from unified_sources import SOURCES_WITH_NAMES

# 鏁版嵁婧愬垪琛?- 浣跨敤缁熶竴鐨勬暟鎹簮
SOURCES = SOURCES_WITH_NAMES

# 鍒嗙被瑙勫垯
CATEGORY_RULES = {
    "澶": [
        r'CCTV', r'中央电视台', r'CGTN', r'卫视'
    ],
    "鍗": [
        r'鍗', r'婀栧崡鍗', r'娴欐睙鍗', r'涓滄柟鍗', r'鍖椾含鍗', r'姹熻嫃鍗',
        r'瀹夊窘鍗', r'閲嶅簡鍗', r'涓滃崡鍗', r'鐢樿們鍗', r'骞夸笢鍗',
        r'骞胯タ鍗', r'璐靛窞鍗', r'娴峰崡鍗', r'娌冲寳鍗', r'新疆卫视',
        r'娌冲崡鍗', r'婀栧寳鍗', r'姹熻タ鍗', r'鍚夋灄鍗', r'杈藉畞鍗',
        r'灞变笢鍗', r'娣卞湷鍗', r'鍥涘窛鍗', r'澶╂触鍗', r'浜戝崡鍗'
    ],
    "境外台": [
        r'鍑ゅ嚢', r'TVB', r'缈＄繝', r'鏄庣彔', r'鏈腐', r'鍥介檯', r'婢宠', r'婢抽棬',
        r'鍗庤', r'涓', r'鍙拌', r'姘戣', r'涓夌珛', r'涓滄．', r'鏄熺┖', r'棣欐腐',
        r'婢抽杸', r'鍙扮仯', r'鍙版咕'
    ],
    "电影剧场": [
        r'鐢靛奖', r'电影', r'剧场', r'剧集', r'影院', r'MOVIE', r'DRAMA',
        r'CHC', r'万达', r'佳片有约', r'华语电影', r'家庭影院'
    ],
    "4K": [
        r'4K', r'4k', r'UHD', r'超高清', r'2160P', r'2160p'
    ],
    "音乐": [
        r'音乐', r'MUSIC', r'MTV', r'流行音乐', r'经典音乐', r'音乐台',
        r'凤凰音乐', r'星空OK'
    ]
}

# 楂樻竻鍏抽敭璇?
HD_KEYWORDS = [
    r'1080', r'1080p', r'1080P', r'楂樻竻', r'HD', r'High Definition', 
    r'FHD', r'Full HD', r'瓒呮竻', r'4K', r'4k', r'UHD', r'2160'
]

# 鎺掗櫎瑙勫垯 - 鎺掗櫎鍖呭惈鐗瑰畾瀛楃鐨刄RL
def should_exclude_url(url):
    """
    鍒ゆ柇鏄惁搴旇鎺掗櫎璇RL
    鎺掗櫎瑙勫垯锛歎RL浠?http://example"鎴?https://example"寮€澶达紝鎴栧寘鍚?demo"瀛楃
    """
    if not url:
        return True
    # 鎺掗櫎鐗瑰畾鍩熷悕鐨刄RL
    exclude_patterns = [
        'http://example',
        'https://example'
    ]
    for pattern in exclude_patterns:
        if url.startswith(pattern):
            return True
    # 淇濈暀瀵?demo"鐨勬帓闄?
    return "demo" in url.lower()

def download_m3u(url, retries=2):
    """涓嬭浇M3U鏂囦欢"""
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
    """鏍囧噯鍖栭閬撳悕绉?""
    if not name or name == "鏈煡棰戦亾":
        return "鏈煡棰戦亾"
        
    name = re.sub(r'\s+', ' ', name.strip())
    
    # 绉婚櫎娓呮櫚搴︽爣璁?
    name = re.sub(r'\[[^\]]*\]', '', name)
    name = re.sub(r'\([^\)]*\)', '', name)
    
    # 妫€鏌ユ槸鍚︿负鏃堕棿鎴筹紙濡?2025-11-26 18:53:51锛?
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
    if re.match(timestamp_pattern, name):
        return "鏈煡棰戦亾"
    
    # 妫€鏌ユ槸鍚︿负绾暟瀛?
    if name.isdigit():
        return "鏈煡棰戦亾"
    
    # 甯歌棰戦亾鍚嶇О鏍囧噯鍖?
    replacements = {
        r'CCTV-1\s*缁煎悎': 'CCTV-1',
        r'CCTV-1HD': 'CCTV-1',
        r'CCTV1': 'CCTV-1',
        r'CCTV-2\s*璐㈢粡': 'CCTV-2',
        r'CCTV2': 'CCTV-2',
        r'CCTV-3\s*缁艰壓': 'CCTV-3',
        r'CCTV3': 'CCTV-3',
        r'CCTV-4\s*涓枃鍥介檯': 'CCTV-4',
        r'CCTV4': 'CCTV-4',
        r'CCTV-5\s*浣撹偛': 'CCTV-5',
        r'CCTV5': 'CCTV-5',
        r'CCTV-5\+': 'CCTV-5+',
        r'CCTV-6\s*鐢靛奖': 'CCTV-6',
        r'CCTV6': 'CCTV-6',
        r'CCTV-7\s*鍥介槻鍐涗簨': 'CCTV-7',
        r'CCTV7': 'CCTV-7',
        r'CCTV-8\s*鐢佃鍓?: 'CCTV-8',
        r'CCTV8': 'CCTV-8',
        r'CCTV-9\s*绾綍': 'CCTV-9',
        r'CCTV9': 'CCTV-9',
        r'CCTV-10\s*绉戞暀': 'CCTV-10',
        r'CCTV10': 'CCTV-10',
        r'CCTV-11\s*鎴忔洸': 'CCTV-11',
        r'CCTV11': 'CCTV-11',
        r'CCTV-12\s*绀句細涓庢硶': 'CCTV-12',
        r'CCTV12': 'CCTV-12',
        r'CCTV-13\s*鏂伴椈': 'CCTV-13',
        r'CCTV13': 'CCTV-13',
        r'CCTV-14\s*灏戝効': 'CCTV-14',
        r'CCTV14': 'CCTV-14',
        r'CCTV-15\s*闊充箰': 'CCTV-15',
        r'CCTV15': 'CCTV-15',
        r'婀栧崡鍗HD': '婀栧崡鍗',
        r'娴欐睙鍗HD': '娴欐睙鍗',
        r'姹熻嫃鍗HD': '姹熻嫃鍗',
        r'鍖椾含鍗HD': '鍖椾含鍗',
        r'涓滄柟鍗HD': '涓滄柟鍗',
    }
    
    for pattern, replacement in replacements.items():
        name = re.sub(pattern, replacement, name)
    
    return name.strip()

def is_hd_channel(channel_info):
    """判断是否为高清晰度频道"""
    name = channel_info.get('name', '').lower()
    tvg_name = channel_info.get('tvg_name', '').lower()
    group = channel_info.get('group', '').lower()
    
    # 检查是否包含高清关键字
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
                
                # 鍒濇绛涢€夐珮娓呴閬?
                if is_hd_channel(current_channel):
                    channel_name = normalize_channel_name(current_channel['name'])
                    
                    if channel_name not in channels:
                        channels[channel_name] = {
                            'name': channel_name,
                            'tvg_name': current_channel.get('tvg_name', channel_name),
                            'group': current_channel.get('group', '榛樿鍒嗙粍'),
                            'logo': current_channel.get('logo', ''),
                            'urls': [],
                            'sources': set()
                        }
                    
                    # 妫€鏌RL鏄惁搴旇琚帓闄?
                    if not should_exclude_url(line) and line not in channels[channel_name]['urls']:
                        channels[channel_name]['urls'].append(line)
                        channels[channel_name]['sources'].add(source_name)
                
                current_channel = {}
    
    return channels

def parse_extinf_line(line, source_name):
    """瑙ｆ瀽EXTINF琛?""
    channel = {'source': source_name}
    
    name_match = re.search(r',(?P<name>.+)$', line)
    if name_match:
        channel['name'] = name_match.group('name').strip()
    else:
        channel['name'] = "鏈煡棰戦亾"
    
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
    if tvg_name_match:
        channel['tvg_name'] = tvg_name_match.group(1)
    else:
        channel['tvg_name'] = channel['name']
    
    group_match = re.search(r'group-title="([^"]*)"', line)
    if group_match:
        channel['group'] = group_match.group(1)
    else:
        channel['group'] = "榛樿鍒嗙粍"
    
    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    if logo_match:
        channel['logo'] = logo_match.group(1)
    else:
        channel['logo'] = ""
    
    return channel

def categorize_channel(channel):
    """瀵归閬撹繘琛屽垎绫?""
    name = channel['name'].lower()
    tvg_name = channel['tvg_name'].lower()
    group = channel['group'].lower()
    
    # 棣栧厛鏍规嵁鏉ユ簮鍒ゆ柇娓境鍙?
    source = channel.get('source', '')
    if any(region in source for region in ['hk', 'mo', 'tw']):
        # 妫€鏌ユ槸鍚﹀凡缁忚鍏朵粬鍒嗙被瑙勫垯鍖归厤
        for category, patterns in CATEGORY_RULES.items():
            if category == "娓境鍙?:
                continue
            for pattern in patterns:
                pattern_lower = pattern.lower()
                if (re.search(pattern_lower, name) or 
                    re.search(pattern_lower, tvg_name) or 
                    re.search(pattern_lower, group)):
                    return category
        return "娓境鍙?
    
    # 鏍规嵁鍒嗙被瑙勫垯鍖归厤
    for category, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if (re.search(pattern_lower, name) or 
                re.search(pattern_lower, tvg_name) or 
                re.search(pattern_lower, group)):
                return category
    
    # 鏈垎绫荤殑棰戦亾
    return "鍏朵粬"

def merge_all_channels(all_channels_dicts):
    """合并所有频道"""
    merged_channels = {}
    
    for channels_dict in all_channels_dicts:
        for channel_name, channel_info in channels_dict.items():
            if channel_name == "鏈煡棰戦亾":
                continue
                
            if channel_name not in merged_channels:
                merged_channels[channel_name] = channel_info.copy()
                merged_channels[channel_name]['sources'] = set(channel_info['sources'])
            else:
                # 鍚堝苟URLs锛屽悓鏃舵帓闄や笉闇€瑕佺殑URL鍜岄噸澶峌RL
                for url in channel_info['urls']:
                    if not should_exclude_url(url) and url not in merged_channels[channel_name]['urls']:
                        merged_channels[channel_name]['urls'].append(url)
                merged_channels[channel_name]['sources'].update(channel_info['sources'])
    
    return merged_channels

def ensure_min_urls_per_channel(channels, min_urls=10, max_urls=30):
    """确保每个频道有最少链接数量"""
    # 闄愬埗鏈€澶х嚎璺暟
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
    """鍐欏叆杈撳嚭TXT鏂囦欢"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_channels = sum(len(channels) for channels in channels_by_category.values())
    total_urls = sum(sum(len(channel['urls']) for channel in channels) for channels in channels_by_category.values())
    
    with open('ipzy_channels.txt', 'w', encoding='utf-8') as f:
        f.write(f"# 涓浗澧冨唴鐢佃鐩存挱绾胯矾 (浠呴檺1080p楂樻竻浠ヤ笂)\n")
        f.write(f"# 鏇存柊鏃堕棿: {timestamp}\n")
        f.write(f"# 鏁版嵁鏉ユ簮: 澶氫釜GitHub IPTV椤圭洰\n")
        f.write(f"# 棰戦亾鎬绘暟: {total_channels}\n")
        f.write(f"# 绾胯矾鎬绘暟: {total_urls}\n")
        f.write(f"# 娓呮櫚搴﹁姹? 浠呬繚鐣?080p楂樻竻鍙婁互涓婄嚎璺痋n")
        f.write("#" * 60 + "\n\n")
        
        category_order = ["澶", "鍗", "娓境鍙?, "褰辫鍓?, "4K", "闊充箰", "鍏朵粬"]
        
        for category in category_order:
            if category in channels_by_category and channels_by_category[category]:
                f.write(f"{category},#genre#\n")
                
                sorted_channels = sorted(channels_by_category[category], key=lambda x: x['name'])
                
                for channel in sorted_channels:
                    for url in channel['urls']:
                        f.write(f"{channel['name']},{url}\n")
                
                category_url_count = sum(len(channel['urls']) for channel in sorted_channels)
                avg_urls = category_url_count / len(sorted_channels) if sorted_channels else 0
                f.write(f"# 鍏?{len(sorted_channels)} 涓閬擄紝{category_url_count} 鏉＄嚎璺?(骞冲潎{avg_urls:.1f}鏉?棰戦亾)\n\n")
        
        f.write("# 鑷姩鐢熸垚 - 姣忔棩鍖椾含鏃堕棿涓?鐐规洿鏂癨n")
        f.write("# 浠呬繚鐣?080p楂樻竻鍙婁互涓婃竻鏅板害绾胯矾\n")
        f.write("# 姣忎釜棰戦亾鑷冲皯10鏉＄嚎璺紝鏈€澶?0鏉＄嚎璺痋n")

def main():
    """涓诲嚱鏁?""
    print("寮€濮嬫敹闆嗛珮娓呯洿鎾簮...")
    all_channels_dicts = []
    successful_sources = 0
    failed_sources = 0
    
    print(f"鍏卞彂鐜?{len(SOURCES)} 涓暟鎹簮")
    
    for i, source in enumerate(SOURCES, 1):
        try:
            # SOURCES_WITH_NAMES鏄竴涓厓缁勫垪琛細(name, url)
            source_name, source_url = source
            print(f"\n{i}/{len(SOURCES)}: 姝ｅ湪澶勭悊 {source_name}")
            print(f"  URL: {source_url}")
            
            content = download_m3u(source_url)
            if content:
                print(f"  鉁?涓嬭浇鎴愬姛锛屽唴瀹归暱搴? {len(content)} 瀛楃")
                channels = parse_m3u_content(content, source_name)
                print(f"  鉁?瑙ｆ瀽鎴愬姛锛屽彂鐜?{len(channels)} 涓閬?)
                all_channels_dicts.append(channels)
                successful_sources += 1
            else:
                print(f"  鉂?涓嬭浇澶辫触鎴栧唴瀹逛负绌?)
                failed_sources += 1
            
            time.sleep(0.5)
        except Exception as e:
            print(f"  鉂?閿欒: {type(e).__name__}: {e}")
            failed_sources += 1
    
    print(f"\n鏁版嵁婧愬鐞嗗畬鎴?")
    print(f"  鎴愬姛: {successful_sources}")
    print(f"  澶辫触: {failed_sources}")
    
    if not all_channels_dicts:
        print("鉂?娌℃湁鎴愬姛瑙ｆ瀽浠讳綍棰戦亾鏁版嵁")
        return
    
    # 鍚堝苟鎵€鏈夐閬撴暟鎹?
    print("\n姝ｅ湪鍚堝苟鎵€鏈夐閬撴暟鎹?..")
    try:
        merged_channels = merge_all_channels(all_channels_dicts)
        print(f"  鉁?鍚堝苟瀹屾垚锛屽叡 {len(merged_channels)} 涓閬?)
    except Exception as e:
        print(f"  鉂?鍚堝苟閿欒: {type(e).__name__}: {e}")
        return
    
    # 纭繚姣忎釜棰戦亾鏈夎冻澶熺嚎璺?
    print("\n姝ｅ湪浼樺寲棰戦亾绾胯矾鏁伴噺...")
    try:
        merged_channels = ensure_min_urls_per_channel(merged_channels, min_urls=10, max_urls=30)
        print(f"  鉁?浼樺寲瀹屾垚")
    except Exception as e:
        print(f"  鉂?浼樺寲閿欒: {type(e).__name__}: {e}")
        return
    
    # 鎸夊垎绫荤粍缁囬閬?
    print("\n姝ｅ湪鍒嗙被棰戦亾...")
    try:
        categorized_channels = organize_channels_by_category(merged_channels)
        print(f"  鉁?鍒嗙被瀹屾垚")
    except Exception as e:
        print(f"  鉂?鍒嗙被閿欒: {type(e).__name__}: {e}")
        return
    
    # 鍐欏叆杈撳嚭鏂囦欢
    print("\n姝ｅ湪鐢熸垚杈撳嚭鏂囦欢...")
    try:
        write_output_file(categorized_channels)
        print("  鉁?杈撳嚭鏂囦欢鐢熸垚瀹屾垚")
    except Exception as e:
        print(f"  鉂?杈撳嚭鏂囦欢閿欒: {type(e).__name__}: {e}")
        return
    
    print("\n鉁?鎵€鏈変换鍔″畬鎴愶紒")

if __name__ == "__main__":
    main()
