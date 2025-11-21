#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电视直播线路自动收集整理脚本（日常更新版）
功能：自动从GitHub收集整理中国境内可看的电视直播线路，并按指定分类进行整理
作者：AutoScript
日期：2024
"""

import os
import re
import json
import time
import requests
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("tvzy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GitHub数据源列表（至少10个）
GITHUB_SOURCES = [
    # 有效的中国电视频道源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_UHD.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/MeooPlayer/China-M3U-List/main/China_HD.m3u",
    "http://106.53.99.30/2025.txt",
    "http://tv.html-5.me/i/9390107.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://freetv.fun/test_channels_new.txt",
    
    # 其他稳定的IPTV源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u",
    # 优质高清源
    "https://ghcy.eu.org/https://raw.githubusercontent.com/LongLiveTheKing/web-data/master/data/ip.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/HeJiawen01/IPTV/main/IPTV.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/XIU2/CloudflareSpeedTest/master/ip.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/chenjie/ip.txt/master/ip.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/chnadsl/IPTV/main/IPTV.m3u",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/sbilly/awesome-english-ebooks/master/README.md"
]

# 频道分类
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

CHANNEL_MAPPING.update(additional_mappings)

CATEGORY_ORDER = [
    "4K频道", "央视频道", "卫视频道", "北京专属频道", "山东专属频道", 
    "港澳频道", "电影频道", "儿童频道", "iHOT频道", "综合频道", 
    "剧场频道", "体育频道", "音乐频道"
]

OUTPUT_FILE = "tzydayauto.txt"  # 修改后的输出文件名

def download_source(url, timeout=30):
    """下载单个数据源，包含重试逻辑"""
    start_time = time.time()
    retry_count = 0
    max_retries = 3
    
    while retry_count <= max_retries:
        try:
            # 验证URL格式
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.warning(f"URL格式无效: {url}")
                return None
            
            # 增加请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            logger.info(f"尝试下载: {url}, 第 {retry_count + 1}/{max_retries + 1} 次")
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()  # 检查HTTP错误
            
            elapsed_time = time.time() - start_time
            logger.info(f"成功下载: {url}, 耗时: {elapsed_time:.2f}秒")
            return response.text
            
        except requests.exceptions.RequestException as e:
            retry_count += 1
            elapsed_time = time.time() - start_time
            logger.error(f"下载失败: {url}, 错误: {str(e)}, 耗时: {elapsed_time:.2f}秒")
            
            if retry_count <= max_retries:
                wait_time = min(2 ** retry_count, 10)  # 指数退避，最大等待10秒
                logger.info(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"达到最大重试次数，放弃下载: {url}")
                return None
    
    return None

def collect_all_sources(max_workers=5):
    """并发下载所有数据源，添加URL验证和性能优化"""
    start_time = time.time()
    sources_content = []
    success_count = 0
    failure_count = 0
    
    # 验证URL列表
    if not GITHUB_SOURCES or len(GITHUB_SOURCES) < 10:
        logger.error(f"数据源列表不足10个，当前有: {len(GITHUB_SOURCES) if GITHUB_SOURCES else 0}")
        return sources_content
    
    logger.info(f"开始收集所有数据源，总计: {len(GITHUB_SOURCES)}个，并发数: {max_workers}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有下载任务
        future_to_url = {executor.submit(download_source, url): url for url in GITHUB_SOURCES}
        
        # 处理完成的任务
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                content = future.result()
                if content:
                    # 验证内容有效性
                    if len(content.strip()) > 0:
                        sources_content.append((url, content))
                        success_count += 1
                        logger.debug(f"成功获取并验证内容: {url}")
                    else:
                        failure_count += 1
                        logger.warning(f"获取到空内容: {url}")
                else:
                    failure_count += 1
                    logger.warning(f"未能获取内容: {url}")
            except Exception as e:
                failure_count += 1
                logger.error(f"处理数据源时出错: {url}, 错误: {str(e)}")
    
    total_time = time.time() - start_time
    logger.info(f"数据源收集完成，成功: {success_count}, 失败: {failure_count}, 总计耗时: {total_time:.2f}秒")
    
    # 验证结果
    if len(sources_content) < 5:
        logger.warning(f"成功收集的数据源较少，只有: {len(sources_content)}个")
    
    return sources_content

def extract_channels_from_m3u(content):
    """从M3U格式内容中提取频道信息"""
    channels = []
    try:
        lines = content.strip().split('\n')
        i = 0
        while i < len(lines):
            if lines[i].startswith('#EXTINF:'):
                # 提取频道名称
                name_match = re.search(r'tvg-name="([^"]*)"', lines[i])
                if not name_match:
                    name_match = re.search(r',(.*)$', lines[i])
                
                channel_name = name_match.group(1).strip() if name_match else "未知频道"
                
                # 提取频道URL（下一行）
                if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                    url = lines[i + 1].strip()
                    # 验证URL格式
                    parsed_url = urlparse(url)
                    if parsed_url.scheme and parsed_url.netloc:
                        channels.append((channel_name, url))
                    i += 2
                else:
                    i += 1
            else:
                i += 1
        
        logger.info(f"从M3U内容中成功提取 {len(channels)} 个频道")
    except Exception as e:
        logger.error(f"解析M3U内容时出错: {str(e)}")
    
    return channels

def extract_channels_from_text(content):
    """从文本内容中提取频道信息"""
    channels = []
    try:
        lines = content.strip().split('\n')
        # 匹配频道名称和URL的模式
        url_pattern = re.compile(r'https?://[^\s]+')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # 查找URL
            url_match = url_pattern.search(line)
            if url_match:
                url = url_match.group(0)
                # 提取频道名称（URL之前的部分）
                name_part = line[:url_match.start()].strip()
                # 如果URL之前没有名称，则尝试使用URL的一部分作为名称
                if not name_part:
                    name_part = "未知频道"
                
                channels.append((name_part, url))
        
        logger.info(f"从文本内容中成功提取 {len(channels)} 个频道")
    except Exception as e:
        logger.error(f"解析文本内容时出错: {str(e)}")
    
    return channels

def collect_all_channels():
    """收集所有频道，包括错误处理、日志记录和去重"""
    start_time = time.time()
    logger.info("开始收集所有频道...")
    
    # 下载所有数据源
    sources_content = collect_all_sources()
    if not sources_content:
        logger.error("未能获取任何数据源，无法继续收集频道")
        return []
    
    all_channels = []
    m3u_parsed_count = 0
    text_parsed_count = 0
    error_count = 0
    
    # 用于去重的集合
    unique_channels = set()
    
    for url, content in sources_content:
        try:
            # 首先尝试作为M3U解析
            channels = extract_channels_from_m3u(content)
            if len(channels) > 0:
                m3u_parsed_count += len(channels)
            else:
                # 如果M3U解析失败或没有找到频道，尝试作为文本解析
                channels = extract_channels_from_text(content)
                text_parsed_count += len(channels)
            
            # 去重：使用频道名称和URL的组合作为唯一标识
            for name, url in channels:
                channel_key = f"{name}|{url}"
                if channel_key not in unique_channels:
                    unique_channels.add(channel_key)
                    all_channels.append((name, url))
                    
        except Exception as e:
            error_count += 1
            logger.error(f"处理数据源 {url} 时出错: {str(e)}")
    
    # 统计信息
    original_count = m3u_parsed_count + text_parsed_count
    unique_count = len(all_channels)
    duplicate_count = original_count - unique_count
    
    elapsed_time = time.time() - start_time
    
    logger.info(f"频道收集完成:")
    logger.info(f"- 从M3U格式解析: {m3u_parsed_count} 个频道")
    logger.info(f"- 从文本格式解析: {text_parsed_count} 个频道")
    logger.info(f"- 原始频道总数: {original_count} 个")
    logger.info(f"- 去重后频道数: {unique_count} 个")
    logger.info(f"- 重复频道数: {duplicate_count} 个")
    logger.info(f"- 处理错误数: {error_count} 个")
    logger.info(f"- 总耗时: {elapsed_time:.2f} 秒")
    
    return all_channels

def standardize_channel_name(channel_name):
    """标准化频道名称，添加错误处理和日志记录"""
    start_time = time.time()
    logger.debug(f"开始标准化频道名称: {channel_name}")
    
    try:
        # 检查是否为空
        if not channel_name or channel_name.strip() == "":
            logger.warning("接收到空的频道名称")
            return "未知频道"
        
        # 清理频道名称
        cleaned_name = channel_name.strip()
        
        # 检查是否为CCTV数字频道的特殊格式
        cctv_match = re.match(r'CCTV(\d+)', cleaned_name, re.IGNORECASE)
        if cctv_match:
            cctv_number = cctv_match.group(1)
            try:
                # 查找标准名称
                for standard_name, aliases in CHANNEL_MAPPING.items():
                    if any(f"CCTV{cctv_number}" in alias.upper() for alias in aliases):
                        logger.debug(f"将CCTV{cctv_number}类频道 '{cleaned_name}' 标准化为: {standard_name}")
                        return standard_name
            except Exception as e:
                logger.error(f"处理CCTV频道匹配时出错: {str(e)}")
        
        # 尝试精确匹配
        for standard_name, aliases in CHANNEL_MAPPING.items():
            try:
                for alias in aliases:
                    if alias.lower() == cleaned_name.lower():
                        logger.debug(f"精确匹配: '{cleaned_name}' -> '{standard_name}'")
                        return standard_name
            except Exception as e:
                logger.error(f"检查别名匹配时出错: {str(e)}")
                continue
        
        # 尝试包含匹配（不区分大小写）
        cleaned_lower = cleaned_name.lower()
        for standard_name, aliases in CHANNEL_MAPPING.items():
            try:
                for alias in aliases:
                    if alias.lower() in cleaned_lower and len(alias) > 2:  # 避免过短的匹配
                        logger.debug(f"包含匹配: '{cleaned_name}' -> '{standard_name}'")
                        return standard_name
            except Exception as e:
                logger.error(f"检查包含匹配时出错: {str(e)}")
                continue
        
        # 如果没有匹配，返回清理后的原始名称
        logger.warning(f"未能标准化频道名称: '{cleaned_name}'")
        return cleaned_name
        
    except Exception as e:
        logger.error(f"标准化频道名称时出错: {str(e)}")
        # 返回原始名称作为最后的后备
        return channel_name.strip() if channel_name else "未知频道"
    finally:
        elapsed_time = time.time() - start_time
        logger.debug(f"标准化频道名称耗时: {elapsed_time:.4f}秒")

def get_channel_category(channel_name):
    """获取频道的分类"""
    try:
        # 首先尝试从CHANNEL_MAPPING中找到标准名称
        standard_name = standardize_channel_name(channel_name)
        
        # 在分类中查找
        for category, channels in CHANNEL_CATEGORIES.items():
            if standard_name in channels:
                return category
        
        # 如果找不到，返回默认分类
        return "其他频道"
    except Exception as e:
        logger.error(f"获取频道分类时出错: {str(e)}")
        return "其他频道"

def optimize_channel_mappings():
    """优化频道映射，创建反向映射以便快速查找"""
    reverse_mapping = {}
    
    for standard_name, aliases in CHANNEL_MAPPING.items():
        for alias in aliases:
            reverse_mapping[alias.lower()] = standard_name
    
    return reverse_mapping

REVERSE_CHANNEL_MAPPING = optimize_channel_mappings()

def evaluate_url_quality(url):
    """评估URL质量，提高评估准确性和性能"""
    try:
        # 初始化分数
        score = 0
        
        # URL长度评估（适中的长度通常更好）
        url_len = len(url)
        if 50 <= url_len <= 200:
            score += 20
        elif url_len < 50:
            score += 5  # 太短可能不够稳定
        
        # 检查协议
        if url.startswith('https://'):
            score += 15
        elif url.startswith('http://'):
            score += 10
        
        # 检查域名质量
        high_quality_domains = ['m3u8', 'hls', 'cdn', 'live', 'tv', 'stream']
        for domain in high_quality_domains:
            if domain in url:
                score += 5
        
        # 检查URL参数和路径特征
        if '.m3u8' in url:
            score += 20
        elif '.m3u' in url:
            score += 15
        
        if 'hd' in url.lower() or '高清' in url:
            score += 10
        
        if '4k' in url.lower():
            score += 15
        
        # 检查潜在的不良特征
        bad_features = ['test', 'demo', 'example', 'expired', 'invalid']
        for bad in bad_features:
            if bad in url.lower():
                score -= 10
        
        # 检查是否包含过多的重定向参数
        if 'redirect' in url.lower() and ('http' in url[url.find('redirect'):]):
            score -= 5
        
        # 确保分数在0-100范围内
        score = max(0, min(100, score))
        
        # 记录详细的评分信息
        logger.debug(f"URL质量评估: {url}, 得分: {score}")
        
        return score
        
    except Exception as e:
        logger.error(f"评估URL质量时出错: {str(e)}")
        return 0

def is_high_quality(url):
    """判断URL是否为高质量"""
    return evaluate_url_quality(url) >= 50

def filter_and_group_channels(channels):
    """过滤和分组频道，添加性能优化"""
    start_time = time.time()
    logger.info(f"开始过滤和分组频道，输入频道数: {len(channels)}")
    
    # 第一阶段：收集和过滤
    collected_channels = []
    url_set = set()  # 用于URL去重
    batch_size = 1000  # 批处理大小
    
    for i in range(0, len(channels), batch_size):
        batch_start = time.time()
        batch = channels[i:i+batch_size]
        
        for channel_name, url in batch:
            try:
                # 清理URL
                url = url.strip()
                
                # 检查URL是否有效
                parsed_url = urlparse(url)
                if not (parsed_url.scheme and parsed_url.netloc):
                    continue
                
                # URL去重
                if url in url_set:
                    continue
                url_set.add(url)
                
                # 标准化频道名称
                std_name = standardize_channel_name(channel_name)
                
                # 评估URL质量
                quality_score = evaluate_url_quality(url)
                
                collected_channels.append((std_name, url, quality_score))
                
            except Exception as e:
                logger.error(f"处理频道时出错: {channel_name}, {url}, 错误: {str(e)}")
        
        batch_time = time.time() - batch_start
        logger.info(f"处理批次 {i//batch_size + 1}, 批次大小: {len(batch)}, 耗时: {batch_time:.2f}秒")
    
    # 第二阶段：排序和分组
    grouped = {}
    
    # 按质量分数降序排序
    collected_channels.sort(key=lambda x: x[2], reverse=True)
    
    # 按分类分组
    for channel_name, url, _ in collected_channels:
        category = get_channel_category(channel_name)
        if category not in grouped:
            grouped[category] = []
        grouped[category].append((channel_name, url))
    
    # 统计信息
    elapsed_time = time.time() - start_time
    input_count = len(channels)
    output_count = sum(len(channels) for channels in grouped.values())
    coverage_rate = (output_count / input_count * 100) if input_count > 0 else 0
    
    logger.info(f"频道过滤和分组完成:")
    logger.info(f"- 输入频道数: {input_count}")
    logger.info(f"- 输出频道数: {output_count}")
    logger.info(f"- 频道覆盖率: {coverage_rate:.2f}%")
    logger.info(f"- 分组数: {len(grouped)}")
    logger.info(f"- 总耗时: {elapsed_time:.2f}秒")
    
    # 记录每个分组的频道数
    for category, category_channels in grouped.items():
        logger.debug(f"分组 '{category}' 包含 {len(category_channels)} 个频道")
    
    return grouped

def validate_url(url, timeout=5):
    """简单验证URL是否有效"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 使用HEAD请求以减少流量
        response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

