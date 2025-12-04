#!/usr/bin/env python3
"""
IPTV直播源自动生成工具
功能：从多个来源获取IPTV直播源并生成M3U文件
support：手动更新和通过GitHub Actions工作流定时更新
"""

import asyncio
import re
import time
import requests
import datetime
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iptv_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 频道分类
CHANNEL_CATEGORIES = {
    "4K频道": ['CCTV4K', 'CCTV8K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K','广东卫视4K', '四川卫视4K',
                 '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K',
                 '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],

    "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                 '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '卫生健康','电视指南'],
    "卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视',
                 '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视',
                 '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视',
                 '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育',
                 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育'],

    "北京专属频道": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻',
                 '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV', '北京卡酷少儿'],

    "山东专属频道": ['山东卫视', '山东齐鲁', '山东综艺', '山东少儿', '山东生活',
                 '山东新闻', '山东国际', '山东体育', '山东文旅', '山东农科'],

    "港澳频道": ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影'],

    "电影频道": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场', '星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影', '超级电影'],
    "儿童频道": ['动漫秀场', '哒啵电竞', '黑莓动画', '卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通'],
    "iHOT频道": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教',
                 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈', 'iHOT爱科学', 'iHOT爱动漫'],
    "综合频道": ['重温经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活',
                 '求索动物', '睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论',
                 '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云', '金色学堂', '法治天地', '哒啵赛事'],
    "体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
    "剧场频道": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],
}

