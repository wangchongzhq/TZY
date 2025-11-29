import os
import re
import requests
import concurrent.futures
import time
import sys
import logging
import argparse

# 配置日志记录
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler('tvzy.log', encoding='utf-8')
                    ])
logger = logging.getLogger(__name__)

# 配置参数
MAX_WORKERS = 10
TIMEOUT = 10
MIN_LINES_PER_CHANNEL = 10
MAX_LINES_PER_CHANNEL = 90
# 默认输出文件名
DEFAULT_OUTPUT_FILE = 'tzydauto.txt'
# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='电视直播线路收集和处理脚本')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT_FILE, help=f'输出文件名（默认: {DEFAULT_OUTPUT_FILE}）')
    parser.add_argument('--test', action='store_true', help='测试模式，只检查脚本基本功能')
    return parser.parse_args()

# 获取命令行参数
args = parse_args()
OUTPUT_FILE = args.output

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# 数据源列表
GITHUB_SOURCES = [
    # 有效的中国电视频道源
    "http://tv.html-5.me/i/9390107.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://freetv.fun/test_channels_new.txt",
    "https://ghfast.top/https://github.com/kimwang1978/collect-txt/blob/main/bbxx.txt",
    "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt",
    "https://gitee.com/xiao-ping2/iptv-api/raw/master/output/xp_result.txt",
    # 其他稳定的IPTV源
    "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u",
    # 优质高清源
    "https://ghfast.top/https://raw.githubusercontent.com/LongLiveTheKing/web-data/master/data/ip.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/HeJiawen01/IPTV/main/IPTV.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/chenjie/ip.txt/master/ip.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/chnadsl/IPTV/main/IPTV.m3u"
]

# 频道分类 - 注意：顺序必须严格按照要求的顺序
CHANNEL_CATEGORIES = {
    "4K频道": ['CCTV4K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K', '广东卫视4K', '四川卫视4K',
                '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K',
                '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],
    
    "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '北京纪实科教',
                '卫生健康', '电视指南'],
    "卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视',
                '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视',
                '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视',
                '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育',
                'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育'],

    "北京专属频道": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻',
                '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV'],

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
    "剧场频道": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],
    "体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
    "音乐频道": ['音乐频道', '风云音乐', 'CCTV音乐', 'CHANNEL[V]', '音乐Tai', '音乐台', 'MTV', 'MTV中文', '华语音乐', '流行音乐', '古典音乐']
}

# 频道映射字典
CHANNEL_MAPPING = {}

# 填充频道映射字典
for category, channels in CHANNEL_CATEGORIES.items():
    for channel in channels:
        CHANNEL_MAPPING[channel] = [channel]