def generate_output_file(grouped_channels, output_file=OUTPUT_FILE):
    """生成输出文件，添加性能监控和错误处理"""
    start_time = time.time()
    logger.info(f"开始生成输出文件: {output_file}")
    
    # 创建临时文件以避免部分写入
    temp_file = f"{output_file}.tmp"
    
    try:
        # 获取所有分类（包括不在预定义顺序中的分类）
        all_categories = set(grouped_channels.keys())
        
        # 按预定义顺序排序分类，并添加未在预定义顺序中的分类
        ordered_categories = []
        for category in CATEGORY_ORDER:
            if category in all_categories:
                ordered_categories.append(category)
                all_categories.remove(category)
        # 添加剩余的分类
        ordered_categories.extend(sorted(all_categories))
        
        total_channels = 0
        written_count = 0
        error_count = 0
        
        # 使用缓冲写入优化性能
        with open(temp_file, 'w', encoding='utf-8', buffering=8192) as f:
            # 写入文件头部信息
            header = f"# 电视直播线路自动收集整理\n"
            header += f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += f"# 总分类数: {len(ordered_categories)}\n"
            f.write(header)
            
            # 按批次写入每个分类
            for category in ordered_categories:
                channels = grouped_channels.get(category, [])
                total_channels += len(channels)
                
                try:
                    # 写入分类标题
                    f.write(f"\n# {category}\n")
                    
                    # 批量写入频道
                    for channel_name, url in channels:
                        # 清理URL
                        url = url.strip()
                        if url:
                            f.write(f"{channel_name},{url}\n")
                            written_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"写入分类 {category} 时出错: {str(e)}")
        
        # 验证临时文件
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            # 如果原文件存在，先备份
            if os.path.exists(output_file):
                backup_file = f"{output_file}.bak"
                try:
                    os.replace(output_file, backup_file)
                    logger.info(f"已备份原文件到: {backup_file}")
                except Exception as e:
                    logger.warning(f"备份原文件时出错: {str(e)}")
            
            # 将临时文件重命名为目标文件
            os.replace(temp_file, output_file)
            logger.info(f"成功将临时文件重命名为目标文件")
        else:
            raise Exception("生成的临时文件为空或不存在")
        
        elapsed_time = time.time() - start_time
        logger.info(f"输出文件生成完成:")
        logger.info(f"- 输出文件: {output_file}")
        logger.info(f"- 总分类数: {len(ordered_categories)}")
        logger.info(f"- 计划写入频道数: {total_channels}")
        logger.info(f"- 实际写入频道数: {written_count}")
        logger.info(f"- 写入错误数: {error_count}")
        logger.info(f"- 文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
        logger.info(f"- 总耗时: {elapsed_time:.2f}秒")
        
        return True
        
    except IOError as e:
        logger.error(f"文件IO错误: {str(e)}")
        # 尝试清理临时文件
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False
    except Exception as e:
        logger.error(f"生成输出文件时出错: {str(e)}")
        # 尝试清理临时文件
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False

def reorder_channels_by_category(grouped_channels):
    """按照预定义的分类顺序重新排序频道"""
    reordered = {}
    
    # 按预定义顺序添加分类
    for category in CATEGORY_ORDER:
        if category in grouped_channels:
            reordered[category] = grouped_channels[category]
    
    # 添加剩余的分类
    for category in grouped_channels:
        if category not in reordered:
            reordered[category] = grouped_channels[category]
    
    return reordered

def main():
    """主函数，执行频道收集和整理流程"""
    logger.info("===== 开始执行电视直播线路收集整理任务 =====")
    overall_start_time = time.time()
    
    # 阶段1：收集频道
    collect_start_time = time.time()
    logger.info("阶段1: 开始收集所有频道...")
    channels = collect_all_channels()
    collect_time = time.time() - collect_start_time
    logger.info(f"阶段1完成: 收集到 {len(channels)} 个频道，耗时: {collect_time:.2f}秒")
    
    if not channels:
        logger.error("未能收集到任何频道，任务失败")
        return False
    
    # 阶段2：过滤和分组
    filter_start_time = time.time()
    logger.info("阶段2: 开始过滤和分组频道...")
    grouped_channels = filter_and_group_channels(channels)
    filter_time = time.time() - filter_start_time
    logger.info(f"阶段2完成: 分组完成，耗时: {filter_time:.2f}秒")
    
    # 阶段3：重新排序分类
    reorder_start_time = time.time()
    logger.info("阶段3: 开始按分类顺序重新排序...")
    reordered_channels = reorder_channels_by_category(grouped_channels)
    reorder_time = time.time() - reorder_start_time
    logger.info(f"阶段3完成: 排序完成，耗时: {reorder_time:.2f}秒")
    
    # 阶段4：生成输出文件
    output_start_time = time.time()
    logger.info("阶段4: 开始生成输出文件...")
    success = generate_output_file(reordered_channels)
    output_time = time.time() - output_start_time
    logger.info(f"阶段4完成: {'成功' if success else '失败'}，耗时: {output_time:.2f}秒")
    
    # 计算总体性能指标
    overall_time = time.time() - overall_start_time
    collect_percent = (collect_time / overall_time * 100) if overall_time > 0 else 0
    filter_percent = (filter_time / overall_time * 100) if overall_time > 0 else 0
    reorder_percent = (reorder_time / overall_time * 100) if overall_time > 0 else 0
    output_percent = (output_time / overall_time * 100) if overall_time > 0 else 0
    
    logger.info(f"===== 任务{'成功' if success else '失败'}完成 =====")
    logger.info(f"总耗时: {overall_time:.2f}秒")
    logger.info(f"时间分布:")
    logger.info(f"- 收集阶段: {collect_time:.2f}秒 ({collect_percent:.1f}%)")
    logger.info(f"- 过滤阶段: {filter_time:.2f}秒 ({filter_percent:.1f}%)")
    logger.info(f"- 排序阶段: {reorder_time:.2f}秒 ({reorder_percent:.1f}%)")
    logger.info(f"- 输出阶段: {output_time:.2f}秒 ({output_percent:.1f}%)")
    
    return success

def execute_main_with_error_handling():
    """执行主函数并处理异常"""
    try:
        return main()
    except MemoryError:
        logger.critical("内存不足错误，请减少并发数或优化处理逻辑")
        return False
    except KeyboardInterrupt:
        logger.info("用户中断执行")
        return False
    except Exception as e:
        logger.critical(f"执行过程中发生未预期的错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("===== 电视直播线路自动收集整理脚本（日常更新版）启动 =====")
    logger.info(f"执行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = execute_main_with_error_handling()
    
    if success:
        logger.info("脚本执行成功")
        exit(0)
    else:
        logger.error("脚本执行失败")
        exit(1)