# 频道映射（别名 -> 规范名）
CHANNEL_MAPPING = {
    # 4K频道
    "CCTV4K": ["CCTV 4K", "CCTV-4K超高清頻道", "CCTV4K超高清頻道", "CCTV-4K"],
    "CCTV8K": ["CCTV 8K", "CCTV-8K超高清頻道", "CCTV8K超高清頻道", "CCTV-8K"],
    "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
    "北京卫视4K": ["北京卫视 4K", "北京卫视4K超高清", "北京卫视-4K"],
    "北京IPTV4K": ["北京IPTV 4K", "北京IPTV-4K"],
    "湖南卫视4K": ["湖南卫视 4K", "湖南卫视-4K"],
    "山东卫视4K": ["山东卫视 4K", "山东卫视-4K"],
    "广东卫视4K": ["广东卫视 4K", "广东卫视-4K"],
    "四川卫视4K": ["四川卫视 4K", "四川卫视-4K"],
    "浙江卫视4K": ["浙江卫视 4K", "浙江卫视-4K"],
    "江苏卫视4K": ["江苏卫视 4K", "江苏卫视-4K"],
    "东方卫视4K": ["东方卫视 4K", "东方卫视-4K"],
    "深圳卫视4K": ["深圳卫视 4K", "深圳卫视-4K"],
    "河北卫视4K": ["河北卫视 4K", "河北卫视-4K"],
    "峨眉电影4K": ["峨眉电影 4K", "峨眉电影-4K"],
    "求索4K": ["求索 4K", "求索-4K"],
    "咪视界4K": ["咪视界 4K", "咪视界-4K"],
    "欢笑剧场4K": ["欢笑剧场 4K", "欢笑剧场-4K"],
    "苏州4K": ["苏州 4K", "苏州-4K"],
    "至臻视界4K": ["至臻视界 4K", "至臻视界-4K"],
    "南国都市4K": ["南国都市 4K", "南国都市-4K"],
    "翡翠台4K": ["翡翠台 4K", "翡翠台-4K"],
    "百事通电影4K": ["百事通电影 4K", "百事通电影-4K"],
    "百事通少儿4K": ["百事通少儿 4K", "百事通少儿-4K"],
    "百事通纪实4K": ["百事通纪实 4K", "百事通纪实-4K"],
    "华数爱上4K": ["华数爱上 4K", "爱上 4K", "爱上4K",  "爱上-4K", "华数爱上-4K"],

    # 央视频道
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1综合", "CCTV-1 综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 财经", "CCTV-2 财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 综艺", "CCTV-3 综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4a", "CCTV4A", "CCTV4 中文国际", "CCTV-4 中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲 HD", "CCTV-4 欧洲", "CCTV4o", "CCTV4O", "CCTV-4 中文欧洲", "CCTV4中文欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4美洲 HD", "CCTV-4 美洲", "CCTV4m", "CCTV4M", "CCTV-4 中文美洲", "CCTV4中文美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 体育", "CCTV-5 体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ 体育赛事", "CCTV-5+ 体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 电影", "CCTV-6 电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 国防军事", "CCTV-7 国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 电视剧", "CCTV-8 电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 纪录", "CCTV-9 纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 科教", "CCTV-10 科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 戏曲", "CCTV-11 戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 社会与法", "CCTV-12 社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 新闻", "CCTV-13 新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 少儿", "CCTV-14 少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 音乐", "CCTV-15 音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 奥林匹克", "CCTV16 奥林匹克"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 农业农村", "CCTV-17 农业农村"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],

    # 卫视频道
    "山东卫视": ["山东卫视 HD", "山东台", "山东卫视高清"],
    "浙江卫视": ["浙江卫视 HD", "浙江台", "浙江卫视高清"],
    "江苏卫视": ["江苏卫视 HD", "江苏台", "江苏卫视高清"],
    "东方卫视": ["东方卫视 HD", "东方台", "上海东方卫视", "东方卫视高清"],
    "深圳卫视": ["深圳卫视 HD", "深圳台", "深圳卫视高清"],
    "北京卫视": ["北京卫视 HD", "北京台", "北京卫视高清"],
    "广东卫视": ["广东卫视 HD", "广东台", "广东卫视高清"],
    "广西卫视": ["广西卫视 HD", "广西台", "广西卫视高清"],
    "东南卫视": ["东南卫视 HD", "东南台", "福建东南卫视", "东南卫视高清"],
    "海南卫视": ["海南卫视 HD", "海南台", "海南卫视高清"],
    "河北卫视": ["河北卫视 HD", "河北台", "河北卫视高清"],
    "河南卫视": ["河南卫视 HD", "河南台", "河南卫视高清"],
    "湖北卫视": ["湖北卫视 HD", "湖北台", "湖北卫视高清"],
    "江西卫视": ["江西卫视 HD", "江西台", "江西卫视高清"],
    "四川卫视": ["四川卫视 HD", "四川台", "四川卫视高清"],
    "重庆卫视": ["重庆卫视 HD", "重庆台", "重庆卫视高清"],
    "贵州卫视": ["贵州卫视 HD", "贵州台", "贵州卫视高清"],
    "云南卫视": ["云南卫视 HD", "云南台", "云南卫视高清"],
    "天津卫视": ["天津卫视 HD", "天津台", "天津卫视高清"],
    "安徽卫视": ["安徽卫视 HD", "安徽台", "安徽卫视高清"],
    "湖南卫视": ["湖南卫视 HD", "湖南台", "湖南卫视高清"],
    "辽宁卫视": ["辽宁卫视 HD", "辽宁台", "辽宁卫视高清"],
    "黑龙江卫视": ["黑龙江卫视 HD", "黑龙江台", "黑龙江卫视高清"],
    "吉林卫视": ["吉林卫视 HD", "吉林台", "吉林卫视高清"],
    "内蒙古卫视": ["内蒙古卫视 HD", "内蒙古台", "内蒙古卫视高清"],
    "宁夏卫视": ["宁夏卫视 HD", "宁夏台", "宁夏卫视高清"],
    "山西卫视": ["山西卫视 HD", "山西台", "山西卫视高清"],
    "陕西卫视": ["陕西卫视 HD", "陕西台", "陕西卫视高清"],
    "甘肃卫视": ["甘肃卫视 HD", "甘肃台", "甘肃卫视高清"],
    "青海卫视": ["青海卫视 HD", "青海台", "青海卫视高清"],
    "新疆卫视": ["新疆卫视 HD", "新疆台", "新疆卫视高清"],
    "西藏卫视": ["西藏卫视 HD", "西藏台", "西藏卫视高清"],
    "三沙卫视": ["三沙卫视 HD", "三沙台", "三沙卫视高清"],
    "厦门卫视": ["厦门卫视 HD", "厦门台", "厦门卫视高清"],
    "兵团卫视": ["兵团卫视 HD", "兵团台", "兵团卫视高清"],
    "延边卫视": ["延边卫视 HD", "延边台", "延边卫视高清"],
    "安多卫视": ["安多卫视 HD", "安多台", "安多卫视高清"],
    "康巴卫视": ["康巴卫视 HD", "康巴台", "康巴卫视高清"],
    "农林卫视": ["农林卫视 HD", "农林台", "农林卫视高清"],
    "山东教育": ["山东教育台", "山东教育卫视"],
    "CETV1": ["CETV-1", "中国教育1", "中国教育台1"],
    "CETV2": ["CETV-2", "中国教育2", "中国教育台2"],
    "CETV3": ["CETV-3", "中国教育3", "中国教育台3"],
    "CETV4": ["CETV-4", "中国教育4", "中国教育台4"],
    "早期教育": ["CETV-早期教育", "中国教育台-早期教育"],
}

# 默认直播源URL
# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES
default_sources = UNIFIED_SOURCES

# 本地直播源文件
default_local_sources = [
    "ipzyauto.txt",
]

# 用户自定义直播源URL（可在本地添加）
user_sources = []

# 获取URL列表
def get_urls_from_file(file_path):
    """从文件中读取URL列表"""
    urls = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"读取URL文件时出错: {e}")
    return urls

