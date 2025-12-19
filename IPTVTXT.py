#!/usr/bin/env python3
"""
IPTV直播源自动生成工具（仅使用.txt格式源）
功能：从unified_sources.py中的.txt格式直播源获取内容，仅通过URL检测清晰度，生成高清以上的M3U播放列表
"""

import os
import re
import time
import logging
import requests
import concurrent.futures
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iptv_txt_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 请求头设置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 从统一播放源文件导入
from unified_sources import UNIFIED_SOURCES

# 创建全局Session对象以提高请求性能
session = requests.Session()
session.headers.update(HEADERS)
session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=128, max_retries=0))
session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=128, max_retries=0))

# 频道分类（从IPTV.py复制）
CHANNEL_CATEGORIES = {
    "4K频道": ['CCTV4K', 'CCTV8K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K','广东卫视4K', '四川卫视4K', '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K', '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],
    "央视频道": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9', 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育','兵器科技', '风云足球', '风云音乐', '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '卫生健康','电视指南'],
    "卫视频道": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视', '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视', '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视', '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育'],
    "北京专属频道": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻', '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV', '北京卡酷少儿'],
    "山东专属频道": ['山东卫视', '山东齐鲁', '山东综艺', '山东少儿', '山东生活',
                 '山东新闻', '山东国际', '山东体育', '山东文旅', '山东农科'],
    "港澳频道": ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影'],
    "电影频道": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场', '星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影', '超级电影'],
    "儿童频道": ['动漫秀场', '哒啵电竞', '黑莓动画', '卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通'],
    "iHOT频道": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教', 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈', 'iHOT爱科学', 'iHOT爱动漫'],
    "综合频道": ['重温经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活', '求索动物', '睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论', '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云', '金色学堂', '法治天地', '哒啵赛事'],
    "体育频道": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
    "剧场频道": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],
}