additional_mappings = {
    "CCTV4K": ["CCTV 4K", "CCTV-4K"],
    "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
    "北京卫视4K": ["北京卫视 4K", "北京卫视-4K"],
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
    "华数爱上4K": ["华数爱上 4K", "爱上 4K", "爱上4K", "爱上-4K", "华数爱上-4K"],
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
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-央视高网", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "央视文化精品", "央视文化精品"],
    "北京纪实科教": ["CCTV-北京纪实科教", "CCTV北京纪实科教"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "山东卫视": ["山东卫视", "山东卫视 HD", "山东卫视高清"],
    "浙江卫视": ["浙江卫视", "浙江卫视 HD", "浙江卫视高清"],
    "江苏卫视": ["江苏卫视", "江苏卫视 HD", "江苏卫视高清"],
    "东方卫视": ["东方卫视", "东方卫视 HD", "东方卫视高清"],
    "深圳卫视": ["深圳卫视", "深圳卫视 HD", "深圳卫视高清"],
    "北京卫视": ["北京卫视", "北京卫视 HD", "北京卫视高清"],
    "广东卫视": ["广东卫视", "广东卫视 HD", "广东卫视高清"],
    "广西卫视": ["广西卫视", "广西卫视 HD", "广西卫视高清"],
    "东南卫视": ["东南卫视", "东南卫视 HD", "东南卫视高清"],
    "海南卫视": ["海南卫视", "海南卫视 HD", "海南卫视高清", "旅游卫视", "旅游卫视 HD"],
    "河北卫视": ["河北卫视", "河北卫视 HD", "河北卫视高清"],
    "河南卫视": ["河南卫视", "河南卫视 HD", "河南卫视高清"],
    "湖北卫视": ["湖北卫视", "湖北卫视 HD", "湖北卫视高清"],
    "江西卫视": ["江西卫视", "江西卫视 HD", "江西卫视高清"],
    "四川卫视": ["四川卫视", "四川卫视 HD", "四川卫视高清"],
    "重庆卫视": ["重庆卫视", "重庆卫视 HD", "重庆卫视高清"],
    "贵州卫视": ["贵州卫视", "贵州卫视 HD", "贵州卫视高清"],
    "云南卫视": ["云南卫视", "云南卫视 HD", "云南卫视高清"],
    "天津卫视": ["天津卫视", "天津卫视 HD", "天津卫视高清"],
    "安徽卫视": ["安徽卫视", "安徽卫视 HD", "安徽卫视高清"],
    "湖南卫视": ["湖南卫视", "湖南卫视 HD", "湖南卫视高清"],
    "辽宁卫视": ["辽宁卫视", "辽宁卫视 HD", "辽宁卫视高清"],
    "黑龙江卫视": ["黑龙江卫视", "黑龙江卫视 HD", "黑龙江卫视高清"],
    "吉林卫视": ["吉林卫视", "吉林卫视 HD", "吉林卫视高清"],
    "内蒙古卫视": ["内蒙古卫视", "内蒙古卫视 HD", "内蒙古卫视高清"],
    "宁夏卫视": ["宁夏卫视", "宁夏卫视 HD", "宁夏卫视高清"],
    "山西卫视": ["山西卫视", "山西卫视 HD", "山西卫视高清"],
    "陕西卫视": ["陕西卫视", "陕西卫视 HD", "陕西卫视高清"],
    "甘肃卫视": ["甘肃卫视", "甘肃卫视 HD", "甘肃卫视高清"],
    "青海卫视": ["青海卫视", "青海卫视 HD", "青海卫视高清"],
    "新疆卫视": ["新疆卫视", "新疆卫视 HD", "新疆卫视高清"],
    "西藏卫视": ["西藏卫视", "西藏卫视 HD", "西藏卫视高清"],
    "三沙卫视": ["三沙卫视", "三沙卫视 HD", "三沙卫视高清"],
    "厦门卫视": ["厦门卫视", "厦门卫视 HD", "厦门卫视高清"],
    "兵团卫视": ["兵团卫视", "兵团卫视 HD", "兵团卫视高清"],
    "延边卫视": ["延边卫视", "延边卫视 HD", "延边卫视高清"],
    "安多卫视": ["安多卫视", "安多卫视 HD", "安多卫视高清"],
    "康巴卫视": ["康巴卫视", "康巴卫视 HD", "康巴卫视高清"],
    "农林卫视": ["农林卫视", "农林卫视 HD", "农林卫视高清"],
    "山东教育": ["山东教育", "山东教育 HD", "山东教育高清"],
    "CETV1": ["CETV-1", "中国教育1", "中国教育-1", "中国教育电视台1"],
    "CETV2": ["CETV-2", "中国教育2", "中国教育-2", "中国教育电视台2"],
    "CETV3": ["CETV-3", "中国教育3", "中国教育-3", "中国教育电视台3"],
    "CETV4": ["CETV-4", "中国教育4", "中国教育-4", "中国教育电视台4"],
    "早期教育": ["早期教育", "早教", "幼儿教育"],
    "北京财经": ["北京财经", "BTV财经", "BTV-财经"],
    "北京纪实": ["北京纪实", "BTV纪实", "BTV-纪实"],
    "北京生活": ["北京生活", "BTV生活", "BTV-生活"],
    "北京体育休闲": ["北京体育休闲", "BTV体育休闲", "BTV-体育休闲"],
    "北京国际": ["北京国际", "BTV国际", "BTV-国际"],
    "北京文艺": ["北京文艺", "BTV文艺", "BTV-文艺"],
    "北京新闻": ["北京新闻", "BTV新闻", "BTV-新闻"],
    "北京淘电影": ["北京淘电影", "BTV淘电影"],
    "北京淘剧场": ["北京淘剧场", "BTV淘剧场"],
    "北京淘4K": ["北京淘4K", "BTV淘4K"],
    "北京淘娱乐": ["北京淘娱乐", "BTV淘娱乐"],
    "北京淘BABY": ["北京淘BABY", "BTV淘BABY"],
    "北京萌宠TV": ["北京萌宠TV", "BTV萌宠TV"],
    "山东齐鲁": ["山东齐鲁", "齐鲁频道"],
    "山东综艺": ["山东综艺", "综艺频道"],
    "山东少儿": ["山东少儿", "少儿频道"],
    "山东生活": ["山东生活", "生活频道"],
    "山东新闻": ["山东新闻", "新闻频道"],
    "山东国际": ["山东国际", "国际频道"],
    "山东体育": ["山东体育", "体育频道"],
    "山东文旅": ["山东文旅", "文旅频道"],
    "山东农科": ["山东农科", "农科频道"],
    "凤凰中文": ["凤凰中文", "凤凰卫视中文台"],
    "凤凰资讯": ["凤凰资讯", "凤凰卫视资讯台"],
    "凤凰香港": ["凤凰香港", "凤凰卫视香港台"],
    "凤凰电影": ["凤凰电影", "凤凰卫视电影台"],
    "CHC动作电影": ["CHC动作电影", "动作电影"],
    "CHC家庭影院": ["CHC家庭影院", "家庭影院"],
    "CHC影迷电影": ["CHC影迷电影", "影迷电影"],
    "淘电影": ["淘电影", "电影"],
    "淘精彩": ["淘精彩", "精彩"],
    "淘剧场": ["淘剧场", "剧场"],
    "星空卫视": ["星空卫视", "星空"],
    "黑莓电影": ["黑莓电影", "电影"],
    "东北热剧": ["东北热剧", "热剧"],
    "中国功夫": ["中国功夫", "功夫"],
    "动作电影": ["动作电影", "电影动作"],
    "超级电影": ["超级电影", "电影超级"],
    "动漫秀场": ["动漫秀场", "动漫"],
    "哒啵电竞": ["哒啵电竞", "电竞"],
    "黑莓动画": ["黑莓动画", "动画"],
    "卡酷少儿": ["卡酷少儿", "卡酷"],
    "金鹰卡通": ["金鹰卡通", "金鹰"],
    "优漫卡通": ["优漫卡通", "优漫"],
    "哈哈炫动": ["哈哈炫动", "哈哈"],
    "嘉佳卡通": ["嘉佳卡通", "嘉佳"],
    "iHOT爱喜剧": ["iHOT爱喜剧", "爱喜剧"],
    "iHOT爱科幻": ["iHOT爱科幻", "爱科幻"],
    "iHOT爱院线": ["iHOT爱院线", "爱院线"],
    "iHOT爱悬疑": ["iHOT爱悬疑", "爱悬疑"],
    "iHOT爱历史": ["iHOT爱历史", "爱历史"],
    "iHOT爱谍战": ["iHOT爱谍战", "爱谍战"],
    "iHOT爱旅行": ["iHOT爱旅行", "爱旅行"],
    "iHOT爱幼教": ["iHOT爱幼教", "爱幼教"],
    "iHOT爱玩具": ["iHOT爱玩具", "爱玩具"],
    "iHOT爱体育": ["iHOT爱体育", "爱体育"],
    "iHOT爱赛车": ["iHOT爱赛车", "爱赛车"],
    "iHOT爱浪漫": ["iHOT爱浪漫", "爱浪漫"],
    "iHOT爱奇谈": ["iHOT爱奇谈", "爱奇谈"],
    "iHOT爱科学": ["iHOT爱科学", "爱科学"],
    "iHOT爱动漫": ["iHOT爱动漫", "爱动漫"],
    "重温经典": ["重温经典", "经典"],
    "CHANNEL[V]": ["CHANNEL[V]", "Channel V"],
    "求索纪录": ["求索纪录", "纪录"],
    "求索科学": ["求索科学", "科学"],
    "求索生活": ["求索生活", "生活"],
    "求索动物": ["求索动物", "动物"],
    "睛彩青少": ["睛彩青少", "青少"],
    "睛彩竞技": ["睛彩竞技", "竞技"],
    "睛彩篮球": ["睛彩篮球", "篮球"],
    "睛彩广场舞": ["睛彩广场舞", "广场舞"],
    "金鹰纪实": ["金鹰纪实", "纪实"],
    "快乐垂钓": ["快乐垂钓", "垂钓"],
    "茶频道": ["茶频道", "茶"],
    "军事评论": ["军事评论", "军事"],
    "军旅剧场": ["军旅剧场", "军旅"],
    "乐游": ["乐游", "旅游"],
    "生活时尚": ["生活时尚", "时尚"],
    "都市剧场": ["都市剧场", "都市"],
    "欢笑剧场": ["欢笑剧场", "欢笑"],
    "游戏风云": ["游戏风云", "游戏"],
    "金色学堂": ["金色学堂", "学堂"],
    "法治天地": ["法治天地", "法治"],
    "哒啵赛事": ["哒啵赛事", "赛事"],
    "古装剧场": ["古装剧场", "古装"],
    "家庭剧场": ["家庭剧场", "家庭"],
    "惊悚悬疑": ["惊悚悬疑", "悬疑"],
    "明星大片": ["明星大片", "大片"],
    "欢乐剧场": ["欢乐剧场", "欢乐"],
    "海外剧场": ["海外剧场", "海外"],
    "潮妈辣婆": ["潮妈辣婆", "潮妈"],
    "爱情喜剧": ["爱情喜剧", "爱情"],
    "超级电视剧": ["超级电视剧", "电视剧"],
    "超级综艺": ["超级综艺", "综艺"],
    "金牌综艺": ["金牌综艺", "金牌"],
    "武搏世界": ["武搏世界", "武搏"],
    "农业致富": ["农业致富", "农业"],
    "炫舞未来": ["炫舞未来", "炫舞"],
    "精品体育": ["精品体育", "精品"],
    "精品大剧": ["精品大剧", "大剧"],
    "精品纪录": ["精品纪录", "纪录"],
    "精品萌宠": ["精品萌宠", "萌宠"],
    "怡伴健康": ["怡伴健康", "健康"],
    "天元围棋": ["天元围棋", "围棋"],
    "魅力足球": ["魅力足球", "足球"],
    "五星体育": ["五星体育", "五星"],
    "劲爆体育": ["劲爆体育", "劲爆"],
    "超级体育": ["超级体育", "超级"],
    "音乐频道": ["音乐频道", "音乐"],
    "CCTV音乐": ["CCTV音乐", "音乐"],
    "CHANNEL[V]": ["CHANNEL[V]", "Channel V"],
    "音乐Tai": ["音乐Tai", "音乐台"],
    "音乐台": ["音乐台", "音乐"],
    "MTV": ["MTV", "音乐电视"],
    "MTV中文": ["MTV中文", "中文MTV"],
    "华语音乐": ["华语音乐", "华语"],
    "流行音乐": ["流行音乐", "流行"],
    "古典音乐": ["古典音乐", "古典"]
}

# 添加额外的映射关系
for channel, aliases in additional_mappings.items():
    if channel in CHANNEL_MAPPING:
        CHANNEL_MAPPING[channel].extend(aliases)

# 建立频道到类别的映射
CHANNEL_TO_CATEGORY = {}
for category, channels in CHANNEL_CATEGORIES.items():
    for channel in channels:
        CHANNEL_TO_CATEGORY[channel] = category

# 类别顺序列表
CATEGORY_ORDER = list(CHANNEL_CATEGORIES.keys())

# 清晰度正则表达式 - 增强版，更好地识别高清线路
HD_PATTERNS = [
    # 4K及以上
    r'[48]k',
    r'2160[pdi]',
    r'uhd',
    r'超高清',
    r'4k',
    # 2K
    r'1440[pdi]',
    r'qhd',
    # 1080P及以上
    r'1080[pdi]',
    r'fhd',
    # 其他高清标识
    r'高清',
    r'超清',
    r'hd',
    r'high.?definition',
    r'high.?def',
    # 特定的高清标识
    r'hdmi',
    r'蓝光',
    r'blue.?ray',
    r'hd.?live',
    # 码率标识
    r'[89]m',
    r'[1-9]\d+m',
    # 特定的URL参数标识
    r'quality=high',
    r'resolution=[1-9]\d{3}',
    r'hd=true',
    r'fhd=true'
]

HD_REGEX = re.compile('|'.join(HD_PATTERNS), re.IGNORECASE)

def fetch_content(url, timeout=10, max_retries=3):
    """获取URL内容，支持超时和重试"""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout, headers=HEADERS)
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            logger.info(f"成功获取 {url}")
            return response.text
        except requests.RequestException as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"获取 {url} 失败: {e}")
                return None
            logger.warning(f"重试 ({retries}/{max_retries}) 获取 {url}...")
            time.sleep(2)  # 重试前等待2秒

