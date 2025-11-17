import requests

import re

from datetime import datetime

import os




# 定义数据源 - 主要使用iptv-org的分地区M3U文件

SOURCES = {

    "cn": "https://iptv-org.github.io/iptv/countries/cn.m3u",

    "hk": "https://iptv-org.github.io/iptv/countries/hk.m3u", 

    "mo": "https://iptv-org.github.io/iptv/countries/mo.m3u",

    "tw": "https://iptv-org.github.io/iptv/countries/tw.m3u",

    "backup": "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u"

}




# 分类规则

CATEGORY_RULES = {

    "央视": [

        r'CCTV', r'中央电视台', r'CGTN'

    ],

    "卫视": [

        r'卫视', r'湖南卫视', r'浙江卫视', r'东方卫视', r'北京卫视', r'江苏卫视',

        r'安徽卫视', r'重庆卫视', r'东南卫视', r'甘肃卫视', r'广东卫视',

        r'广西卫视', r'贵州卫视', r'海南卫视', r'河北卫视', r'黑龙江卫视',

        r'河南卫视', r'湖北卫视', r'江西卫视', r'吉林卫视', r'辽宁卫视',

        r'山东卫视', r'深圳卫视', r'四川卫视', r'天津卫视', r'云南卫视'

    ],

    "港澳台": [

        r'凤凰', r'TVB', r'翡翠', r'明珠', r'本港', r'国际', r'澳视', r'澳门',

        r'华视', r'中视', r'台视', r'民视', r'三立', r'东森', r'星空'

    ],

    "影视剧": [

        r'电影', r'剧场', r'影院', r'影视', r'剧集', r'MOVIE', r'DRAMA',

        r'CHC', r'黑莓', r'好莱坞', r'华语电影', r'家庭影院'

    ],

    "4K": [

        r'4K', r'4k', r'UHD', r'超高清', r'2160P', r'2160p', r'HEVC'

    ],

    "音乐": [

        r'音乐', r'MUSIC', r'MTV', r'流行音乐', r'经典音乐', r'音乐台',

        r'风云音乐', r'卡拉OK'

    ]

}




def download_m3u(url):

    """下载M3U文件"""

    try:

        response = requests.get(url, timeout=10)

        response.encoding = 'utf-8'

        return response.text

    except Exception as e:

        print(f"下载失败 {url}: {e}")

        return None




def parse_m3u_content(content, source_type):

    """解析M3U内容并分类"""

    if not content:

        return {}

    

    lines = content.split('\n')

    channels = {}

    current_channel = {}

    

    for line in lines:

        line = line.strip()

        if line.startswith('#EXTINF:'):

            # 解析频道信息行

            current_channel = parse_extinf_line(line, source_type)

        elif line.startswith('http'):

            # 这是URL行

            if current_channel:

                current_channel['url'] = line

                category = categorize_channel(current_channel)

                

                if category not in channels:

                    channels[category] = []

                

                # 去重检查

                if not any(ch['name'] == current_channel['name'] and ch['url'] == line for ch in channels[category]):

                    channels[category].append(current_channel.copy())

                

                current_channel = {}

    

    return channels




def parse_extinf_line(line, source_type):

    """解析EXTINF行提取频道信息"""

    channel = {'source': source_type}

    

    # 提取频道名称（逗号后的部分）

    name_match = re.search(r',(?P<name>.+)$', line)

    if name_match:

        channel['name'] = name_match.group('name').strip()

    else:

        channel['name'] = "未知频道"

    

    # 提取tvg-name

    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)

    if tvg_name_match:

        channel['tvg_name'] = tvg_name_match.group(1)

    else:

        channel['tvg_name'] = channel['name']

    

    # 提取group-title

    group_match = re.search(r'group-title="([^"]*)"', line)

    if group_match:

        channel['group'] = group_match.group(1)

    else:

        channel['group'] = "默认分组"

    

    # 提取tvg-logo

    logo_match = re.search(r'tvg-logo="([^"]*)"', line)

    if logo_match:

        channel['logo'] = logo_match.group(1)

    else:

        channel['logo'] = ""

    

    return channel




def categorize_channel(channel):

    """对频道进行分类"""

    name = channel['name'].lower()

    tvg_name = channel['tvg_name'].lower()

    group = channel['group'].lower()

    source = channel['source']

    

    # 首先根据来源判断港澳台

    if source in ['hk', 'mo', 'tw']:

        # 但需要排除已经明确分类的频道

        for category, patterns in CATEGORY_RULES.items():

            if category == "港澳台":

                continue

            for pattern in patterns:

                if (re.search(pattern.lower(), name) or 

                    re.search(pattern.lower(), tvg_name) or 

                    re.search(pattern.lower(), group)):

                    return category

        return "港澳台"

    

    # 根据分类规则匹配

    for category, patterns in CATEGORY_RULES.items():

        for pattern in patterns:

            if (re.search(pattern.lower(), name) or 

                re.search(pattern.lower(), tvg_name) or 

                re.search(pattern.lower(), group)):

                return category

    

    # 未分类的频道

    return "其他"




def merge_channels(all_channels):

    """合并来自不同源的频道并去重"""

    merged = {}

    

    for source, categories in all_channels:

        for category, channels in categories.items():

            if category not in merged:

                merged[category] = []

            

            for channel in channels:

                # 基于名称和URL去重

                if not any(ch['name'] == channel['name'] and ch['url'] == channel['url']for ch in merged[category]):

                    merged[category].append(channel)

    

    return merged




def write_output_file(channels_by_category):

    """写入输出TXT文件"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    

    with open('ipzy_channels.txt', 'w', encoding='utf-8') as f:

        f.write(f"# 中国境内电视直播线路\n")

        f.write(f"# 更新时间: {timestamp}\n")

        f.write(f"# 数据来源: GitHub iptv-org等项目\n")

        f.write(f"# 频道总数: {sum(len(channels) for channels in channels_by_category.values())}\n")

        f.write("#" * 50 + "\n\n")

        

        # 按固定顺序写入分类

        category_order = ["央视", "卫视", "港澳台", "影视剧", "4K", "音乐", "其他"]

        

        for category in category_order:

            if category in channels_by_category and channels_by_category[category]:

                f.write(f"{category},#genre#\n")

                

                # 按频道名称排序

                sorted_channels = sorted(channels_by_category[category], key=lambda x: x['name'])

                

                for channel in sorted_channels:

                    f.write(f"{channel['name']},{channel['url']}\n")

                

                f.write(f"# 共 {len(sorted_channels)} 个频道\n\n")

        

        f.write("# 自动生成 - 每日北京时间为2点更新\n")




def main():

    """主函数"""

    print("开始收集IPZY直播线路...")

    

    all_channels = {}

    

    # 从各数据源收集频道

    for source_id, url in SOURCES.items():

        print(f"处理源: {source_id} - {url}")

        content = download_m3u(url)

        if content:

            channels = parse_m3u_content(content, source_id)

            

            # 合并到总列表

            for category, channel_list in channels.items():

                if category not in all_channels:

                    all_channels[category] = []

                all_channels[category].extend(channel_list)

    

    print("频道收集完成，开始写入文件...")

    

    # 写入输出文件

    write_output_file(all_channels)

    

    # 统计信息

    total_channels = sum(len(channels) for channels in all_channels.values())

    print(f"任务完成！共收集 {total_channels} 个频道")

    

    for category, channels in all_channels.items():

        print(f"{category}: {len(channels)} 个频道")




if __name__ == "__main__":

    main()