# 频道映射（从IPTV.py复制）
CHANNEL_MAPPING = {
    # 4K频道
    "CCTV4K": ["CCTV 4K", "CCTV-4K超高清頻道", "CCTV4K超高清頻道", "CCTV-4K"],
    "CCTV8K": ["CCTV 8K", "CCTV-8K超高清頻道", "CCTV8K超高清頻道", "CCTV-8K"],
    "CCTV16 4K": ["CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
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
    "CETV1": ["CETV-1", "中国教育1", "中国教育台1", "中国教育-1", "中国教育电视台1"],
    "CETV2": ["CETV-2", "中国教育2", "中国教育台2", "中国教育-2", "中国教育电视台2"],
    "CETV3": ["CETV-3", "中国教育3", "中国教育台3", "中国教育-3", "中国教育电视台3"],
    "CETV4": ["CETV-4", "中国教育4", "中国教育台4", "中国教育-4", "中国教育电视台4"],
    "早期教育": ["CETV-早期教育", "中国教育台-早期教育", "早教", "幼儿教育"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],

    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐", "风云音乐HD", "风云音乐 HD"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV央视高网", "CCTV高尔夫网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "央视文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    
    # 卫视频道
    "山东卫视": ["山东卫视 HD", "山东卫视高清", "山东台"],
    "浙江卫视": ["浙江卫视 HD", "浙江卫视高清", "浙江台"],
    "江苏卫视": ["江苏卫视 HD", "江苏卫视高清", "江苏台"],
    "东方卫视": ["东方卫视 HD", "东方卫视高清", "东方台", "上海东方卫视"],
    "深圳卫视": ["深圳卫视 HD", "深圳卫视高清", "深圳台"],
    "北京卫视": ["北京卫视 HD", "北京卫视高清", "北京台"],
    "广东卫视": ["广东卫视 HD", "广东卫视高清", "广东台"],
    "广西卫视": ["广西卫视 HD", "广西卫视高清", "广西台"],
    "东南卫视": ["东南卫视 HD", "东南卫视高清", "东南台", "福建东南卫视"],
    "海南卫视": ["海南卫视 HD", "海南卫视高清", "海南台", "旅游卫视", "旅游卫视 HD"],
    "河北卫视": ["河北卫视 HD", "河北卫视高清", "河北台"],
    "河南卫视": ["河南卫视 HD", "河南卫视高清", "河南台"],
    "湖北卫视": ["湖北卫视 HD", "湖北卫视高清", "湖北台"],
    "江西卫视": ["江西卫视 HD", "江西卫视高清", "江西台"],
    "四川卫视": ["四川卫视 HD", "四川卫视高清", "四川台"],
    "重庆卫视": ["重庆卫视 HD", "重庆卫视高清", "重庆台"],
    "贵州卫视": ["贵州卫视 HD", "贵州卫视高清", "贵州台"],
    "云南卫视": ["云南卫视 HD", "云南卫视高清", "云南台"],
    "天津卫视": ["天津卫视 HD", "天津卫视高清", "天津台"],
    "安徽卫视": ["安徽卫视 HD", "安徽卫视高清", "安徽台"],
    "湖南卫视": ["湖南卫视 HD", "湖南卫视高清", "湖南台"],
    "辽宁卫视": ["辽宁卫视 HD", "辽宁卫视高清", "辽宁台"],
    "黑龙江卫视": ["黑龙江卫视 HD", "黑龙江卫视高清", "黑龙江台"],
    "吉林卫视": ["吉林卫视 HD", "吉林卫视高清", "吉林台"],
    "内蒙古卫视": ["内蒙古卫视 HD", "内蒙古卫视高清", "内蒙古台"],
    "宁夏卫视": ["宁夏卫视 HD", "宁夏卫视高清", "宁夏台"],
    "山西卫视": ["山西卫视 HD", "山西卫视高清", "山西台"],
    "陕西卫视": ["陕西卫视 HD", "陕西卫视高清", "陕西台"],
    "甘肃卫视": ["甘肃卫视 HD", "甘肃卫视高清", "甘肃台"],
    "青海卫视": ["青海卫视 HD", "青海卫视高清", "青海台"],
    "新疆卫视": ["新疆卫视 HD", "新疆卫视高清", "新疆台"],
    "西藏卫视": ["西藏卫视 HD", "西藏卫视高清", "西藏台"],
    "三沙卫视": ["三沙卫视 HD", "三沙卫视高清", "三沙台"],
    "厦门卫视": ["厦门卫视 HD", "厦门卫视高清", "厦门台"],
    "兵团卫视": ["兵团卫视 HD", "兵团卫视高清", "兵团台"],
    "延边卫视": ["延边卫视 HD", "延边卫视高清", "延边台"],
    "安多卫视": ["安多卫视 HD", "安多卫视高清", "安多台"],
    "康巴卫视": ["康巴卫视 HD", "康巴卫视高清", "康巴台"],
    "农林卫视": ["农林卫视 HD", "农林卫视高清", "农林台"],
    "山东教育": ["山东教育 HD", "山东教育高清", "山东教育台", "山东教育卫视"],

    # 北京专属频道映射
    "北京财经": ["BTV财经", "BTV-财经"],
    "北京纪实": ["BTV纪实", "BTV-纪实"],
    "北京生活": ["BTV生活", "BTV-生活"],
    "北京体育休闲": ["BTV体育休闲", "BTV-体育休闲"],
    "北京国际": ["BTV国际", "BTV-国际"],
    "北京文艺": ["BTV文艺", "BTV-文艺"],
    "北京新闻": ["BTV新闻", "BTV-新闻"],
    "北京淘电影": ["BTV淘电影"],
    "北京淘剧场": ["BTV淘剧场"],
    "北京淘4K": ["BTV淘4K"],
    "北京淘娱乐": ["BTV淘娱乐"],
    "北京淘BABY": ["BTV淘BABY"],
    "北京萌宠TV": ["BTV萌宠TV"],
    "北京卡酷少儿": ["卡酷少儿", "卡酷"],

    # 山东专属频道映射
    "山东齐鲁": ["齐鲁频道"],
    "山东综艺": ["综艺频道"],
    "山东少儿": ["少儿频道"],
    "山东生活": ["生活频道"],
    "山东新闻": ["新闻频道"],
    "山东国际": ["国际频道"],
    "山东体育": ["体育频道"],
    "山东文旅": ["文旅频道"],
    "山东农科": ["农科频道"],

    # 港澳频道映射
    "凤凰中文": ["凤凰卫视中文台"],
    "凤凰资讯": ["凤凰卫视资讯台"],
    "凤凰香港": ["凤凰卫视香港台"],
    "凤凰电影": ["凤凰卫视电影台"],

    # 电影频道映射
    "CHC动作电影": ["动作电影"],
    "CHC家庭影院": ["家庭影院"],
    "CHC影迷电影": ["影迷电影"],
    "淘电影": ["电影"],
    "淘精彩": ["精彩"],
    "淘剧场": ["剧场"],
    "星空卫视": ["星空"],
    "黑莓电影": ["电影"],
    "东北热剧": ["热剧"],
    "中国功夫": ["功夫"],
    "动作电影": ["电影动作"],
    "超级电影": ["电影超级"],

    # 儿童频道映射
    "动漫秀场": ["动漫"],
    "哒啵电竞": ["电竞"],
    "黑莓动画": ["动画"],
    "卡酷少儿": ["卡酷"],
    "金鹰卡通": ["金鹰"],
    "优漫卡通": ["优漫"],
    "哈哈炫动": ["哈哈"],
    "嘉佳卡通": ["嘉佳"],

    # iHOT频道映射
    "iHOT爱喜剧": ["爱喜剧"],
    "iHOT爱科幻": ["爱科幻"],
    "iHOT爱院线": ["爱院线"],
    "iHOT爱悬疑": ["爱悬疑"],
    "iHOT爱历史": ["爱历史"],
    "iHOT爱谍战": ["爱谍战"],
    "iHOT爱旅行": ["爱旅行"],
    "iHOT爱幼教": ["爱幼教"],
    "iHOT爱玩具": ["爱玩具"],
    "iHOT爱体育": ["爱体育"],
    "iHOT爱赛车": ["爱赛车"],
    "iHOT爱浪漫": ["爱浪漫"],
    "iHOT爱奇谈": ["爱奇谈"],
    "iHOT爱科学": ["爱科学"],
    "iHOT爱动漫": ["爱动漫"],

    # 综合频道映射
    "重温经典": ["经典"],
    "CHANNEL[V]": ["Channel V"],
    "求索纪录": ["纪录"],
    "求索科学": ["科学"],
    "求索生活": ["生活"],
    "求索动物": ["动物"],
    "睛彩青少": ["青少"],
    "睛彩竞技": ["竞技"],
    "睛彩篮球": ["篮球"],
    "睛彩广场舞": ["广场舞"],
    "金鹰纪实": ["纪实"],
    "快乐垂钓": ["垂钓"],
    "茶频道": ["茶"],
    "军事评论": ["军事"],
    "军旅剧场": ["军旅"],
    "乐游": ["旅游"],
    "生活时尚": ["时尚"],
    "都市剧场": ["都市"],
    "欢笑剧场": ["欢笑"],
    "游戏风云": ["游戏"],
    "金色学堂": ["学堂"],
    "法治天地": ["法治"],
    "哒啵赛事": ["赛事"],

    # 体育频道映射
    "天元围棋": ["围棋"],
    "魅力足球": ["足球"],
    "五星体育": ["五星"],
    "劲爆体育": ["劲爆"],
    "超级体育": ["超级"],

    # 剧场频道映射
    "古装剧场": ["古装"],
    "家庭剧场": ["家庭"],
    "惊悚悬疑": ["悬疑"],
    "明星大片": ["大片"],
    "欢乐剧场": ["欢乐"],
    "海外剧场": ["海外"],
    "潮妈辣婆": ["潮妈"],
    "爱情喜剧": ["爱情"],
    "超级电视剧": ["电视剧"],
    "超级综艺": ["综艺"],
    "金牌综艺": ["金牌"],
    "武搏世界": ["武搏"],
    "农业致富": ["农业"],
    "炫舞未来": ["炫舞"],
    "精品体育": ["精品"],
    "精品大剧": ["大剧"],
    "精品纪录": ["纪录"],
    "精品萌宠": ["萌宠"],
    "怡伴健康": ["健康"]
}

# 分辨率过滤配置
open_filter_resolution = True  # 开启分辨率过滤
min_resolution = (1920, 1080)  # 最低分辨率要求

# 命令行参数处理
import argparse

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='IPTV高清直播源提取工具（仅使用.txt格式源）')
    
    # 输出文件路径参数
    parser.add_argument('--m3u-output', default='jieguo_txt.m3u', help='M3U文件输出路径')
    parser.add_argument('--txt-output', default='jieguo_txt.txt', help='TXT文件输出路径')
    
    # 日志级别参数
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='日志级别')
    
    # 分辨率过滤参数
    parser.add_argument('--no-resolution-filter', action='store_true', help='禁用分辨率过滤')
    parser.add_argument('--min-resolution', default='1920x1080', help='最低分辨率要求（格式：1920x1080）')
    
    # 其他参数
    parser.add_argument('--timeout', type=int, default=10, help='请求超时时间（秒）')
    
    return parser.parse_args()

