#!/usr/bin/env python3
# tvzy_autocollect.py


import requests
import re
import json
from datetime import datetime
import time
import os
import random
from urllib.parse import urlparse


class TVSourceCollector:
    def __init__(self):
        self.sources = []
        
        # 频道分组定义
        self.channel_categories = {
            "4K": ['CCTV4K', 'CCTV16 4K', '北京卫视4K', '北京IPTV4K', '湖南卫视4K', '山东卫视4K','广东卫视4K', '四川卫视4K', 
                 '浙江卫视4K', '江苏卫视4K', '东方卫视4K', '深圳卫视4K', '河北卫视4K', '峨眉电影4K', '求索4K', '咪视界4K', '欢笑剧场4K',
                 '苏州4K', '至臻视界4K', '南国都市4K', '翡翠台4K', '百事通电影4K', '百事通少儿4K', '百事通纪实4K', '华数爱上4K'],


            "央视": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4欧洲', 'CCTV4美洲', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '兵器科技', '风云音乐', '风云足球',
                 '风云剧场', '怀旧剧场', '第一剧场', '女性时尚', '世界地理', '央视台球', '高尔夫网球', '央视文化精品', '北京纪实科教',
                 '卫生健康','电视指南'],
            "卫视": ['山东卫视', '浙江卫视', '江苏卫视', '东方卫视', '深圳卫视', '北京卫视', '广东卫视', '广西卫视', '东南卫视', '海南卫视',
                 '河北卫视', '河南卫视', '湖北卫视', '江西卫视', '四川卫视', '重庆卫视', '贵州卫视', '云南卫视', '天津卫视', '安徽卫视',
                 '湖南卫视', '辽宁卫视', '黑龙江卫视', '吉林卫视', '内蒙古卫视', '宁夏卫视', '山西卫视', '陕西卫视', '甘肃卫视',
                 '青海卫视', '新疆卫视', '西藏卫视', '三沙卫视', '厦门卫视', '兵团卫视', '延边卫视', '安多卫视', '康巴卫视', '农林卫视', '山东教育',
                 'CETV1', 'CETV2', 'CETV3', 'CETV4', '早期教育'],


            "北京专属": ['北京卫视', '北京财经', '北京纪实', '北京生活', '北京体育休闲', '北京国际', '北京文艺', '北京新闻', 
                 '北京淘电影', '北京淘剧场', '北京淘4K', '北京淘娱乐', '北京淘BABY', '北京萌宠TV'],


            "山东专属": ['山东卫视', '山东齐鲁', '山东综艺', '山东少儿', '山东生活',
                 '山东新闻', '山东国际', '山东体育', '山东文旅', '山东农科'],


            "港澳台": ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影'],


            "影视剧": ['CHC动作电影', 'CHC家庭影院', 'CHC影迷电影', '淘电影',
                 '淘精彩', '淘剧场', '星空卫视', '黑莓电影', '东北热剧',
                 '中国功夫', '动作电影', '超级电影'],
            "音乐": ['动漫秀场', '哒啵电竞', '黑莓动画', '卡酷少儿',
                 '金鹰卡通', '优漫卡通', '哈哈炫动', '嘉佳卡通'],
            "体育": ['iHOT爱喜剧', 'iHOT爱科幻', 'iHOT爱院线', 'iHOT爱悬疑', 'iHOT爱历史', 'iHOT爱谍战', 'iHOT爱旅行', 'iHOT爱幼教',
                 'iHOT爱玩具', 'iHOT爱体育', 'iHOT爱赛车', 'iHOT爱浪漫', 'iHOT爱奇谈', 'iHOT爱科学', 'iHOT爱动漫'],
            "综合": ['重温经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活',
                 '求索动物', '睛彩青少', '睛彩竞技', '睛彩篮球', '睛彩广场舞', '金鹰纪实', '快乐垂钓', '茶频道', '军事评论',
                 '军旅剧场', '乐游', '生活时尚', '都市剧场', '欢笑剧场', '游戏风云', '金色学堂', '法治天地', '哒啵赛事'],
            "剧场": ['天元围棋', '魅力足球', '五星体育', '劲爆体育', '超级体育'],
            "其他": ['古装剧场', '家庭剧场', '惊悚悬疑', '明星大片', '欢乐剧场', '海外剧场', '潮妈辣婆',
                 '爱情喜剧', '超级电视剧', '超级综艺', '金牌综艺', '武搏世界', '农业致富', '炫舞未来',
                 '精品体育', '精品大剧', '精品纪录', '精品萌宠', '怡伴健康'],
        }
        
        # 频道别名映射
        self.channel_mapping = {
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
            "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品"],
            "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
            "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
            "北京纪实科教": ["纪实科教", "纪实科教8K", "北京纪实"],
            # 卫视频道
            "山东卫视": ["山东卫视 HD"],
            "浙江卫视": ["浙江卫视 HD"],
            "江苏卫视": ["江苏卫视 HD"],
            "东方卫视": ["东方卫视 HD"],
            "深圳卫视": ["深圳卫视 HD"],
            "北京卫视": ["北京卫视 HD"],
            "广东卫视": ["广东卫视 HD"],
            "广西卫视": ["广西卫视 HD"],
            "东南卫视": ["东南卫视 HD"],
            "海南卫视": ["海南卫视 HD"],
            "河北卫视": ["河北卫视 HD"],
            "河南卫视": ["河南卫视 HD"],
            "湖北卫视": ["湖北卫视 HD"],
            "江西卫视": ["江西卫视 HD"],
            "四川卫视": ["四川卫视 HD"],
            "重庆卫视": ["重庆卫视 HD"],
            "贵州卫视": ["贵州卫视 HD"],
            "云南卫视": ["云南卫视 HD"],
            "天津卫视": ["天津卫视 HD"],
            "安徽卫视": ["安徽卫视 HD"],
            "湖南卫视": ["湖南卫视 HD"],
            "辽宁卫视": ["辽宁卫视 HD"],
            "黑龙江卫视": ["黑龙江卫视 HD", "龙江卫视", "龙江卫视 HD"],
            "吉林卫视": ["吉林卫视 HD"],
            "内蒙古卫视": ["内蒙古卫视 HD", "内蒙卫视", "内蒙卫视 HD"],
            "宁夏卫视": ["宁夏卫视 HD"],
            "山西卫视": ["山西卫视 HD"],
            "陕西卫视": ["陕西卫视 HD"],
            "甘肃卫视": ["甘肃卫视 HD"],
            "青海卫视": ["青海卫视 HD"],
            "新疆卫视": ["新疆卫视 HD"],
            "西藏卫视": ["西藏卫视 HD"],
            "三沙卫视": ["三沙卫视 HD"],
            "厦门卫视": ["厦门卫视 HD"],
            "兵团卫视": ["兵团卫视 HD"],
            "延边卫视": ["延边卫视 HD"],
            "安多卫视": ["安多卫视 HD"],
            "康巴卫视": ["康巴卫士 HD"],
            "农林卫视": ["农林卫视 HD"],
            "山东教育": ["山东教育卫视", "IPTV山东教育"],
            "CETV1": ["中国教育1台", "中国教育一台", "中国教育1", "CETV-1 综合教育", "CETV-1"],
            "CETV2": ["中国教育2台", "中国教育二台", "中国教育2", "CETV-2 空中课堂", "CETV-2"],
            "CETV3": ["中国教育3台", "中国教育三台", "中国教育3", "CETV-3 教育服务", "CETV-3"],
            "CETV4": ["中国教育4台", "中国教育四台", "中国教育4", "CETV-4 职业教育", "CETV-4"],
            "早期教育": ["中国教育5台", "中国教育5", "中国教育五台", "CETV早期教育", "CETV-早期教育", "CETV 早期教育", "CETV-5", "CETV5"],
            # 北京专属频道
            "北京卫视": ["北京卫视 HD"],
            "北京财经": ["北京财经 HD"],
            "北京纪实": ["北京纪实 HD"],
            "北京生活": ["北京生活 HD"],
            "北京体育休闲": ["北京体育休闲 HD"],
            "北京国际": ["北京国际 HD"],
            "北京文艺": ["北京文艺 HD"],
            "北京新闻": ["北京新闻 HD"],
            "北京淘电影": ["IPTV淘电影", "北京IPTV淘电影", "淘电影"],
            "北京淘剧场": ["IPTV淘剧场", "北京IPTV淘剧场", "淘剧场"],
            "北京淘4K": ["IPTV淘4K", "北京IPTV淘4K", "北京IPTV4K超清", "淘 4K"],
            "北京淘娱乐": ["IPTV淘娱乐", "北京IPTV淘娱乐", "淘娱乐"],
            "北京淘BABY": ["IPTV淘BABY", "北京IPTV淘BABY", "北京淘Baby", "IPTV淘baby", "IPTV淘Baby", "北京IPTV淘baby", "北京淘baby"],
            "北京萌宠TV": ["IPTV淘萌宠", "北京IPTV淘萌宠", "北京淘萌宠"],
            # 山东专属频道
            "山东卫视": ["山东卫视频道", "山东卫视 HD"],
            "山东齐鲁": ["山东齐鲁频道", "齐鲁频道 HD"],
            "山东综艺": ["山东综艺频道", "山东综艺 HD"],
            "山东少儿": ["山东少儿频道", "山东少儿频道 HD"],
            "山东生活": ["山东生活频道", "山东生活频道 HD"],
            "山东新闻": ["山东新闻频道", "山东新闻频道 HD"],
            "山东国际": ["山东国际频道", "山东新闻频道 HD"],
            "山东体育": ["山东体育频道", "山东体育频道 HD"],
            "山东文旅": ["山东文旅频道", "山东文旅频道 HD"],
            # 港澳频道
            "凤凰中文": ["凤凰卫视中文台", "凤凰中文台", "凤凰卫视中文"],
            "凤凰资讯": ["凤凰卫视资讯台", "凤凰资讯台", "凤凰咨询", "凤凰咨询台", "凤凰卫视咨询台", "凤凰卫视资讯", "凤凰卫视咨询"],
            "凤凰香港": ["凤凰卫视香港台", "凤凰卫视香港", "凤凰香港"],
            "凤凰电影": ["凤凰卫视电影台", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台", "凤凰电影"],
            # 电影频道
            "CHC动作电影": ["CHC动作电影 HD"],
            "CHC家庭影院": ["CHC家庭影院 HD"],
            "CHC影迷电影": ["CHC高清电影", "chc影迷电影", "影迷电影", "chc高清电影", "CHC影迷电影 HD"],
            "淘电影": ["IPTV淘电影", "北京IPTV淘电影", "北京淘电影"],
            "淘精彩": ["IPTV淘精彩", "北京IPTV淘精彩", "北京淘精彩"],
            "淘剧场": ["IPTV淘剧场", "北京IPTV淘剧场", "北京淘剧场"],
            "星空卫视": ["星空卫视 HD"],
            "黑莓电影": ["黑莓电影 HD"],
            "东北热剧": ["NewTV东北热剧", "NewTV 东北热剧", "newtv 东北热剧", "NEWTV 东北热剧", "NEWTV东北热剧"],
            "中国功夫": ["NewTV中国功夫", "NewTV 中国功夫", "newtv 中国功夫", "NEWTV 中国功夫", "NEWTV中国功夫"],
            "动作电影": ["NewTV动作电影", "NewTV 动作电影", "newtv 动作电影", "NEWTV 动作电影", "NEWTV动作电影"],
            "超级电影": ["NewTV超级电影", "NewTV 超级电影", "newtv 超级电影", "NEWTV 超级电影", "NEWTV超级电影"],
            # 儿童频道
            "动漫秀场": ["动漫秀场4K", "SiTV动漫秀场", "SiTV 动漫秀场", "上海动漫秀场"],
            "哒啵电竞": ["哒啵电竞 HD"],
            "黑莓动画": ["黑莓动画 HD"],
            "卡酷少儿": ["北京卡酷", "卡酷卡通", "北京卡酷少儿", "卡酷动画"],
            "金鹰卡通": ["金鹰卡通 HD"],
            "优漫卡通": ["优漫卡通 HD"],
            "哈哈炫动": ["炫动卡通", "上海哈哈炫动", "哈哈炫动 HD"],
            "嘉佳卡通": ["嘉佳卡通 HD"],
            # iHOT频道
            "iHOT爱喜剧": ["iHOT 爱喜剧", "IHOT 爱喜剧", "IHOT爱喜剧", "ihot爱喜剧", "爱喜剧", "ihot 爱喜剧"],
            "iHOT爱科幻": ["iHOT 爱科幻", "IHOT 爱科幻", "IHOT爱科幻", "ihot爱科幻", "爱科幻", "ihot 爱科幻"],
            "iHOT爱院线": ["iHOT 爱院线", "IHOT 爱院线", "IHOT爱院线", "ihot爱院线", "ihot 爱院线", "爱院线"],
            "iHOT爱悬疑": ["iHOT 爱悬疑", "IHOT 爱悬疑", "IHOT爱悬疑", "ihot爱悬疑", "ihot 爱悬疑", "爱悬疑"],
            "iHOT爱历史": ["iHOT 爱历史", "IHOT 爱历史", "IHOT爱历史", "ihot爱历史", "ihot 爱历史", "爱历史"],
            "iHOT爱谍战": ["iHOT 爱谍战", "IHOT 爱谍战", "IHOT爱谍战", "ihot爱谍战", "ihot 爱谍战", "爱谍战"],
            "iHOT爱旅行": ["iHOT 爱旅行", "IHOT 爱旅行", "IHOT爱旅行", "ihot爱旅行", "ihot 爱旅行", "爱旅行"],
            "iHOT爱幼教": ["iHOT 爱幼教", "IHOT 爱幼教", "IHOT爱幼教", "ihot爱幼教", "ihot 爱幼教", "爱幼教"],
            "iHOT爱玩具": ["iHOT 爱玩具", "IHOT 爱玩具", "IHOT爱玩具", "ihot爱玩具", "ihot 爱玩具", "爱玩具"],
            "iHOT爱体育": ["iHOT 爱体育", "IHOT 爱体育", "IHOT爱体育", "ihot爱体育", "ihot 爱体育", "爱体育"],
            "iHOT爱赛车": ["iHOT 爱赛车", "IHOT 爱赛车", "IHOT爱赛车", "ihot爱赛车", "ihot 爱赛车", "爱赛车"],
            "iHOT爱浪漫": ["iHOT 爱浪漫", "IHOT 爱浪漫", "IHOT爱浪漫", "ihot爱浪漫", "ihot 爱浪漫", "爱浪漫"],
            "iHOT爱奇谈": ["iHOT 爱奇谈", "IHOT 爱奇谈", "IHOT爱奇谈", "ihot爱奇谈", "ihot 爱奇谈", "爱奇谈"],
            "iHOT爱科学": ["iHOT 爱科学", "IHOT 爱科学", "IHOT爱科学", "ihot爱科学", "ihot 爱科学", "爱科学"],
            "iHOT爱动漫": ["iHOT 爱动漫", "IHOT 爱动漫", "IHOT爱动漫", "ihot爱动漫", "ihot 爱动漫", "爱动漫"],
            # 综合频道
            "重温经典": ["重温经典 HD"],
            "CHANNEL[V]": ["CHANNEL V", "Channel V"],
            "求索纪录": ["求索记录", "求索纪录4K", "求索记录4K", "求索纪录 4K", "求索记录 4K"],
            "求索科学": ["求索科学 HD"],
            "求索生活": ["求索生活 HD"],
            "求索动物": ["求索动物 HD"],
            "睛彩青少": ["睛彩青少 HD"],
            "睛彩竞技": ["睛彩竞技 HD"],
            "睛彩篮球": ["睛彩篮球 HD"],
            "睛彩广场舞": ["睛彩广场舞 HD"],
            "金鹰纪实": ["湖南金鹰纪实", "金鹰记实", "金鹰纪实 HD"],
            "快乐垂钓": ["快乐垂钓 HD"],
            "茶频道": ["茶频道 HD"],
            "军事评论": ["NewTV军事评论", "NewTV 军事评论", "newtv 军事评论", "NEWTV 军事评论", "NEWTV军事评论"],
            "军旅剧场": ["NewTV军旅剧场", "NewTV 军旅剧场", "newtv 军旅剧场", "NEWTV 军旅剧场", "NEWTV军旅剧场"],
            "乐游": ["乐游频道", "全纪实", "SiTV乐游", "SiTV乐游频道", "SiTV 乐游频道", "上海乐游频道"],
            "生活时尚": ["生活时尚4K", "SiTV生活时尚", "SiTV 生活时尚", "上海生活时尚"],
            "都市剧场": ["都市剧场4K", "SiTV都市剧场", "SiTV 都市剧场", "上海都市剧场"],
            "欢笑剧场": ["欢笑剧场4K", "欢笑剧场 4K", "SiTV欢笑剧场", "SiTV 欢笑剧场", "上海欢笑剧场"],
            "游戏风云": ["游戏风云4K", "SiTV游戏风云", "SiTV 游戏风云", "上海游戏风云"],
            "金色学堂": ["金色学堂4K", "SiTV金色学堂", "SiTV 金色学堂"],
            "法治天地": ["法治天地 HD", "上海法治天地"],
            "哒啵赛事": ["哒啵赛事 HD"],
            # 体育频道
            "天元围棋": ["天元围棋 HD"],
            "魅力足球": ["魅力足球 HD"],
            "五星体育": ["五星体育 HD"],
            "劲爆体育": ["劲爆体育 HD"],
            "超级体育": ["NewTV超级体育", "NewTV 超级体育", "newtv 超级体育", "NEWTV 超级体育", "NEWTV超级体育"],
            # 剧场频道
            "古装剧场": ["NewTV古装剧场", "NewTV 古装剧场", "newtv 古装剧场", "NEWTV 古装剧场", "NEWTV古装剧场"],
            "家庭剧场": ["NewTV家庭剧场", "NewTV 家庭剧场", "newtv 家庭剧场", "NEWTV 家庭剧场", "NEWTV家庭剧场"],
            "惊悚悬疑": ["NewTV惊悚悬疑", "NewTV 惊悚悬疑", "newtv 惊悚悬疑", "NEWTV 惊悚悬疑", "NEWTV惊悚悬疑"],
            "明星大片": ["NewTV明星大片", "NewTV 明星大片", "newtv 明星大片", "NEWTV 明星大片", "NEWTV明星大片"],
            "欢乐剧场": ["NewTV欢乐剧场", "NewTV 欢乐剧场", "newtv 欢乐剧场", "NEWTV 欢乐剧场", "NEWTV欢乐剧场"],
            "海外剧场": ["NewTV海外剧场", "NewTV 海外剧场", "newtv 海外剧场", "NEWTV 海外剧场", "NEWTV海外剧场"],
            "潮妈辣婆": ["NewTV潮妈辣婆", "NewTV 潮妈辣婆", "newtv 潮妈辣婆", "NEWTV 潮妈辣婆", "NEWTV潮妈辣婆"],
            "爱情喜剧": ["NewTV爱情喜剧", "NewTV 爱情喜剧", "newtv 爱情喜剧", "NEWTV 爱情喜剧", "NEWTV爱情喜剧"],
            "超级电视剧": ["NewTV超级电视剧", "NewTV 超级电视剧", "newtv 超级电视剧", "NEWTV 超级电视剧", "NEWTV超级电视剧"],
            "超级综艺": ["NewTV超级综艺", "NewTV 超级综艺", "newtv 超级综艺", "NEWTV 超级综艺", "NEWTV超级综艺"],
            "金牌综艺": ["NewTV金牌综艺", "NewTV 金牌综艺", "newtv 金牌综艺", "NEWTV 金牌综艺", "NEWTV金牌综艺"],
            "武搏世界": ["NewTV武搏世界", "NewTV 武搏世界", "newtv 武搏世界", "NEWTV 武搏世界", "NEWTV武搏世界"],
            "农业致富": ["NewTV农业致富", "NewTV 农业致富", "newtv 农业致富", "NEWTV 农业致富", "NEWTV农业致富"],
            "炫舞未来": ["NewTV炫舞未来", "NewTV 炫舞未来", "newtv 炫舞未来", "NEWTV 炫舞未来", "NEWTV炫舞未来"],
            "精品体育": ["NewTV精品体育", "NewTV 精品体育", "newtv 精品体育", "NEWTV 精品体育", "NEWTV精品体育"],
            "精品大剧": ["NewTV精品大剧", "NewTV 精品大剧", "newtv 精品大剧", "NEWTV 精品大剧", "NEWTV精品大剧"],
            "精品纪录": ["NewTV精品纪录", "NewTV 精品纪录", "newtv 精品纪录", "NEWTV 精品纪录", "NEWTV精品纪录"],
            "精品萌宠": ["NewTV精品萌宠", "NewTV 精品萌宠", "newtv 精品萌宠", "NEWTV 精品萌宠", "NEWTV精品萌宠"],
            "怡伴健康": ["NewTV怡伴健康", "NewTV 怡伴健康", "newtv 怡伴健康", "NEWTV 怡伴健康", "NEWTV怡伴健康"],
        }
        
        # 创建反向映射：别名 -> 规范名
        self.alias_to_standard = {}
        for standard_name, aliases in self.channel_mapping.items():
            # 规范名本身也是一个有效的名称
            self.alias_to_standard[standard_name.lower()] = standard_name
            for alias in aliases:
                self.alias_to_standard[alias.lower()] = standard_name
        
        # 创建分类映射：规范名 -> 分类
        self.standard_to_category = {}
        for category, channels in self.channel_categories.items():
            for channel in channels:
                self.standard_to_category[channel] = category
        
        # 初始化输出分类（合并一些分类以符合要求）
        self.output_categories = {
            "4K": [],
            "央视": [],
            "卫视": [], 
            "港澳台": [],
            "影视剧": [],
            "音乐": [],
            "体育": []
        }
        
        # 分类合并映射（将详细分类合并到输出分类）
        self.category_merge_map = {
            "4K": ["4K"],
            "央视": ["央视"],
            "卫视": ["卫视", "北京专属", "山东专属"],
            "港澳台": ["港澳台"],
            "影视剧": ["影视剧", "剧场", "其他"],
            "音乐": ["音乐"],
            "体育": ["体育", "综合"]
        }
        
        # 真实数据源列表
        self.data_sources = [
            # GitHub上的直播源
            "http://106.53.99.30/2025.txt",
            "http://tv.html-5.me/i/9390107.txt",
            "https://ghcy.eu.org/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
            "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
            "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
            
            # 其他直播源
            "https://mirror.ghproxy.com/https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
  

            
            # 备份源

        ]
        
    def normalize_channel_name(self, channel_name):
        """
        将频道名称标准化为规范名
        """
        name_lower = channel_name.lower()
        
        # 查找匹配的别名
        for alias, standard in self.alias_to_standard.items():
            if alias in name_lower:
                return standard
        
        # 如果没有找到匹配的别名，返回原始名称
        return channel_name
    
    def get_channel_category(self, standard_name):
        """
        获取频道的分类
        """
        return self.standard_to_category.get(standard_name, None)
    
    def fetch_all_sources(self):
        """
        从多个数据源获取直播源
        """
        print(f"开始从 {len(self.data_sources)} 个数据源收集直播源...")
        
        for source_url in self.data_sources:
            try:
                print(f"正在获取源: {source_url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(source_url, timeout=15, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    print(f"获取成功，内容长度: {len(content)} 字符")
                    self.parse_content(content, source_url)
                else:
                    print(f"获取源失败，状态码: {response.status_code}")
                time.sleep(2) # 避免请求过于频繁
            except Exception as e:
                print(f"获取源 {source_url} 失败: {e}")
                continue
    
    def parse_content(self, content, source_url):
        """
        解析内容，支持多种格式
        """
        lines = content.split('\n')
        current_channel = {}
        format_detected = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 检测M3U格式
            if line.startswith('#EXTM3U'):
                format_detected = True
                continue
                
            # 解析EXTINF行
            if line.startswith('#EXTINF:'):
                current_channel = self.parse_extinf_line(line)
                current_channel['source'] = source_url
                continue
                
            # 如果是URL行且前面有EXTINF
            if line.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                if current_channel:
                    current_channel['url'] = line
                    # 标准化频道名称
                    original_name = current_channel['channel_name']
                    standard_name = self.normalize_channel_name(original_name)
                    current_channel['standard_name'] = standard_name
                    current_channel['original_name'] = original_name
                    
                    if self.check_quality(current_channel):
                        self.sources.append(current_channel.copy())
                    current_channel = {}
                else:
                    # 如果没有EXTINF，尝试从URL推断频道信息
                    self.parse_url_only(line, source_url)
                continue
                
            # 尝试解析文本格式：频道名称,URL
            if ',' in line and any(proto in line for proto in ['http://', 'https://', 'rtmp://']):
                parts = line.split(',', 1)
                if len(parts) == 2 and parts[1].startswith(('http://', 'https://', 'rtmp://')):
                    channel_name = parts[0].strip()
                    url = parts[1].strip()
                    if self.is_valid_url(url):
                        # 标准化频道名称
                        standard_name = self.normalize_channel_name(channel_name)
                        channel = {
                            'channel_name': channel_name,
                            'standard_name': standard_name,
                            'original_name': channel_name,
                            'url': url,
                            'source': source_url,
                            'quality': 'unknown'
                        }
                        if self.check_quality(channel):
                            self.sources.append(channel)
        
        if not format_detected and len(self.sources) == 0:
            print(f"警告: 无法识别 {source_url} 的格式")
    
    def parse_extinf_line(self, line):
        """
        解析EXTINF行
        """
        channel = {}
        
        # 提取tvg-name
        tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
        if tvg_name_match:
            channel['tvg_name'] = tvg_name_match.group(1)
        else:
            # 如果没有tvg-name，尝试从其他地方提取
            tvg_name_match = re.search(r'tvg-id="([^"]*)"', line)
            if tvg_name_match:
                channel['tvg_name'] = tvg_name_match.group(1)
        
        # 提取group-title
        group_match = re.search(r'group-title="([^"]*)"', line)
        if group_match:
            channel['group_title'] = group_match.group(1)
        
        # 提取频道名称（最后一个逗号后的内容）
        name_match = re.search(r',([^,]*)$', line)
        if name_match:
            channel['channel_name'] = name_match.group(1).strip()
        else:
            # 如果没有逗号，尝试其他解析方式
            channel['channel_name'] = line
        
        return channel
    
    def parse_url_only(self, url, source_url):
        """
        解析只有URL没有频道信息的情况
        """
        if self.is_valid_url(url):
            # 从URL推断频道名称
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            path = parsed_url.path
            
            # 尝试从路径中提取频道信息
            channel_name = "未知频道"
            if '/cctv' in path.lower():
                channel_name = "CCTV频道"
            elif '/tv' in path.lower():
                channel_name = "电视频道"
            elif 'live' in path.lower():
                channel_name = "直播频道"
                
            # 标准化频道名称
            standard_name = self.normalize_channel_name(channel_name)
            
            channel = {
                'channel_name': channel_name,
                'standard_name': standard_name,
                'original_name': channel_name,
                'url': url,
                'source': source_url,
                'quality': 'unknown'
            }
            if self.check_quality(channel):
                self.sources.append(channel)
    
    def is_valid_url(self, url):
        """
        检查URL是否有效
        """
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def check_quality(self, channel):
        """
        检查频道清晰度是否符合要求
        """
        name = channel['channel_name'].lower()
        standard_name = channel['standard_name'].lower()
        
        # 基于名称的简单过滤
        if '4k' in name or 'uhd' in name or '超高清' in name or '4k' in standard_name:
            channel['quality'] = '4K'
            return True
        elif '1080' in name or 'fhd' in name:
            channel['quality'] = '1080p'
            return True
        elif '高清' in name or 'hd' in name:
            channel['quality'] = '720p'
            return True
        elif 'test' in name or '演示' in name or 'sample' in name:
            return False # 过滤测试频道
        
        # 如果没有质量信息，默认接受（后面会进一步过滤）
        channel['quality'] = 'unknown'
        return True
    
    def categorize_channels(self):
        """
        将频道按规则分类，使用标准名和分类映射
        """
        # 先按详细分类分组
        detailed_categories = {}
        for category in self.channel_categories.keys():
            detailed_categories[category] = []
        
        for channel in self.sources:
            standard_name = channel['standard_name']
            category = self.get_channel_category(standard_name)
            
            if category and category in detailed_categories:
                detailed_categories[category].append(channel)
            else:
                # 如果没有找到分类，尝试使用关键词匹配
                self.fallback_categorize(channel, detailed_categories)
        
        # 合并到输出分类
        for output_cat, source_cats in self.category_merge_map.items():
            for source_cat in source_cats:
                if source_cat in detailed_categories:
                    self.output_categories[output_cat].extend(detailed_categories[source_cat])
    
    def fallback_categorize(self, channel, detailed_categories):
        """
        备用分类方法，用于未映射的频道
        """
        name = channel['standard_name'].lower()
        
        if '4k' in name or 'uhd' in name or '超高清' in name:
            detailed_categories["4K"].append(channel)
        elif 'cctv' in name or '央视' in name or '中央' in name:
            detailed_categories["央视"].append(channel)
        elif '卫视' in name:
            detailed_categories["卫视"].append(channel)
        elif any(keyword in name for keyword in ['凤凰', '翡翠', 'tvb', '澳亚', '港澳', '香港', '澳门', '台湾']):
            detailed_categories["港澳台"].append(channel)
        elif any(keyword in name for keyword in ['电影', '影院', '剧场', '影视', 'movie', 'iHOT']):
            detailed_categories["影视剧"].append(channel)
        elif any(keyword in name for keyword in ['音乐', 'mtv', 'music', '演唱会']):
            detailed_categories["音乐"].append(channel)
        elif any(keyword in name for keyword in ['体育', 'sports', 'cctv5', '运动', 'nba', '足球', '篮球']):
            detailed_categories["体育"].append(channel)
    
    def filter_quality_channels(self):
        """
        过滤出高质量频道
        """
        quality_sources = []
        for channel in self.sources:
            # 优先选择已知清晰度的频道
            if channel['quality'] in ['4K', '1080p', '720p']:
                quality_sources.append(channel)
        
        # 如果高质量频道不够，添加一些未知质量的频道
        if len(quality_sources) < 100:
            unknown_quality = [ch for ch in self.sources if ch['quality'] == 'unknown']
            # 随机选择一些未知质量的频道（但确保总数不超过限制）
            additional = min(len(unknown_quality), 200 - len(quality_sources))
            quality_sources.extend(unknown_quality[:additional])
        
        self.sources = quality_sources
    
    def limit_channels_per_group(self):
        """
        限制每个分组的频道数量
        """
        for category, channels in self.output_categories.items():
            if not channels:
                print(f"警告: {category} 分组没有频道")
                continue
                
            # 去重：基于URL去除重复频道
            unique_channels = {}
            for channel in channels:
                url = channel['url']
                if url not in unique_channels:
                    unique_channels[url] = channel
                else:
                    # 如果已有相同URL，选择质量更好的
                    existing = unique_channels[url]
                    if self.get_quality_score(channel) > self.get_quality_score(existing):
                        unique_channels[url] = channel
            
            unique_channel_list = list(unique_channels.values())
            
            # 按质量排序
            unique_channel_list.sort(key=lambda x: self.get_quality_score(x), reverse=True)
            
            # 限制数量：最少10个，最多90个
            if len(unique_channel_list) < 10:
                print(f"警告: {category} 分组频道数不足10个，当前为 {len(unique_channel_list)} 个")
                # 尝试从其他源补充
                self.supplement_channels(category, unique_channel_list)
            elif len(unique_channel_list) > 90:
                unique_channel_list = unique_channel_list[:90]
            
            self.output_categories[category] = unique_channel_list
    
    def supplement_channels(self, category, existing_channels):
        """
        补充频道数量不足的分组
        """
        if len(existing_channels) >= 10:
            return
            
        # 查找该分类对应的标准频道名
        standard_channels = []
        for output_cat, source_cats in self.category_merge_map.items():
            if output_cat == category:
                for source_cat in source_cats:
                    if source_cat in self.channel_categories:
                        standard_channels.extend(self.channel_categories[source_cat])
        
        if not standard_channels:
            return
            
        # 从其他数据源查找相关频道
        backup_sources = [
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/cn.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/hk.m3u",
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/tw.m3u",
        ]
        
        for source_url in backup_sources:
            try:
                response = requests.get(source_url, timeout=10)
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    current_channel = {}
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#EXTINF:'):
                            current_channel = self.parse_extinf_line(line)
                            current_channel['source'] = source_url
                        elif line.startswith(('http://', 'https://')):
                            if current_channel:
                                current_channel['url'] = line
                                # 标准化频道名称
                                original_name = current_channel['channel_name']
                                standard_name = self.normalize_channel_name(original_name)
                                current_channel['standard_name'] = standard_name
                                current_channel['original_name'] = original_name
                                
                                # 检查是否属于当前分类
                                if standard_name in standard_channels:
                                    # 检查是否已存在
                                    if not any(ch['url'] == current_channel['url'] for ch in existing_channels):
                                        existing_channels.append(current_channel.copy())
                                        if len(existing_channels) >= 10:
                                            return
                                current_channel = {}
            except Exception as e:
                print(f"补充 {category} 频道时出错: {e}")
                continue
    
    def get_quality_score(self, channel):
        """
        获取频道质量评分
        """
        quality_scores = {
            '4K': 4,
            '1080p': 3,
            '720p': 2,
            'unknown': 1
        }
        return quality_scores.get(channel['quality'], 0)
    
    def generate_output_file(self):
        """
        生成最终的输出文件
        """
        with open('tzyauto.txt', 'w', encoding='utf-8') as f:
            f.write("# 自动生成的直播源文件\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# 分组格式: 频道名称,频道URL,#genre#\n\n")
            
            # 按指定顺序输出分组
            category_order = ["4K", "央视", "卫视", "港澳台", "影视剧", "音乐", "体育"]
            
            for category in category_order:
                channels = self.output_categories.get(category, [])
                if channels:
                    f.write(f"\n# {category}频道,#genre#\n")
                    for channel in channels:
                        # 使用标准化名称输出
                        f.write(f"{channel['standard_name']},{channel['url']}\n")
        
        print(f"文件生成完成! 共处理 {len(self.sources)} 个频道")


def main():
    collector = TVSourceCollector()
    print("开始收集直播源...")
    collector.fetch_all_sources()
    print(f"初步收集到 {len(collector.sources)} 个频道")
    
    print("过滤高质量频道...")
    collector.filter_quality_channels()
    print(f"过滤后剩余 {len(collector.sources)} 个频道")
    
    print("开始分类频道...")
    collector.categorize_channels()
    
    print("限制各分组频道数量...")
    collector.limit_channels_per_group()
    
    print("生成输出文件...")
    collector.generate_output_file()
    
    # 输出统计信息
    print("\n=== 统计信息 ===")
    total_channels = 0
    for category, channels in collector.output_categories.items():
        print(f"{category}: {len(channels)} 个频道")
        total_channels += len(channels)
    
    # 质量统计
    quality_stats = {}
    for channel in collector.sources:
        quality = channel['quality']
        quality_stats[quality] = quality_stats.get(quality, 0) + 1
    
    print(f"\n=== 质量统计 ===")
    for quality, count in quality_stats.items():
        print(f"{quality}: {count} 个频道")
    
    print(f"\n总计: {total_channels} 个频道")


if __name__ == "__main__":
    main()