# 检查URL是否有效
def check_url(url, timeout=5):
    """检查URL是否可访问"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

# 格式化时间间隔
def format_interval(seconds):
    """格式化时间间隔"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)}分{int(seconds)}秒"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}时{int(minutes)}分{int(seconds)}秒"

# 获取IP地址
def get_ip_address():
    """获取本地IP地址"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 检查IPv6支持
def check_ipv6_support():
    """检查系统是否支持IPv6"""
    try:
        import socket
        socket.inet_pton(socket.AF_INET6, '::1')
        return True
    except:
        return False

# 从M3U文件中提取频道信息
def extract_channels_from_m3u(content):
    """从M3U内容中提取频道信息"""
    channels = defaultdict(list)
    pattern = r'#EXTINF:.*?tvg-name="([^"]*)".*?(?:group-title="([^"]*)")?,([^\n]+)\n(http[^\n]+)'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        tvg_name = match[0].strip() if match[0] else match[2].strip()
        channel_name = match[2].strip()
        url = match[3].strip()

        # 规范化频道名称
        normalized_name = normalize_channel_name(channel_name)
        if normalized_name:
            # 获取频道分类
            category = get_channel_category(normalized_name)
            channels[category].append((normalized_name, url))
        else:
            # 未规范化的频道放在其他频道
            channels["其他频道"].append((channel_name, url))

    return channels

# 获取频道分类
def get_channel_category(channel_name):
    """获取频道所属的分类"""
    for category, channels in CHANNEL_CATEGORIES.items():
        if channel_name in channels:
            return category
    return "其他频道"

# 规范化频道名称
def normalize_channel_name(name):
    """将频道名称规范化为标准名称"""
    name = name.strip()
    # 检查是否是标准名称
    for standard_name in CHANNEL_MAPPING:
        if name == standard_name:
            return standard_name
    # 检查是否是别名
    for standard_name, aliases in CHANNEL_MAPPING.items():
        if name in aliases:
            return standard_name
    return None

# 从URL获取M3U内容
def fetch_m3u_content(url):
    """从URL获取M3U内容"""
    try:
        print(f"正在获取: {url}")
        # 添加verify=False参数来跳过SSL证书验证
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"获取 {url} 时出错: {e}")
        return None

# 从本地文件获取M3U内容
def fetch_local_m3u_content(file_path):
    """从本地文件获取M3U内容"""
    try:
        print(f"正在读取本地文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取本地文件 {file_path} 时出错: {e}")
        return None

# 生成M3U文件
def generate_m3u_file(channels, output_path):
    """生成M3U文件"""
    print(f"正在生成 {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头
        f.write("#EXTM3U x-tvg-url=\"https://kakaxi-1.github.io/IPTV/epg.xml\"\n")

        # 按CHANNEL_CATEGORIES中定义的顺序写入分类
        for category in CHANNEL_CATEGORIES:
            if category in channels:
                for channel_name, url in channels[category]:
                    # 写入频道信息
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{url}\n")

        # 最后写入其他频道
        if "其他频道" in channels:
            for channel_name, url in channels["其他频道"]:
                # 写入频道信息
                f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"其他频道\",{channel_name}\n")
                f.write(f"{url}\n")

    print(f"✅ 成功生成 {output_path}")
    return True

# 生成TXT文件
def generate_txt_file(channels, output_path):
    """生成TXT文件"""
    print(f"正在生成 {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入文件头注释
        f.write(f"# IPTV直播源列表\n")
        f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 格式: 频道名称,播放URL\n")
        f.write("# 按分组排列\n")
        f.write("\n")

        # 写入频道分类说明
        f.write("# 频道分类: 4K频道,央视频道,卫视频道,北京专属频道,山东专属频道,港澳频道,电影频道,儿童频道,iHOT频道,综合频道,体育频道,剧场频道,其他频道\n")
        f.write("\n")

        # 按CHANNEL_CATEGORIES中定义的顺序写入分类
        for category in CHANNEL_CATEGORIES:
            if category in channels and channels[category]:
                # 写入分组标题，添加,#genre#后缀
                f.write(f"#{category}#,genre#\n")

                # 写入该分组下的所有频道
                for channel_name, url in channels[category]:
                    f.write(f"{channel_name},{url}\n")

                # 分组之间添加空行
                f.write("\n")

        # 最后写入其他频道
        if "其他频道" in channels and channels["其他频道"]:
            # 写入分组标题，添加,#genre#后缀
            f.write("#其他频道#,#genre#\n")

            # 写入该分组下的所有频道
            for channel_name, url in channels["其他频道"]:
                f.write(f"{channel_name},{url}\n")

            # 分组之间添加空行
            f.write("\n")

    print(f"✅ 成功生成 {output_path}")
    return True

# 从本地TXT文件提取频道信息
def extract_channels_from_txt(file_path):
    """从本地TXT文件提取频道信息"""
    channels = defaultdict(list)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 只跳过格式不正确的行（不以#开头但包含,#genre#的行）
                # 正确格式的分组标题行（以#开头且包含,#genre#）已经在上面的line.startswith('#')条件中被跳过了
                if not line.startswith('#') and (line.endswith(',#genre#') or line.endswith(',genre#')):
                    continue

                # 解析频道信息（格式：频道名称,URL）
                if ',' in line:
                    channel_name, url = line.split(',', 1)
                    channel_name = channel_name.strip()
                    url = url.strip()

                    # 跳过无效的URL
                    if not url.startswith(('http://', 'https://')):
                        continue

                    # 规范化频道名称
                    normalized_name = normalize_channel_name(channel_name)
                    if normalized_name:
                        # 获取频道分类
                        category = get_channel_category(normalized_name)
                        channels[category].append((normalized_name, url))
                    else:
                        # 未规范化的频道放在其他频道
                        channels["其他频道"].append((channel_name, url))
    except Exception as e:
        print(f"解析本地文件 {file_path} 时出错: {e}")

    return channels

# 合并直播源
def merge_sources(sources, local_files):
    """合并多个直播源"""
    all_channels = defaultdict(list)
    seen = set()

    # 处理远程直播源
    for source_url in sources:
        content = fetch_m3u_content(source_url)
        if content:
            channels = extract_channels_from_m3u(content)
            for group_title, channel_list in channels.items():
                for channel_name, url in channel_list:
                    # 去重
                    if (channel_name, url) not in seen:
                        all_channels[group_title].append((channel_name, url))
                        seen.add((channel_name, url))

    # 处理本地直播源文件
    for file_path in local_files:
        if os.path.exists(file_path):
            local_channels = extract_channels_from_txt(file_path)
            for group_title, channel_list in local_channels.items():
                for channel_name, url in channel_list:
                    # 去重
                    if (channel_name, url) not in seen:
                        all_channels[group_title].append((channel_name, url))
                        seen.add((channel_name, url))

    return all_channels

# 忽略requests的SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_iptv_sources():
    """更新IPTV直播源"""
    logger.info("🚀 IPTV直播源自动生成工具")
    logger.info(f"📅 运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # 合并所有直播源
    all_sources = default_sources + user_sources
    logger.info(f"📡 正在获取{len(all_sources)}个远程直播源...")
    logger.info(f"💻 正在读取{len(default_local_sources)}个本地直播源文件...")

    start_time = time.time()
    all_channels = merge_sources(all_sources, default_local_sources)

    # 统计频道数量
    total_channels = sum(len(channel_list) for channel_list in all_channels.values())
    total_groups = len(all_channels)

    logger.info("=" * 50)
    logger.info(f"📊 统计信息:")
    logger.info(f"📡 直播源数量: {len(all_sources)}")
    logger.info(f"📺 频道组数: {total_groups}")
    logger.info(f"📚 总频道数: {total_channels}")
    logger.info(f"⏱️  耗时: {format_interval(time.time() - start_time)}")
    logger.info("=" * 50)

    # 显示频道组信息
    logger.info("📋 频道组详情:")
    for group_title, channel_list in all_channels.items():
        logger.info(f"   {group_title}: {len(channel_list)}个频道")

    # 生成M3U文件
    output_file_m3u = "jieguo.m3u"  # 将输出文件改为jieguo.m3u
    # 生成TXT文件
    output_file_txt = "jieguo.txt"  # 新增TXT格式输出文件

    if generate_m3u_file(all_channels, output_file_m3u) and generate_txt_file(all_channels, output_file_txt):
        logger.info(f"🎉 任务完成！")
        return True
    else:
        logger.error("💥 生成文件失败！")
        return False

def main():
    """主函数"""
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        # 手动更新模式
        update_iptv_sources()
    else:
        # 显示帮助信息
        print("=" * 60)
        print("      IPTV直播源自动生成工具")
        print("=" * 60)
        print("功能：")
        print("  1. 从多个来源获取IPTV直播源")
        print("  2. 生成M3U和TXT格式的直播源文件")
        print("  3. 支持手动更新和通过GitHub Actions工作流定时更新")
        print("")
        print("使用方法：")
        print("  python IP-TV.py --update     # 立即手动更新直播源")
        print("  通过GitHub Actions工作流自动更新")
        print("")
        print("输出文件：")
        print("  - jieguo.m3u   # M3U格式的直播源文件")
        print("  - jieguo.txt   # TXT格式的直播源文件")
        print("  - iptv_update.log  # 更新日志文件")
        print("=" * 60)

if __name__ == "__main__":
    main()