# URL格式验证正则表达式
URL_REGEX = re.compile(r'https?://', re.IGNORECASE)

# 高清检测的正则表达式模式（只针对URL）
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

# URL测试函数
def check_url(url, timeout=1, retries=0):
    """测试URL是否可用
    
    参数:
        url: 要测试的URL
        timeout: 超时时间（秒）
        retries: 重试次数（当前已禁用）
    
    返回:
        bool: URL是否可用
    """
    if not URL_REGEX.match(url):
        return False
    
    try:
        # 使用head请求快速测试URL是否存在
        response = session.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False

# 超清（4K及以上）检测的正则表达式模式
ULTRA_HD_PATTERNS = [
    r'[48]k',
    r'2160[pdi]',
    r'3840x2160',
    r'uhd',
    r'超高清',
    r'4k'
]

ULTRA_HD_REGEX = re.compile('|'.join(ULTRA_HD_PATTERNS), re.IGNORECASE)

# 预编译常用的分辨率检测正则表达式
VERTICAL_RES_PATTERN = re.compile(r'(\d{3,4})[pdi]', re.IGNORECASE)
WH_RES_PATTERN = re.compile(r'(\d+)x(\d+)', re.IGNORECASE)

# 分辨率检测的正则表达式模式（只针对URL）
RESOLUTION_PATTERNS = [
    r'(\d{3,4})[pdi]',  # 如1080p, 2160i
    r'(\d+)x(\d+)',     # 如1920x1080, 3840x2160
    r'(\d+)_(\d+)',     # 如1920_1080
    r'res=([1-9]\d+)',       # 如res=1080
    r'resolution=([1-9]\d+)x?([1-9]\d+)',  # 如resolution=1920x1080
    r'width=([1-9]\d+).*?height=([1-9]\d+)',  # 如width=1920 height=1080
]

