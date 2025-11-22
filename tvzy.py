#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电视直播线路自动收集整理脚本
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
import schedule
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
    "https://ghcy.eu.org/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/kimwang1978/collect-txt/refs/heads/main/bbxx.txt",
    "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/yoursmile66/TVBox/main/XC.json
    "https://ghfast.top/https://raw.githubusercontent.com/leevi0709/one/main/jsm.json",
    "http://106.53.99.30/2025.txt",
    "http://tv.html-5.me/i/9390107.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
    "https://freetv.fun/test_channels_new.txt",
    "https://ghcy.eu.org/https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u"
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

# 频道映射（别名 -> 规范名）
CHANNEL_MAPPING = {
    # 4K频道
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
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-央视高网", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "央视文化精品", "央视文化精品"],
    "北京纪实科教": ["CCTV-北京纪实科教", "CCTV北京纪实科教"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    
    # 卫视频道
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
    "早期教育": ["早期教育", "早教", "幼儿教育"]
}

# 补充其他频道的映射
additional_mappings = {
    # 北京专属频道
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
    
    # 山东专属频道
    "山东齐鲁": ["山东齐鲁", "齐鲁频道"],
    "山东综艺": ["山东综艺", "综艺频道"],
    "山东少儿": ["山东少儿", "少儿频道"],
    "山东生活": ["山东生活", "生活频道"],
    "山东新闻": ["山东新闻", "新闻频道"],
    "山东国际": ["山东国际", "国际频道"],
    "山东体育": ["山东体育", "体育频道"],
    "山东文旅": ["山东文旅", "文旅频道"],
    "山东农科": ["山东农科", "农科频道"],
    
    # 港澳频道
    "凤凰中文": ["凤凰中文", "凤凰卫视中文台"],
    "凤凰资讯": ["凤凰资讯", "凤凰卫视资讯台"],
    "凤凰香港": ["凤凰香港", "凤凰卫视香港台"],
    "凤凰电影": ["凤凰电影", "凤凰卫视电影台"],
    
    # 电影频道
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
    
    # 儿童频道
    "动漫秀场": ["动漫秀场", "动漫"],
    "哒啵电竞": ["哒啵电竞", "电竞"],
    "黑莓动画": ["黑莓动画", "动画"],
    "卡酷少儿": ["卡酷少儿", "卡酷"],
    "金鹰卡通": ["金鹰卡通", "金鹰"],
    "优漫卡通": ["优漫卡通", "优漫"],
    "哈哈炫动": ["哈哈炫动", "哈哈"],
    "嘉佳卡通": ["嘉佳卡通", "嘉佳"],
    
    # iHOT频道
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
    
    # 综合频道
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
    
    # 剧场频道
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
    
    # 体育频道
    "天元围棋": ["天元围棋", "围棋"],
    "魅力足球": ["魅力足球", "足球"],
    "五星体育": ["五星体育", "五星"],
    "劲爆体育": ["劲爆体育", "劲爆"],
    "超级体育": ["超级体育", "超级"],
    
    # 音乐频道
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

# 合并映射字典
CHANNEL_MAPPING.update(additional_mappings)

# 创建反向映射（别名 -> 规范名）
# REVERSE_CHANNEL_MAPPING 会在 optimize_channel_mappings 函数中初始化和优化

# 分类排序顺序
CATEGORY_ORDER = [
    "4K频道", "央视频道", "卫视频道", "北京专属频道", "山东专属频道", 
    "港澳频道", "电影频道", "儿童频道", "iHOT频道", "综合频道", 
    "剧场频道", "体育频道", "音乐频道"
]

# 输出文件配置
OUTPUT_FILE = "tzydayauto.txt"  # 修改为正确的输出文件名

def download_source(url, timeout=30):
    """
    下载单个数据源（带重试机制）
    :param url: GitHub数据源URL
    :param timeout: 超时时间
    :return: 下载的内容
    """
    retry_count = 3
    retry_delay = 5  # 秒
    
    for attempt in range(retry_count):
        try:
            logger.info(f"正在下载数据源 ({attempt+1}/{retry_count}): {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            # 检查内容是否为空
            if not response.text.strip():
                logger.warning(f"数据源返回空内容: {url}, 尝试 {attempt+1}/{retry_count}")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                return ""
            
            logger.info(f"成功下载数据源: {url} (尝试 {attempt+1}/{retry_count})")
            return response.text
            
        except requests.exceptions.Timeout:
            logger.warning(f"下载超时: {url}, 尝试 {attempt+1}/{retry_count}")
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
        except requests.exceptions.ConnectionError:
            logger.warning(f"连接错误: {url}, 尝试 {attempt+1}/{retry_count}")
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误 {e.response.status_code}: {url}")
            # 对于404等致命错误，不再重试
            if attempt < retry_count - 1 and e.response.status_code != 404:
                time.sleep(retry_delay)
                continue
        except Exception as e:
            logger.error(f"下载数据源时发生未知错误: {url}, 错误: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
    
    logger.error(f"在 {retry_count} 次尝试后，下载数据源失败: {url}")
    return ""

def collect_all_sources(max_workers=5):
    """
    并行下载所有数据源（带详细日志和错误处理）
    :param max_workers: 最大线程数
    :return: 所有数据源内容列表
    """
    start_time = time.time()
    logger.info(f"开始收集所有数据源，总计{len(GITHUB_SOURCES)}个数据源")
    
    # 验证数据源URL
    valid_sources = [url for url in GITHUB_SOURCES if url.strip() and url.startswith(('http://', 'https://'))]
    invalid_count = len(GITHUB_SOURCES) - len(valid_sources)
    
    if invalid_count > 0:
        logger.warning(f"发现{invalid_count}个无效的数据源URL，已过滤")
    
    all_contents = []
    success_count = 0
    failed_count = 0
    empty_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(download_source, url): url for url in valid_sources}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                content = future.result()
                if content:
                    all_contents.append(content)
                    success_count += 1
                    content_size_kb = len(content) / 1024
                    logger.debug(f"成功处理数据源: {url}, 大小: {content_size_kb:.2f}KB")
                else:
                    empty_count += 1
                    logger.warning(f"数据源返回空内容: {url}")
            except Exception as e:
                failed_count += 1
                logger.error(f"处理数据源时发生异常: {url}, 错误: {str(e)}", exc_info=True)
    
    elapsed_time = time.time() - start_time
    logger.info(f"数据源收集完成 - 成功: {success_count}, 失败: {failed_count}, 空内容: {empty_count}, 耗时: {elapsed_time:.2f}秒")
    
    # 检查数据源数量是否满足要求
    if len(all_contents) < 10:
        logger.warning(f"警告: 收集到的有效数据源数量为{len(all_contents)}，低于要求的10个数据源")
    
    return all_contents

def extract_channels_from_m3u(content):
    """
    从M3U内容中提取频道信息
    :param content: M3U格式的内容
    :return: 频道列表
    """
    channels = []
    lines = content.split('\n')
    title = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            match = re.search(r'tvg-name="([^"]+)"', line)
            if match:
                title = match.group(1)
            else:
                # 尝试其他格式提取频道名称
                match = re.search(r',(.+)', line)
                if match:
                    title = match.group(1)
        elif line.startswith('http') and title:
            # 提取URL
            url = line
            channels.append({
                'title': title,
                'url': url
            })
            title = None
    
    return channels

def extract_channels_from_text(content):
    """
    从文本内容中提取频道信息（处理非标准M3U格式）
    :param content: 文本内容
    :return: 频道列表
    """
    channels = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # 尝试不同的分隔符格式
        if '=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2 and parts[1].startswith('http'):
                channels.append({
                    'title': parts[0],
                    'url': parts[1]
                })
        elif ',' in line:
            parts = line.split(',', 1)
            if len(parts) == 2 and parts[1].startswith('http'):
                channels.append({
                    'title': parts[0],
                    'url': parts[1]
                })
        elif line.startswith('http'):
            # 只有URL，没有标题
            url = line
            # 尝试从URL中提取可能的标题
            parsed_url = urlparse(url)
            title = parsed_url.netloc.split('.')[-2] if len(parsed_url.netloc.split('.')) >= 2 else 'Unknown'
            channels.append({
                'title': title,
                'url': url
            })
    
    return channels

def collect_all_channels():
    """
    收集所有频道（带详细错误处理和日志）
    :return: 频道列表
    """
    start_time = time.time()
    logger.info("开始收集所有频道信息...")
    
    try:
        sources_content = collect_all_sources()
        all_channels = []
        m3u_count = 0
        text_count = 0
        error_count = 0
        
        for idx, content in enumerate(sources_content):
            try:
                # 尝试解析为M3U格式
                m3u_channels = extract_channels_from_m3u(content)
                if m3u_channels:
                    all_channels.extend(m3u_channels)
                    m3u_count += len(m3u_channels)
                    logger.debug(f"数据源 {idx+1} 解析为M3U格式，提取到{len(m3u_channels)}个频道")
                else:
                    # 如果不是M3U格式，尝试作为文本解析
                    text_channels = extract_channels_from_text(content)
                    all_channels.extend(text_channels)
                    text_count += len(text_channels)
                    logger.debug(f"数据源 {idx+1} 解析为文本格式，提取到{len(text_channels)}个频道")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"解析数据源 {idx+1} 时发生异常: {str(e)}", exc_info=True)
        
        # 去重处理
        unique_channels = {channel['name'] + '_' + channel['url']: channel for channel in all_channels}.values()
        unique_channels = list(unique_channels)
        
        elapsed_time = time.time() - start_time
        logger.info(f"频道收集完成 - 原始频道: {len(all_channels)}, 去重后频道: {len(unique_channels)}")
        logger.info(f"M3U解析频道: {m3u_count}, 文本解析频道: {text_count}, 解析错误: {error_count}, 耗时: {elapsed_time:.2f}秒")
        
        return unique_channels
    except Exception as e:
        logger.error(f"收集频道信息时发生严重错误: {str(e)}", exc_info=True)
        return []

def standardize_channel_name(channel_name):
    """
    标准化频道名称（带详细错误处理和日志）
    :param channel_name: 原始频道名称
    :return: 标准化后的频道名称，如果无法识别则返回None或原始名称
    """
    try:
        if not channel_name:
            logger.warning("接收到空的频道名称")
            return None
        
        original_name = channel_name
        logger.debug(f"开始标准化频道名称: '{original_name}'")
        
        # 清理频道名称
        cleaned_name = channel_name.strip()
        # 移除常见的后缀
        suffixes = [' HD', '-HD', '高清', '直播']
        for suffix in suffixes:
            if cleaned_name.endswith(suffix):
                cleaned_name = cleaned_name[:-len(suffix)].strip()
                logger.debug(f"移除后缀 '{suffix}': '{cleaned_name}'")
        
        # 转换为小写进行匹配
        lower_name = cleaned_name.lower()
        
        # 尝试直接匹配反向映射（精确匹配优先级最高）
        if lower_name in REVERSE_CHANNEL_MAPPING:
            result = REVERSE_CHANNEL_MAPPING[lower_name]
            logger.debug(f"精确匹配: '{cleaned_name}' -> '{result}'")
            return result
        
        # 尝试部分匹配，但使用更精确的算法
        best_match = None
        best_match_score = 0
        
        for alias, standard_name in REVERSE_CHANNEL_MAPPING.items():
            try:
                # 完全包含关系
                if alias in lower_name or lower_name in alias:
                    # 计算匹配得分：重叠字符数 / 较长字符串长度
                    overlap_length = len(set(alias).intersection(set(lower_name)))
                    longer_length = max(len(alias), len(lower_name))
                    score = overlap_length / longer_length
                    
                    # 对于CCTV频道的特殊处理
                    if ('cctv' in alias and 'cctv' in lower_name) or \
                       (standard_name.startswith('CCTV') and 'cctv' in lower_name):
                        score += 0.3  # 提高CCTV频道的匹配优先级
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = standard_name
            except Exception as inner_e:
                logger.error(f"处理别名 '{alias}' 时出错: {str(inner_e)}", exc_info=True)
                continue
        
        # 如果找到匹配且分数足够高
        if best_match and best_match_score > 0.6:
            logger.debug(f"模糊匹配: '{cleaned_name}' -> '{best_match}' (得分: {best_match_score:.2f})")
            return best_match
        elif best_match:
            logger.debug(f"匹配分数不足: '{cleaned_name}' -> '{best_match}' (得分: {best_match_score:.2f})")
        
        # 对于没有明确映射的频道，尝试根据关键词匹配分类
        for category, channel_list in CHANNEL_CATEGORIES.items():
            for standard_name in channel_list:
                try:
                    std_lower = standard_name.lower()
                    # 完全匹配或部分匹配
                    if std_lower == lower_name or std_lower in lower_name or lower_name in std_lower:
                        logger.debug(f"分类匹配: '{cleaned_name}' -> '{standard_name}' (分类: {category})")
                        return standard_name
                except Exception as inner_e:
                    logger.error(f"分类匹配时出错: {str(inner_e)}", exc_info=True)
                    continue
        
        # 针对特殊情况的额外处理
        # 处理带有数字的频道
        if re.match(r'^cctv\d+$', lower_name):
            try:
                # 匹配CCTV数字频道
                cctv_num = re.search(r'cctv(\d+)', lower_name).group(1)
                for std_name in CHANNEL_MAPPING.keys():
                    if std_name.lower() == f'cctv{cctv_num}':
                        logger.debug(f"CCTV数字频道匹配: '{cleaned_name}' -> '{std_name}'")
                        return std_name
            except Exception as inner_e:
                logger.error(f"CCTV数字频道处理出错: {str(inner_e)}", exc_info=True)
        
        # 所有匹配都失败，返回原始清理后的名称
        logger.debug(f"无匹配: '{original_name}' -> '{cleaned_name}'")
        return cleaned_name
    
    except Exception as e:
        logger.error(f"标准化频道名称时发生严重错误: '{channel_name}', 错误: {str(e)}", exc_info=True)
        # 出错时返回原始名称，保证程序继续运行
        return channel_name if channel_name else None
    
    # 如果都无法识别，返回None
    return None

def get_channel_category(channel_name):
    """
    获取频道所属分类
    :param channel_name: 频道名称
    :return: 分类名称，如果不属于任何分类则返回None
    """
    if not channel_name:
        return None
    
    # 优先检查完全匹配
    for category, channel_list in CHANNEL_CATEGORIES.items():
        if channel_name in channel_list:
            return category
    
    # 检查部分匹配
    for category, channel_list in CHANNEL_CATEGORIES.items():
        for std_name in channel_list:
            if std_name in channel_name or channel_name in std_name:
                return category
    
    # 特殊处理：根据关键词推断分类
    channel_lower = channel_name.lower()
    if '4k' in channel_lower:
        return "4K频道"
    elif 'cctv' in channel_lower:
        return "央视频道"
    elif '卫视' in channel_lower:
        return "卫视频道"
    elif '北京' in channel_lower or 'btv' in channel_lower:
        return "北京专属频道"
    elif '山东' in channel_lower:
        return "山东专属频道"
    elif '凤凰' in channel_lower or '香港' in channel_lower or '澳门' in channel_lower or 'tvb' in channel_lower:
        return "港澳频道"
    elif '电影' in channel_lower or '剧场' in channel_lower or '影院' in channel_lower:
        return "电影频道"
    elif '少儿' in channel_lower or '卡通' in channel_lower or '动漫' in channel_lower or '动画' in channel_lower:
        return "儿童频道"
    elif 'ihot' in channel_lower:
        return "iHOT频道"
    elif '体育' in channel_lower or '足球' in channel_lower or '篮球' in channel_lower:
        return "体育频道"
    elif '音乐' in channel_lower or 'mtv' in channel_lower:
        return "音乐频道"
    elif '剧场' in channel_lower:
        return "剧场频道"
    
    return None

# 预处理和优化频道映射，提高匹配效率
def optimize_channel_mappings():
    """
    优化频道映射，添加更多可能的别名组合
    """
    global REVERSE_CHANNEL_MAPPING
    
    # 创建扩展的反向映射
    extended_mapping = {}
    
    for standard_name, aliases in CHANNEL_MAPPING.items():
        # 添加原始映射
        for alias in aliases:
            extended_mapping[alias.lower()] = standard_name
        extended_mapping[standard_name.lower()] = standard_name
        
        # 添加可能的变体
        # 移除空格和连字符
        no_space_name = standard_name.replace(' ', '')
        no_dash_name = standard_name.replace('-', '')
        no_space_dash_name = standard_name.replace(' ', '').replace('-', '')
        
        for variant in [no_space_name, no_dash_name, no_space_dash_name]:
            if variant and variant.lower() not in extended_mapping:
                extended_mapping[variant.lower()] = standard_name
        
        # 对于CCTV频道的特殊处理
        if standard_name.startswith('CCTV'):
            # 添加小写变体
            extended_mapping[standard_name.lower()] = standard_name
            # 添加带连字符的变体
            if not standard_name.startswith('CCTV-'):
                cctv_with_dash = standard_name.replace('CCTV', 'CCTV-')
                extended_mapping[cctv_with_dash.lower()] = standard_name
    
    return extended_mapping

# 初始化优化的反向映射
REVERSE_CHANNEL_MAPPING = optimize_channel_mappings()

def evaluate_url_quality(url):
    """
    评估URL质量，返回质量分数（越高越好）
    :param url: 直播URL
    :return: 质量分数
    """
    if not url:
        return 0
    
    url_lower = url.lower()
    score = 0
    
    # 根据分辨率关键词加分
    resolution_scores = {
        '4k': 100,
        '2160': 100,
        'uhd': 90,
        '2k': 80,
        '1440': 80,
        'fhd': 70,
        '1080p': 70,
        '1080i': 65,
        '1080': 60,
        'fullhd': 60
    }
    
    for keyword, points in resolution_scores.items():
        if keyword in url_lower:
            score += points
            # 找到最高分辨率的关键词后可以跳出循环
            if score >= 100:  # 4K已经是最高质量
                break
    
    # 根据码率相关关键词加分
    bitrate_keywords = {
        'highbitrate': 30,
        'high-bitrate': 30,
        'hdbitrate': 25,
        'hd-bitrate': 25,
        'high': 20,
        'bitrate': 15
    }
    
    for keyword, points in bitrate_keywords.items():
        if keyword in url_lower:
            score += points
            break  # 只加一次码率分
    
    # 根据服务器稳定性关键词加分
    stability_keywords = {
        'cdn': 15,
        'hls': 10,
        'm3u8': 10,
        'stable': 20,
        'official': 25
    }
    
    for keyword, points in stability_keywords.items():
        if keyword in url_lower:
            score += points
    
    # 根据URL长度和复杂度评分
    # 太短的URL可能不够稳定
    if len(url) > 30:
        score += 5
    elif len(url) < 20:
        score -= 5
    
    # 过滤低质量关键词
    low_quality_keywords = [
        '360p', '480p', '540p', 'sd', 'low', 'poor',
        '240p', '144p', 'lowbitrate', 'low-bitrate'
    ]
    
    for keyword in low_quality_keywords:
        if keyword in url_lower:
            score -= 50  # 大幅降低分数
            break
    
    return max(0, score)  # 确保分数不为负

def is_high_quality(url):
    """
    判断是否为高清线路（1080p以上）
    :param url: 直播URL
    :return: 是否为高清线路
    """
    # 使用质量评估函数，设置阈值为40分
    return evaluate_url_quality(url) >= 40

def filter_and_group_channels(channels):
    """
    筛选和分组频道（优化版）
    :param channels: 原始频道列表
    :return: 分组后的频道字典
    """
    logger.info(f"开始筛选和分组频道，原始频道数量: {len(channels)}")
    
    # 初始化分组字典
    grouped_channels = {category: {} for category in CATEGORY_ORDER}
    
    # 使用集合提高去重效率
    channel_urls_set = {}
    channel_urls_with_scores = {}
    
    # 第一阶段：收集并筛选频道
    processed_count = 0
    start_time = time.time()
    
    # 批量处理以提高性能
    batch_size = 1000
    for i in range(0, len(channels), batch_size):
        batch = channels[i:i+batch_size]
        batch_start = time.time()
        
        for channel in batch:
            try:
                # 提取必要信息
                title = channel.get('title', '')
                url = channel.get('url', '')
                
                # 基本URL验证
                if not url or not url.startswith(('http://', 'https://')):
                    continue
                
                # 标准化频道名称
                standard_name = standardize_channel_name(title)
                if not standard_name:
                    continue
                
                # 初始化数据结构
                if standard_name not in channel_urls_set:
                    channel_urls_set[standard_name] = set()
                    channel_urls_with_scores[standard_name] = []
                
                # 避免重复URL（使用集合提高效率）
                if url in channel_urls_set[standard_name]:
                    continue
                
                # 评估URL质量
                quality_score = evaluate_url_quality(url)
                
                # 只保留高质量线路（1080p以上）
                if quality_score >= 40:
                    channel_urls_set[standard_name].add(url)
                    channel_urls_with_scores[standard_name].append({
                        'url': url,
                        'score': quality_score
                    })
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    logger.info(f"已处理 {processed_count} 个频道项")
            except Exception as e:
                logger.error(f"处理频道项时出错: {str(e)}")
        
        batch_end = time.time()
        logger.debug(f"批处理完成，处理了 {len(batch)} 个频道，耗时: {batch_end - batch_start:.2f} 秒")
    
    stage1_end = time.time()
    logger.info(f"第一阶段处理完成，共处理 {processed_count} 个有效频道项，耗时: {stage1_end - start_time:.2f} 秒")
    
    # 第二阶段：排序和分组
    channel_count = 0
    total_url_count = 0
    insufficient_channels = 0
    invalid_category_count = 0
    
    # 对频道进行排序处理
    for standard_name, url_items in channel_urls_with_scores.items():
        try:
            # 获取频道分类
            category = get_channel_category(standard_name)
            if not category or category not in grouped_channels:
                invalid_category_count += 1
                continue
            
            # 按质量分数排序（从高到低）
            url_items.sort(key=lambda x: x['score'], reverse=True)
            
            # 提取排序后的URL列表
            sorted_urls = [item['url'] for item in url_items]
            
            # 限制URL数量在10-90之间
            if len(sorted_urls) < 10:
                insufficient_channels += 1
                logger.debug(f"频道 {standard_name} 高清线路不足10条（{len(sorted_urls)}条），已跳过")
                continue
            
            # 最多保留90个URL
            final_urls = sorted_urls[:90]
            
            # 添加到分组字典
            grouped_channels[category][standard_name] = final_urls
            
            # 统计信息
            channel_count += 1
            total_url_count += len(final_urls)
            
            # 减少日志输出频率以提高性能
            if channel_count % 20 == 0:
                logger.info(f"已处理 {channel_count} 个频道，共添加 {total_url_count} 条线路")
        except Exception as e:
            logger.error(f"处理频道 {standard_name} 时出错: {str(e)}")
    
    stage2_end = time.time()
    logger.info(f"第二阶段处理完成，耗时: {stage2_end - stage1_end:.2f} 秒")
    
    # 性能统计和优化建议
    logger.info(f"频道筛选和分组完成：")
    logger.info(f"- 成功处理频道: {channel_count}")
    logger.info(f"- 有效线路总数: {total_url_count}")
    logger.info(f"- 跳过的低线路频道: {insufficient_channels}")
    logger.info(f"- 无效分类频道: {invalid_category_count}")
    logger.info(f"- 总耗时: {stage2_end - start_time:.2f} 秒")
    
    # 计算频道覆盖情况
    if CHANNEL_CATEGORIES:
        total_possible_channels = sum(len(channels_list) for channels_list in CHANNEL_CATEGORIES.values())
        coverage_rate = (channel_count / total_possible_channels * 100) if total_possible_channels > 0 else 0
        logger.info(f"频道覆盖比例: {coverage_rate:.1f}%")
    
    return grouped_channels

def validate_url(url, timeout=5):
    """
    简单验证URL是否可访问（可选功能，可在需要时启用）
    :param url: 要验证的URL
    :param timeout: 超时时间
    :return: 是否可访问
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Range": "bytes=0-1024"  # 只请求部分内容以提高效率
        }
        # 使用HEAD请求或GET请求的部分内容
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        # 检查响应状态码
        return response.status_code in [200, 206, 302, 304]
    except Exception:
        return False

def generate_output_file(grouped_channels, output_file=OUTPUT_FILE):
    """
    生成输出文件，并添加genre标签
    :param grouped_channels: 分组后的频道字典
    :param output_file: 输出文件名
    :return: 生成是否成功
    """
    start_time = time.time()
    
    # 验证输出文件路径
    if not output_file:
        logger.error("错误: 输出文件路径为空")
        return False
        
    logger.info(f"开始生成输出文件: {output_file}")
    
    # 计算统计信息 - 优化计算方式
    total_channels = 0
    total_urls = 0
    category_stats = {}
    
    for category in CATEGORY_ORDER:
        if category in grouped_channels and grouped_channels[category]:
            channel_count = len(grouped_channels[category])
            # 预计算并缓存URL数量
            url_count = sum(len(urls) for urls in grouped_channels[category].values())
            
            total_channels += channel_count
            total_urls += url_count
            category_stats[category] = {
                'channel_count': channel_count,
                'url_count': url_count
            }
    
    logger.info(f"统计完成: 共{total_channels}个频道，{total_urls}条线路")
    
    # 确保输出目录存在
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"创建输出目录: {output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {str(e)}")
            return False
    
    # 使用临时文件写入，避免部分写入导致的文件损坏
    temp_file = output_file + '.tmp'
    
    # 生成备份文件
    backup_file = output_file + '.bak'
    if os.path.exists(output_file):
        try:
            shutil.copy2(output_file, backup_file)
            logger.info(f"已创建文件备份: {backup_file}")
        except Exception as e:
            logger.warning(f"创建备份文件失败，但将继续执行: {str(e)}")
    
    # 写入成功计数器
    written_lines = 0
    
    try:
        # 使用缓冲区优化写入性能
        with open(temp_file, 'w', encoding='utf-8', buffering=8192) as f:
            # 写入文件头部信息
            header_lines = [
                "# 电视直播线路自动整理文件\n",
                f"# 更新时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                f"# 频道总数: {total_channels}\n",
                f"# 线路总数: {total_urls}\n",
                f"# 数据源数量: {len(GITHUB_SOURCES)}\n",
                "# 格式: 频道名称,线路URL\n",
                "# 分类顺序: 4K频道 > 央视频道 > 卫视频道 > 北京专属频道 > 山东专属频道 > 港澳频道 > 电影频道 > 儿童频道 > iHOT频道 > 综合频道 > 剧场频道 > 体育频道 > 音乐频道\n\n"
            ]
            f.writelines(header_lines)
            written_lines += len(header_lines)
            
            # 预分配内存减少重新分配开销
            batch_lines = []
            batch_size = 1000  # 每批次处理的行数
            
            # 按指定顺序写入每个分类
            for category in CATEGORY_ORDER:
                # 检查该分类是否存在且有频道
                if category not in grouped_channels or not grouped_channels[category]:
                    logger.info(f"分类 '{category}' 没有符合条件的频道，跳过")
                    continue
                
                # 获取该分类的统计信息
                stats = category_stats.get(category, {'channel_count': 0, 'url_count': 0})
                
                # 写入分类标题，添加genre标签
                category_line = f"# {category},#genre#\n"
                batch_lines.append(category_line)
                written_lines += 1
                
                logger.info(f"正在写入分类: {category} ({stats['channel_count']}个频道, {stats['url_count']}条线路)")
                
                # 获取该分类下的所有频道
                channels = grouped_channels[category]
                
                # 优化排序逻辑
                if category == "央视频道":
                    # 央视频道按数字顺序排序
                    sorted_channels = sorted(channels.items(), key=lambda x: (
                        re.search(r'\d+', x[0]) and int(re.search(r'\d+', x[0]).group()) or float('inf'),
                        x[0]
                    ))
                else:
                    # 其他分类按名称排序
                    sorted_channels = sorted(channels.items(), key=lambda x: x[0])
                
                # 批量处理写入操作以提高性能
                for channel_name, urls in sorted_channels:
                    logger.debug(f"  - 正在写入频道: {channel_name} ({len(urls)}条线路)")
                    
                    # 批量处理URL写入
                    for url in urls:
                        # 确保URL格式正确
                        clean_url = url.strip('\"\'').strip()
                        batch_lines.append(f"{channel_name},{clean_url}\n")
                        written_lines += 1
                        
                        # 当积累到一定数量的行时，批量写入
                        if len(batch_lines) >= batch_size:
                            f.writelines(batch_lines)
                            batch_lines.clear()
                
                # 在分类结束后添加空行
                batch_lines.append("\n")
                written_lines += 1
                
                # 确保该分类的所有行都被写入
                if batch_lines:
                    f.writelines(batch_lines)
                    batch_lines.clear()
        
        logger.info(f"文件写入完成，共写入 {written_lines} 行")
        
        # 使用shutil.move确保原子操作，避免文件损坏
        shutil.move(temp_file, output_file)
        
        # 验证生成的文件
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            elapsed_time = time.time() - start_time
            logger.info(f"✓ 输出文件生成完成: {output_file}, 文件大小: {file_size/1024:.2f} KB, 耗时: {elapsed_time:.2f} 秒")
            
            # 验证文件内容格式
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    # 只读取文件末尾部分进行验证
                    f.seek(max(0, file_size - 1000))
                    last_part = f.read()
                
                if first_line.startswith('# 电视直播线路自动整理文件') and '#genre#' in last_part:
                    logger.info("✓ 输出文件格式验证通过")
                    return True
                else:
                    logger.warning("✗ 输出文件格式可能有问题，请检查")
                    # 尝试恢复备份
                    if os.path.exists(backup_file):
                        shutil.copy2(backup_file, output_file)
                        logger.info("  已从备份恢复文件")
                    return False
            except Exception as e:
                logger.error(f"验证文件内容时出错: {str(e)}")
                return False
        else:
            logger.error(f"✗ 输出文件生成失败: {output_file}")
            # 尝试恢复备份
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, output_file)
                logger.info("  已从备份恢复文件")
            return False
            
    except IOError as io_err:
        logger.error(f"✗ 生成输出文件时出现IO错误: {str(io_err)}")
        # 记录详细信息
        logger.error(f"  错误详情: 文件名={temp_file}, 操作系统错误={io_err.errno}")
    except Exception as e:
        logger.error(f"✗ 生成输出文件时出错: {str(e)}")
        logger.exception("详细错误栈:")
    finally:
        # 确保临时文件被清理
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.debug(f"已清理临时文件: {temp_file}")
            except:
                logger.warning(f"无法删除临时文件: {temp_file}")
        
        # 尝试恢复备份
        if not os.path.exists(output_file) and os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, output_file)
                logger.info("  已从备份恢复文件")
            except:
                logger.error("  从备份恢复文件失败")
    
    return False

def reorder_channels_by_category(grouped_channels):
    """
    确保频道严格按照指定的分类顺序排列
    :param grouped_channels: 分组后的频道字典
    :return: 重新排序后的频道字典
    """
    logger.info("开始按指定顺序重新排列频道分类")
    
    # 创建一个新的有序字典，严格按照CATEGORY_ORDER的顺序
    ordered_channels = {}
    
    # 按顺序添加每个分类
    for category in CATEGORY_ORDER:
        if category in grouped_channels and grouped_channels[category]:
            ordered_channels[category] = grouped_channels[category]
        else:
            # 即使为空也添加，保持结构一致性
            ordered_channels[category] = {}
    
    logger.info(f"频道分类重排完成，共包含 {len([c for c in ordered_channels if ordered_channels[c]])} 个非空分类")
    return ordered_channels

def main():
    """
    主函数，优化版，增加了详细的性能监控和错误处理
    """
    logger.info("===== 电视直播线路自动整理脚本启动 =====")
    
    start_time = time.time()
    
    try:
        # 1. 收集所有频道
        logger.info("开始收集数据源...")
        collect_start = time.time()
        all_channels = collect_all_channels()
        collect_end = time.time()
        logger.info(f"数据源收集完成，共获取 {len(all_channels)} 个原始频道，耗时: {collect_end - collect_start:.2f} 秒")
        
        # 2. 筛选和分组频道 - 可能是性能瓶颈，添加详细计时
        logger.info("开始筛选高质量线路...")
        filter_start = time.time()
        grouped_channels = filter_and_group_channels(all_channels)
        filter_end = time.time()
        total_filtered = sum(len(channels) for channels in grouped_channels.values())
        logger.info(f"线路筛选完成，共 {total_filtered} 个频道通过筛选，耗时: {filter_end - filter_start:.2f} 秒")
        logger.info(f"过滤效率: {(total_filtered / len(all_channels) * 100):.1f}% 的频道通过筛选")
        
        # 3. 按指定顺序重新排列频道分类
        logger.info("开始按指定顺序重新排列频道分类...")
        reorder_start = time.time()
        ordered_channels = reorder_channels_by_category(grouped_channels)
        reorder_end = time.time()
        logger.info(f"频道分类排序完成，耗时: {reorder_end - reorder_start:.2f} 秒")
        
        # 4. 生成输出文件
        logger.info("开始生成输出文件...")
        output_start = time.time()
        generate_output_file(ordered_channels)
        output_end = time.time()
        logger.info(f"输出文件生成完成，耗时: {output_end - output_start:.2f} 秒")
        
        # 5. 计算总耗时并输出性能分析
        end_time = time.time()
        total_duration = end_time - start_time
        logger.info(f"===== 脚本执行完成，总耗时: {total_duration:.2f} 秒 =====")
        
        # 输出各阶段耗时占比
        collect_percent = (collect_end - collect_start) / total_duration * 100
        filter_percent = (filter_end - filter_start) / total_duration * 100
        reorder_percent = (reorder_end - reorder_start) / total_duration * 100
        output_percent = (output_end - output_start) / total_duration * 100
        
        logger.info(f"性能分析:")
        logger.info(f"- 数据收集: {collect_percent:.1f}% ({collect_end - collect_start:.2f}s)")
        logger.info(f"- 频道筛选: {filter_percent:.1f}% ({filter_end - filter_start:.2f}s)")
        logger.info(f"- 分类排序: {reorder_percent:.1f}% ({reorder_end - reorder_start:.2f}s)")
        logger.info(f"- 文件生成: {output_percent:.1f}% ({output_end - output_start:.2f}s)")
        logger.info(f"电视直播线路收集整理任务执行完成")
        
    except MemoryError:
        logger.error("执行过程中出现内存错误，请检查数据量是否过大")
        raise
    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        raise
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        import traceback
        logger.error(f"错误堆栈:\n{traceback.format_exc()}")
        raise

def run_scheduled_task():
    """
    执行定时任务
    """
    # 确保使用北京时间
    logger.info("正在初始化定时任务，设置为每天北京时间凌晨3点执行更新")
    
    # 设置每天北京时间凌晨3点执行任务
    schedule.every().day.at("03:00").do(lambda: execute_main_with_error_handling())
    
    logger.info("定时任务已成功启动，将在每天北京时间凌晨3点自动执行更新")
    logger.info("当前系统时间: %s", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("下次执行时间: %s", get_next_run_time())
    
    # 持续运行定时任务
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("用户中断了定时任务")
    except Exception as e:
        logger.error(f"定时任务运行出错: {str(e)}", exc_info=True)
        # 重新启动定时任务
        logger.info("尝试重新启动定时任务...")
        run_scheduled_task()

def execute_main_with_error_handling():
    """
    包装main函数，添加错误处理
    """
    try:
        logger.info("========== 开始定时更新任务 ==========")
        main()
        logger.info("========== 定时更新任务完成 ==========")
    except Exception as e:
        logger.error(f"定时更新任务执行失败: {str(e)}", exc_info=True)
        # 可以添加通知机制，如发送邮件或消息

def get_next_run_time():
    """
    获取下次执行时间的格式化字符串
    """
    now = datetime.datetime.now()
    next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
    if now >= next_run:
        next_run += datetime.timedelta(days=1)
    return next_run.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    # 立即执行一次任务
    logger.info("程序启动，开始执行初始更新任务...")
    main()
    
    # 然后启动定时任务
    logger.info("初始更新任务完成，启动定时任务服务...")
    run_scheduled_task()