def is_high_quality(line):
    """判断线路是否为高清线路（1080P以上）"""
    # 优先检查是否明确包含1080p或更高清的标识
    high_def_patterns = re.compile(r'(1080[pdi]|1440[pdi]|2160[pdi]|[48]k|fhd|uhd|超高清|4k)', re.IGNORECASE)
    if high_def_patterns.search(line):
        return True
    
    # 其次检查是否包含其他高清标识
    if HD_REGEX.search(line):
        # 排除一些可能误判的情况
        low_quality_patterns = re.compile(r'(360|480|576|标清|sd|low)', re.IGNORECASE)
        if not low_quality_patterns.search(line):
            return True
    
    # 检查URL中是否包含特定的高清参数
    url_high_patterns = re.compile(r'(\bhd\b|quality=high|res=[1-9]\d{3}|bitrate=[8-9]\d{2}|bitrate=\d{4,})', re.IGNORECASE)
    if url_high_patterns.search(line):
        return True
    
    return False

def normalize_channel_name(name):
    """标准化频道名称，进行精确匹配、包含匹配、反向匹配和关键词匹配"""
    if not name:
        logger.warning("尝试标准化空频道名称")
        return None
    
    # 移除一些常见的后缀或标识符
    name = name.strip()
    for suffix in ['高清', 'HD', '(高清)', '[高清]', '(HD)', '[HD]', '-HD', '·HD', '\t']:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    try:
        # 精确匹配
        if name in CHANNEL_MAPPING:
            return name
        
        # 包含匹配 - 检查频道名是否包含规范名
        for canonical_name, aliases in CHANNEL_MAPPING.items():
            # 检查规范名是否在当前名称中
            if canonical_name in name:
                return canonical_name
            
            # 检查别名是否在当前名称中
            for alias in aliases:
                if alias in name:
                    return canonical_name
        
        # 反向匹配 - 检查规范名是否包含当前名称
        for canonical_name in CHANNEL_MAPPING:
            if name in canonical_name:
                return canonical_name
        
        # 关键词匹配 - 提取名称中的关键词进行匹配
        keywords = re.findall(r'[a-zA-Z0-9\u4e00-\u9fa5]+', name)
        for keyword in keywords:
            if keyword in CHANNEL_MAPPING:
                return keyword
        
        # 特殊处理CCTV频道
        cctv_match = re.search(r'CCTV(\d{1,2})', name, re.IGNORECASE)
        if cctv_match:
            cctv_num = cctv_match.group(1)
            canonical_cctv = f"CCTV{cctv_num}"
            if canonical_cctv in CHANNEL_MAPPING:
                return canonical_cctv
    except Exception as e:
        logger.error(f"标准化频道名称 '{name}' 时出错: {e}")
    
    # 无匹配，返回原始名称
    return None