# 高清检测函数（仅针对URL分辨率参数）
def is_high_quality_channel_line(url):
    """判断频道线路是否为高清以上质量（仅通过URL分辨率参数检测）"""
    if not open_filter_resolution:
        return True
    
    logger.debug(f"检查URL分辨率: {url}")
    
    # 检查垂直分辨率（如1080p, 720i）
    vertical_res_pattern = re.compile(r'(\d{3,4})[pdi]', re.IGNORECASE)
    vertical_match = vertical_res_pattern.search(url)
    if vertical_match:
        try:
            res_value = int(vertical_match.group(1))
            logger.debug(f"找到垂直分辨率: {res_value}p")
            if res_value >= min_resolution[1]:
                logger.debug(f"垂直分辨率匹配: {res_value} >= {min_resolution[1]}")
                return True
        except ValueError:
            logger.debug("垂直分辨率解析失败")
    
    # 检查宽高分辨率（如1920x1080, 1280x720）
    wh_res_pattern = re.compile(r'(\d+)x(\d+)', re.IGNORECASE)
    wh_match = wh_res_pattern.search(url)
    if wh_match:
        try:
            width = int(wh_match.group(1))
            height = int(wh_match.group(2))
            logger.debug(f"找到宽高分辨率: {width}x{height}")
            if width >= min_resolution[0] or height >= min_resolution[1]:
                logger.debug(f"宽高分辨率匹配: {width}x{height} >= {min_resolution[0]}x{min_resolution[1]}")
                return True
        except ValueError:
            logger.debug("宽高分辨率解析失败")
    
    # 检查下划线分隔的分辨率（如1920_1080）
    underscore_res_pattern = re.compile(r'(\d+)_(\d+)', re.IGNORECASE)
    underscore_match = underscore_res_pattern.search(url)
    if underscore_match:
        try:
            width = int(underscore_match.group(1))
            height = int(underscore_match.group(2))
            logger.debug(f"找到下划线分隔分辨率: {width}x{height}")
            if width >= min_resolution[0] or height >= min_resolution[1]:
                logger.debug(f"下划线分隔分辨率匹配: {width}x{height} >= {min_resolution[0]}x{min_resolution[1]}")
                return True
        except ValueError:
            logger.debug("下划线分隔分辨率解析失败")
    
    # 检查res参数（如res=1080）
    res_param_pattern = re.compile(r'res=(\d+)', re.IGNORECASE)
    res_param_match = res_param_pattern.search(url)
    if res_param_match:
        try:
            res_value = int(res_param_match.group(1))
            logger.debug(f"找到res参数: {res_value}")
            if res_value >= min_resolution[1]:
                logger.debug(f"res参数匹配: {res_value} >= {min_resolution[1]}")
                return True
        except ValueError:
            logger.debug("res参数解析失败")
    
    # 检查resolution参数（如resolution=1920x1080）
    resolution_param_pattern = re.compile(r'resolution=(\d+)x?(\d*)', re.IGNORECASE)
    resolution_param_match = resolution_param_pattern.search(url)
    if resolution_param_match:
        try:
            if resolution_param_match.group(2):
                # 有宽高参数
                width = int(resolution_param_match.group(1))
                height = int(resolution_param_match.group(2))
                logger.debug(f"找到resolution参数: {width}x{height}")
                if width >= min_resolution[0] or height >= min_resolution[1]:
                    logger.debug(f"resolution参数匹配: {width}x{height} >= {min_resolution[0]}x{min_resolution[1]}")
                    return True
            else:
                # 只有一个参数（可能是垂直分辨率）
                res_value = int(resolution_param_match.group(1))
                logger.debug(f"找到resolution参数: {res_value}")
                if res_value >= min_resolution[1]:
                    logger.debug(f"resolution参数匹配: {res_value} >= {min_resolution[1]}")
                    return True
        except ValueError:
            logger.debug("resolution参数解析失败")
    
    logger.debug(f"URL不符合高清分辨率要求: {url}")
    return False

# 超清频道检测函数
def is_ultra_high_quality(url):
    """判断频道是否为超清（4K及以上）质量
    
    参数:
        url: 要检测的URL
    
    返回:
        bool: 是否为超清频道
    """
    # 检查是否包含超清标识
    if ULTRA_HD_REGEX.search(url):
        return True
    
    # 检查垂直分辨率是否为2160及以上
    vertical_match = VERTICAL_RES_PATTERN.search(url)
    if vertical_match:
        try:
            res_value = int(vertical_match.group(1))
            if res_value >= 2160:
                return True
        except ValueError:
            pass
    
    # 检查宽高分辨率是否为3840x2160及以上
    wh_match = WH_RES_PATTERN.search(url)
    if wh_match:
        try:
            width, height = int(wh_match.group(1)), int(wh_match.group(2))
            if width >= 3840 or height >= 2160:
                return True
        except ValueError:
            pass
    
    return False

# 频道名称标准化函数
def normalize_channel_name(channel_name):
    """标准化频道名称，用于分类"""
    if not channel_name:
        return ""
    
    # 移除所有空格和特殊字符，只保留字母、数字、中文和连字符
    channel_name = re.sub(r'[^\w\u4e00-\u9fa5\-]', '', channel_name)
    channel_name = channel_name.strip()
    
    if not channel_name:
        return ""
    
    # 使用频道映射进行标准化
    for standard_name, aliases in CHANNEL_MAPPING.items():
        # 尝试匹配标准名称
        if standard_name.lower() == channel_name.lower():
            return standard_name
        # 尝试匹配所有别名
        for alias in aliases:
            if alias.lower() == channel_name.lower():
                return standard_name
    
    # 如果没有匹配到映射，尝试直接匹配CHANNEL_CATEGORIES中的频道名称
    for category, channels in CHANNEL_CATEGORIES.items():
        for channel in channels:
            if channel.lower() == channel_name.lower():
                return channel
    
    return channel_name