def extract_channels(content):
    """从内容中提取频道信息"""
    if not content:
        logger.warning("尝试从空内容中提取频道信息")
        return []
    
    channels = []
    
    try:
        # 1. M3U格式
        if '#EXTM3U' in content:
            lines = content.splitlines()
            for i in range(len(lines)):
                if lines[i].startswith('#EXTINF:'):
                    # 提取频道名称
                    name_match = re.search(r',([^,]+)$', lines[i])
                    if name_match and i + 1 < len(lines):
                        name = name_match.group(1).strip()
                        url = lines[i + 1].strip()
                        if url.startswith(('http://', 'https://')):
                            channels.append((name, url))
        
        # 2. 文本格式: 频道名,URL
        elif ',' in content:
            lines = content.splitlines()
            for line in lines:
                if ',' in line and ('http://' in line or 'https://' in line):
                    try:
                        name, url = line.rsplit(',', 1)
                        name = name.strip()
                        url = url.strip()
                        if url.startswith(('http://', 'https://')):
                            channels.append((name, url))
                    except ValueError:
                        continue
        
        # 3. 每行一个URL，尝试从URL中提取信息
        else:
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith(('http://', 'https://')):
                    # 尝试从URL中提取名称
                    name = line.split('/')[-1].split('?')[0].split('#')[0]
                    channels.append((name, line))
        
        logger.info(f"成功提取了 {len(channels)} 个频道")
    except Exception as e:
        logger.error(f"提取频道信息时出错: {e}")
    
    return channels