# 频道分类函数
def get_channel_category(channel_name):
    """根据频道名称获取分类"""
    if not channel_name:
        return None
    
    # 检查频道是否在分类中
    for category, channels in CHANNEL_CATEGORIES.items():
        for channel in channels:
            if channel_name == channel:
                return category
    
    # 如果没有找到分类，返回None
    return None

# 从.txt内容中提取频道的函数
def extract_channels_from_txt(content):
    """从.txt文件内容中提取频道信息"""
    channels = defaultdict(list)
    lines = content.splitlines()
    logger.info(f"正在处理内容，共 {len(lines)} 行")
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 检测URL
        if 'http://' in line or 'https://' in line:
            # 分离频道名称和URL
            if 'http://' in line:
                parts = line.split('http://')
                channel_name = parts[0].strip()
                url = 'http://' + parts[1].strip()
            else:
                parts = line.split('https://')
                channel_name = parts[0].strip()
                url = 'https://' + parts[1].strip()
            
            # 处理空频道名称
            if not channel_name:
                channel_name = url.split('/')[2]  # 使用域名作为频道名称
            
            # 检测是否为高清频道
            if is_high_quality_channel_line(url):
                normalized_name = normalize_channel_name(channel_name)
                category = get_channel_category(normalized_name)
                # 只添加有分类的频道（不在CHANNEL_CATEGORIES中的频道会被舍弃）
                if category:
                    channels[category].append((normalized_name, url))
                    logger.debug(f"添加高清频道: {normalized_name} -> {url} (分类: {category})")
                else:
                    logger.debug(f"舍弃未分类频道: {normalized_name} -> {url}")
    
    logger.info(f"提取完成，共获取 {sum(len(channels_list) for channels_list in channels.values())} 个高清频道")
    return channels

# 过滤.txt直播源的函数
def get_txt_sources():
    """从统一来源中过滤出.txt格式的直播源"""
    txt_sources = [source for source in UNIFIED_SOURCES if source.endswith('.txt')]
    logger.info(f"已过滤出 {len(txt_sources)} 个.txt格式的直播源")
    return txt_sources



# 生成M3U文件的函数
def generate_m3u_file(channels, output_file='jieguo_txt.m3u'):
    """根据提取的频道生成M3U文件（与IPTV.py格式一致）"""
    logger.info(f"正在生成M3U文件，输出到 {output_file}")
    
    import datetime
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write("#EXTM3U x-tvg-url=\"https://kakaxi-1.github.io/IPTV/epg.xml\"\n")
            
            # 写入当前时间作为标记（北京时间UTC+8）
            f.write(f"# 生成时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
            
            # 按CHANNEL_CATEGORIES中定义的顺序写入分类
            written_count = 0
            for category in CHANNEL_CATEGORIES:
                if category in channels:
                    for channel_name, url in channels[category]:
                        # 写入频道信息
                        f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                        f.write(f"{url}\n")
                        written_count += 1
            
            # 不写入其他频道，只包含CHANNEL_CATEGORIES中定义的频道
        
        logger.info(f"M3U文件生成完成，共 {written_count} 个频道")
        return True
    except Exception as e:
        logger.error(f"生成M3U文件失败: {e}")
        return False

# 生成TXT文件的函数
def generate_txt_file(channels, output_file='jieguo_txt.txt'):
    """根据提取的频道生成TXT文件（与IPTV.py格式一致）"""
    logger.info(f"正在生成TXT文件，输出到 {output_file}")
    
    import datetime
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
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
            
            # 不写入其他频道，只包含CHANNEL_CATEGORIES中定义的频道
            
            # 在文件末尾添加说明行
            f.write("\n说明,#genre#\n")
            
            # 写入文件头注释到文件末尾
            f.write(f"# IPTV直播源列表\n")
            f.write(f"# 生成时间: {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 格式: 频道名称,播放URL\n")
            f.write("# 按分组排列\n")
            f.write("\n")
        
        logger.info(f"TXT文件生成完成，共 {sum(len(channels_list) for channels_list in channels.values())} 个频道")
        return True
    except Exception as e:
        logger.error(f"生成TXT文件失败: {e}")
        return False

# 更新全局配置的函数
def update_global_config(args):
    """根据命令行参数更新全局配置"""
    global open_filter_resolution, min_resolution
    
    # 更新日志级别
    numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)
    
    # 更新分辨率过滤配置
    if args.no_resolution_filter:
        open_filter_resolution = False
    else:
        open_filter_resolution = True
        # 解析最低分辨率
        try:
            width, height = map(int, args.min_resolution.split('x'))
            min_resolution = (width, height)
            logger.info(f"设置最低分辨率: {min_resolution[0]}x{min_resolution[1]}")
        except ValueError:
            logger.warning(f"无效的分辨率格式: {args.min_resolution}，使用默认值: {min_resolution[0]}x{min_resolution[1]}")
    
    # 更新请求超时时间
    global session
    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=128, max_retries=0))
    session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=128, max_retries=0))