def process_source(source_url):
    """处理单个数据源"""
    try:
        # 清理URL，移除可能的引号和空格
        url = source_url.strip('"`\' ')
        logger.info(f"开始处理数据源: {url}")
        content = fetch_content(url)
        if not content:
            logger.warning(f"数据源 {url} 没有返回内容或获取失败")
            return []
        
        channels = extract_channels(content)
        if not channels:
            logger.warning(f"从数据源 {url} 未提取到任何频道")
            return []
        
        # 过滤和标准化频道
        processed_channels = []
        for name, url in channels:
            # 检查URL和名称
            if not url or not url.startswith(('http://', 'https://')):
                continue
            
            # 过滤高清线路
            combined = name + ' ' + url
            if not is_high_quality(combined):
                continue
            
            # 标准化频道名称
            normalized_name = normalize_channel_name(name)
            if normalized_name:
                processed_channels.append((normalized_name, url))
        
        logger.info(f"从数据源 {url} 成功处理了 {len(processed_channels)} 个高清频道")
        return processed_channels
    except Exception as e:
        logger.error(f"处理数据源 {source_url} 时出错: {e}")
        return []

def sort_and_limit_lines(lines):
    """排序并限制线路数量，确保优先保留高质量线路"""
    # 更精确的清晰度排序函数
    def sort_key(line):
        name, url = line
        combined = (name + ' ' + url).lower()
        
        # 4K及以上 (最高优先级)
        if any(keyword in combined for keyword in ['4k', '2160p', '2160i', 'uhd', '超高清']):
            return (0, len(combined))  # 长度作为次要排序条件，更简洁的URL可能更好
        
        # 2K (第二优先级)
        elif any(keyword in combined for keyword in ['1440p', 'qhd', '2k']):
            return (1, len(combined))
        
        # 1080p/i (第三优先级)
        elif any(keyword in combined for keyword in ['1080p', '1080i', '1080d', 'fhd']):
            # 进一步细分：1080p优先于1080i
            if '1080p' in combined:
                return (2, 0, len(combined))
            else:
                return (2, 1, len(combined))
        
        # 高清 (第四优先级)
        elif any(keyword in combined for keyword in ['高清', 'hd', 'high definition']):
            return (3, len(combined))
        
        # 其他高清标识 (第五优先级)
        elif any(keyword in combined for keyword in ['超清', '蓝光', 'blue-ray']):
            return (4, len(combined))
        
        # 普通线路 (最低优先级)
        return (5, len(combined))
    
    # 排序
    sorted_lines = sorted(lines, key=sort_key)
    
    # 限制数量 - 确保在范围内
    if len(sorted_lines) < MIN_LINES_PER_CHANNEL:
        # 线路不足时，保留所有线路
        return sorted_lines
    elif len(sorted_lines) > MAX_LINES_PER_CHANNEL:
        # 线路过多时，只保留前MAX_LINES_PER_CHANNEL个
        return sorted_lines[:MAX_LINES_PER_CHANNEL]
    else:
        # 数量在合理范围内，全部保留
        return sorted_lines