# 从.txt源获取内容的函数
def fetch_txt_content(source_url, timeout=10):
    """从指定的URL获取.txt内容"""
    logger.info(f"正在获取 {source_url} 的内容...")
    try:
        response = session.get(source_url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"获取 {source_url} 失败: {e}")
        return None

# 主函数
def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 更新全局配置
    update_global_config(args)
    
    logger.info("=== IPTVTXT 高清直播源提取工具开始运行 ===")
    
    try:
        # 获取.txt格式的直播源
        txt_sources = get_txt_sources()
        if not txt_sources:
            logger.error("没有找到.txt格式的直播源")
            return 1
        
        # 获取所有.txt源的内容并提取频道
        all_channels = defaultdict(list)
        for source in txt_sources:
            content = fetch_txt_content(source, timeout=args.timeout)
            if content:
                channels = extract_channels_from_txt(content)
                # 合并频道
                for category, category_channels in channels.items():
                    all_channels[category].extend(category_channels)
        
        # 去重处理
        unique_channels = defaultdict(list)
        seen = set()
        for category, channels in all_channels.items():
            for channel_name, url in channels:
                if url not in seen:
                    seen.add(url)
                    unique_channels[category].append((channel_name, url))

        if not unique_channels:
            logger.error("没有提取到任何高清频道")
            return 2

        logger.info(f"去重后剩余 {sum(len(channels_list) for channels_list in unique_channels.values())} 个频道")
    
    # URL测试处理
        logger.info("正在进行URL测试...")
        
        # 准备需要测试的频道
        test_items = []
        for category, channels in unique_channels.items():
            for channel_name, url in channels:
                # 判断是否为超清频道，设置不同的超时时间
                if is_ultra_high_quality(url):
                    timeout = 5  # 超清频道超时5秒
                else:
                    timeout = 2  # 普通高清频道超时2秒
                test_items.append((category, channel_name, url, timeout))
        
        # 并发测试URL
        tested_channels = defaultdict(list)
        total_tested = len(test_items)
        valid_count = 0
        
        # 使用ThreadPoolExecutor并发处理，最大工作线程数为50
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # 提交所有测试任务
            future_to_test = {executor.submit(check_url, url, timeout, 0): (category, channel_name) 
                             for category, channel_name, url, timeout in test_items}
            
            # 收集测试结果
            for future in concurrent.futures.as_completed(future_to_test):
                category, channel_name = future_to_test[future]
                try:
                    is_valid = future.result()
                    if is_valid:
                        url = [item[2] for item in test_items if item[1] == channel_name and item[0] == category][0]
                        tested_channels[category].append((channel_name, url))
                        valid_count += 1
                        logger.debug(f"频道可用: {channel_name} -> {url}")
                    else:
                        logger.debug(f"频道不可用: {channel_name}")
                except Exception as e:
                    logger.error(f"测试频道 {channel_name} 时出错: {e}")

        if not tested_channels:
            logger.error("没有测试通过的频道")
            return 3

        logger.info(f"URL测试完成，共测试 {total_tested} 个频道，{valid_count} 个可用")

        # 生成M3U文件
        m3u_result = generate_m3u_file(tested_channels, output_file=args.m3u_output)
        if not m3u_result:
            logger.error("生成M3U文件失败")
            return 3
    
    # 生成TXT文件
        txt_result = generate_txt_file(tested_channels, output_file=args.txt_output)
        if not txt_result:
            logger.error("生成TXT文件失败")
            return 4
        
        logger.info("=== IPTVTXT 高清直播源提取工具运行完成 ===")
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断了程序")
        return 130
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        return 5

# 运行主函数
if __name__ == "__main__":
    import sys
    sys.exit(main())