def write_output_file(category_channels):
    """写入输出文件"""
    try:
        output_lines = []
        channel_count = 0
        source_count = 0
        
        # 按照指定的顺序遍历类别
        for category in CATEGORY_ORDER:
            if category not in category_channels:
                continue
            
            # 添加类别标记
            output_lines.append(f"#{category},#genre#")
            
            # 添加该类别的频道
            for channel_name, lines in category_channels[category].items():
                output_lines.append(f"##{channel_name}")
                channel_count += 1
                source_count += len(lines)
                for name, url in lines:
                    # 验证URL
                    if url and url.startswith(('http://', 'https://')):
                        output_lines.append(f"{name},{url}")
            
            # 在类别之间添加空行
            output_lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        logger.info(f"已成功生成 {OUTPUT_FILE}，共包含 {channel_count} 个频道，{source_count} 条线路")
        print(f"已成功生成 {OUTPUT_FILE}，共包含 {channel_count} 个频道，{source_count} 条线路")
        return True
    except Exception as e:
        logger.error(f"写入输出文件时出错: {e}")
        return False

def main():
    """主函数"""
    try:
        # 检查是否为测试模式
        if args.test:
            print("=== 测试模式 ===")
            logger.info("测试模式：开始基本功能检查...")
            logger.info(f"输出文件配置为: {OUTPUT_FILE}")
            
            # 检查必要的导入和配置
            logger.info("✓ 导入模块检查通过")
            logger.info(f"✓ 配置参数检查通过")
            
            # 检查数据源列表
            print(f"GITHUB_SOURCES变量存在，长度: {len(GITHUB_SOURCES)}")
            logger.info(f"✓ 数据源数量: {len(GITHUB_SOURCES)}")
            
            # 检查频道类别
            print(f"CHANNEL_CATEGORIES变量存在，长度: {len(CHANNEL_CATEGORIES)}")
            logger.info(f"✓ 频道类别数量: {len(CHANNEL_CATEGORIES)}")
            
            # 检查输出文件路径是否可写
            test_dir = os.path.dirname(OUTPUT_FILE) if os.path.dirname(OUTPUT_FILE) else '.'
            if os.access(test_dir, os.W_OK):
                logger.info("✓ 输出文件路径可写")
                print("测试模式检查完成：所有基本功能正常！")
                return True
            else:
                logger.error("✗ 输出文件路径不可写")
                print("测试模式检查失败：输出文件路径不可写")
                return False
        
        # 正常模式
        logger.info("开始收集和处理电视直播线路...")
        logger.info(f"输出文件将保存为: {OUTPUT_FILE}")
        start_time = time.time()
        
        # 并发处理所有数据源
        all_channels = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_source = {executor.submit(process_source, source): source for source in GITHUB_SOURCES}
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    channels = future.result()
                    all_channels.extend(channels)
                except Exception as e:
                    logger.error(f"处理 {source} 时发生异常: {e}")
        
        logger.info(f"总共收集到 {len(all_channels)} 条频道线路")
        
        # 按频道名称分组
        channel_map = {}
        for name, url in all_channels:
            if name not in channel_map:
                channel_map[name] = []
            channel_map[name].append((name, url))
        
        logger.info(f"去重后共有 {len(channel_map)} 个频道")
        
        # 排序并限制每个频道的线路数量
        for name in channel_map:
            channel_map[name] = sort_and_limit_lines(channel_map[name])
        
        # 按类别分组
        category_channels = {}
        for channel_name, lines in channel_map.items():
            if channel_name in CHANNEL_TO_CATEGORY:
                category = CHANNEL_TO_CATEGORY[channel_name]
                if category not in category_channels:
                    category_channels[category] = {}
                category_channels[category][channel_name] = lines
        
        logger.info(f"按类别分组后共有 {len(category_channels)} 个类别")
        
        # 写入输出文件
        if write_output_file(category_channels):
            logger.info(f"处理完成！耗时: {time.time() - start_time:.2f} 秒")
            print(f"处理完成！耗时: {time.time() - start_time:.2f} 秒")
        else:
            logger.error("处理失败：无法写入输出文件")
            print("处理失败：无法写入输出文件")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("程序被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"程序运行过程中发生未捕获的异常: {e}", exc_info=True)
        print(f"程序运行过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
