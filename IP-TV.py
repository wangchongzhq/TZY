# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
IPTV鐩存挱婧愯嚜鍔ㄧ敓鎴愬伐鍏?
鍔熻兘锛氫粠澶氫釜鏉ユ簮鑾峰彇IPTV鐩存挱婧愬苟鐢熸垚M3U鏂囦欢
support锛氭墜鍔ㄦ洿鏂板拰閫氳繃GitHub Actions宸ヤ綔娴佸畾鏃舵洿鏂?
"""

import asyncio
import os
import re
import time
import requests
import datetime
import threading
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# 閰嶇疆鏃ュ織
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iptv_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 棰戦亾鍒嗙被
CHANNEL_CATEGORIES = {
    "4K棰戦亾": ['CCTV4K', 'CCTV8K', 'CCTV16 4K', '鍖椾含鍗4K', '鍖椾含IPTV4K', '婀栧崡鍗4K', '灞变笢鍗4K','骞夸笢鍗4K', '鍥涘窛鍗4K', 
                 '娴欐睙鍗4K', '姹熻嫃鍗4K', '涓滄柟鍗4K', '娣卞湷鍗4K', '娌冲寳鍗4K', '宄ㄧ湁鐢靛奖4K', '姹傜储4K', '鍜鐣?K', '娆㈢瑧鍓у満4K',
                 '鑻忓窞4K', '鑷宠嚮瑙嗙晫4K', '鍗楀浗閮藉競4K', '缈＄繝鍙?K', '鐧句簨閫氱數褰?K', '鐧句簨閫氬皯鍎?K', '鐧句簨閫氱邯瀹?K', '鍗庢暟鐖变笂4K'],

    "澶棰戦亾": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4娆ф床', 'CCTV4缇庢床', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                 'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '鍏靛櫒绉戞妧', '椋庝簯闊充箰', '椋庝簯瓒崇悆',
                 '凤凰电影', '实时赛场', '第一剧场', '精彩时刻', '世界地理', '卫视体育', '气象影视网', '卫视文化精品', '养生健康','电视指南'],
    "鍗棰戦亾": ['灞变笢鍗', '娴欐睙鍗', '姹熻嫃鍗', '涓滄柟鍗', '娣卞湷鍗', '鍖椾含鍗', '骞夸笢鍗', '骞胯タ鍗', '涓滃崡鍗', '娴峰崡鍗',
                 '娌冲寳鍗', '娌冲崡鍗', '婀栧寳鍗', '姹熻タ鍗', '鍥涘窛鍗', '閲嶅簡鍗', '璐靛窞鍗', '浜戝崡鍗', '澶╂触鍗', '瀹夊窘鍗',
                 '云南卫视', '甘肃卫视', '新疆卫视', '安徽卫视', '内蒙古卫视', '宁夏卫视', '西藏卫视', '青海卫视', '甘肃卫视',
                 '闈掓捣鍗', '鏂扮枂鍗', '瑗胯棌鍗', '涓夋矙鍗', '鍘﹂棬鍗', '鍏靛洟鍗', '寤惰竟鍗', '瀹夊鍗', '搴峰反鍗', '鍐滄灄鍗', '灞变笢鏁欒偛',
                 'CETV1', 'CETV2', 'CETV3', 'CETV4', '鏃╂湡鏁欒偛'],

    "鍖椾含涓撳睘棰戦亾": ['鍖椾含鍗', '鍖椾含璐㈢粡', '鍖椾含绾疄', '鍖椾含鐢熸椿', '鍖椾含浣撹偛浼戦棽', '鍖椾含鍥介檯', '鍖椾含鏂囪壓', '鍖椾含鏂伴椈', 
                 '北京纪实', '北京赛场', '北京4K', '北京文艺', '北京IPTVABY', '北京纪实TV', '北京卡酷少儿'],

    "灞变笢涓撳睘棰戦亾": ['灞变笢鍗', '灞变笢榻愰瞾', '灞变笢缁艰壓', '灞变笢灏戝効', '灞变笢鐢熸椿',
                 '灞变笢鏂伴椈', '灞变笢鍥介檯', '灞变笢浣撹偛', '灞变笢鏂囨梾', '灞变笢鍐滅'],

    "娓境棰戦亾": ['鍑ゅ嚢涓枃', '鍑ゅ嚢璧勮', '鍑ゅ嚢棣欐腐', '鍑ゅ嚢鐢靛奖'],

    "电影剧场": ['CHC动作电影', 'CHC家庭影院', 'CHC科幻电影', '纪实', '纪录', '赛场', '电影频道', '万达电影', '东北热影',
                 '涓浗鍔熷か', '鍔ㄤ綔鐢靛奖', '瓒呯骇鐢靛奖'],
    "儿童频道": ['动漫世界', '哈哈炫动', '万达动漫', '卡酷少儿',
                   '优漫卡通', '央视少儿', '华数动画', '东方卡通'],
    "iHOT频道": ['iHOT爱情剧', 'iHOT剧情片', 'iHOT院线档', 'iHOT动作片', 'iHOT古装剧', 'iHOT悬疑剧', 'iHOT纪录片', 'iHOT喜剧片',
                 'iHOT游戏档', 'iHOT动作片', 'iHOT赛事档', 'iHOT综艺档', 'iHOT搞笑档', 'iHOT科幻档', 'iHOT动漫档'],
    "综合频道": ['重低音经典', 'CHANNEL[V]', '求索纪录', '求索科学', '求索生活',
                   '求索动物', '星空少儿', '星空科幻', '星空体育', '星空赛车频道', '优漫卡通', '乐芒卡通', '戏曲频道', '军情评论',
                 '鍐涙梾鍓у満', '涔愭父', '鐢熸椿鏃跺皻', '閮藉競鍓у満', '娆㈢瑧鍓у満', '娓告垙椋庝簯', '閲戣壊瀛﹀爞', '娉曟不澶╁湴', '鍝掑暤璧涗簨'],
    "浣撹偛棰戦亾": ['澶╁厓鍥存', '榄呭姏瓒崇悆', '浜旀槦浣撹偛', '鍔茬垎浣撹偛', '瓒呯骇浣撹偛'],
    "鍓у満棰戦亾": ['鍙よ鍓у満', '瀹跺涵鍓у満', '鎯婃倸鎮枒', '鏄庢槦澶х墖', '娆箰鍓у満', '娴峰鍓у満', '娼杈ｅ﹩',
                 '综艺剧场', '超级电视电影', '超级综艺', '财经综艺', '时尚世界', '商业理财', '未来科技',
                 '绮惧搧浣撹偛', '绮惧搧澶у墽', '绮惧搧绾綍', '绮惧搧钀屽疇', '鎬′即鍋ュ悍'],
}

# 棰戦亾鏄犲皠锛堝埆鍚?-> 瑙勮寖鍚嶏級
CHANNEL_MAPPING = {
    # 4K棰戦亾
    "CCTV4K": ["CCTV 4K", "CCTV-4K", "CCTV4K"],
    "CCTV8K": ["CCTV 8K", "CCTV-8K", "CCTV8K"],
    "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 奥林匹克 4K", "CCTV16奥林匹克 4K"],
    "北京卫视4K": ["北京卫视 4K", "北京卫视-4K"],
    "鍖椾含IPTV4K": ["鍖椾含IPTV 4K", "鍖椾含IPTV-4K"],
    "婀栧崡鍗4K": ["婀栧崡鍗 4K", "婀栧崡鍗-4K"],
    "灞变笢鍗4K": ["灞变笢鍗 4K", "灞变笢鍗-4K"],
    "骞夸笢鍗4K": ["骞夸笢鍗 4K", "骞夸笢鍗-4K"],
    "鍥涘窛鍗4K": ["鍥涘窛鍗 4K", "鍥涘窛鍗-4K"],
    "娴欐睙鍗4K": ["娴欐睙鍗 4K", "娴欐睙鍗-4K"],
    "姹熻嫃鍗4K": ["姹熻嫃鍗 4K", "姹熻嫃鍗-4K"],
    "涓滄柟鍗4K": ["涓滄柟鍗 4K", "涓滄柟鍗-4K"],
    "娣卞湷鍗4K": ["娣卞湷鍗 4K", "娣卞湷鍗-4K"],
    "娌冲寳鍗4K": ["娌冲寳鍗 4K", "娌冲寳鍗-4K"],
    "宄ㄧ湁鐢靛奖4K": ["宄ㄧ湁鐢靛奖 4K", "宄ㄧ湁鐢靛奖-4K"],
    "姹傜储4K": ["姹傜储 4K", "姹傜储-4K"],
    "鍜鐣?K": ["鍜鐣?4K", "鍜鐣?4K"],
    "娆㈢瑧鍓у満4K": ["娆㈢瑧鍓у満 4K", "娆㈢瑧鍓у満-4K"],
    "鑻忓窞4K": ["鑻忓窞 4K", "鑻忓窞-4K"],
    "鑷宠嚮瑙嗙晫4K": ["鑷宠嚮瑙嗙晫 4K", "鑷宠嚮瑙嗙晫-4K"],
    "鍗楀浗閮藉競4K": ["鍗楀浗閮藉競 4K", "鍗楀浗閮藉競-4K"],
    "缈＄繝鍙?K": ["缈＄繝鍙?4K", "缈＄繝鍙?4K"],
    "鐧句簨閫氱數褰?K": ["鐧句簨閫氱數褰?4K", "鐧句簨閫氱數褰?4K"],
    "鐧句簨閫氬皯鍎?K": ["鐧句簨閫氬皯鍎?4K", "鐧句簨閫氬皯鍎?4K"],
    "鐧句簨閫氱邯瀹?K": ["鐧句簨閫氱邯瀹?4K", "鐧句簨閫氱邯瀹?4K"],
    "鍗庢暟鐖变笂4K": ["鍗庢暟鐖变笂 4K", "鐖变笂 4K", "鐖变笂4K",  "鐖变笂-4K", "鍗庢暟鐖变笂-4K"],
    
    # 澶棰戦亾
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1缁煎悎", "CCTV-1 缁煎悎"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 璐㈢粡", "CCTV-2 璐㈢粡"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 缁艰壓", "CCTV-3 缁艰壓"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4a", "CCTV4A", "CCTV4 涓枃鍥介檯", "CCTV-4 涓枃鍥介檯"],
    "CCTV4娆ф床": ["CCTV-4娆ф床", "CCTV-4娆ф床 HD", "CCTV-4 娆ф床", "CCTV4o", "CCTV4O", "CCTV-4 涓枃娆ф床", "CCTV4涓枃娆ф床"],
    "CCTV4缇庢床": ["CCTV-4缇庢床", "CCTV-4缇庢床 HD", "CCTV-4 缇庢床", "CCTV4m", "CCTV4M", "CCTV-4 涓枃缇庢床", "CCTV4涓枃缇庢床"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 浣撹偛", "CCTV-5 浣撹偛"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ 浣撹偛璧涗簨", "CCTV-5+ 浣撹偛璧涗簨"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 鐢靛奖", "CCTV-6 鐢靛奖"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 鍥介槻鍐涗簨", "CCTV-7 鍥介槻鍐涗簨"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 绾綍", "CCTV-9 绾綍"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 绉戞暀", "CCTV-10 绉戞暀"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 鎴忔洸", "CCTV-11 鎴忔洸"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 绀句細涓庢硶", "CCTV-12 绀句細涓庢硶"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 鏂伴椈", "CCTV-13 鏂伴椈"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 灏戝効", "CCTV-14 灏戝効"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 闊充箰", "CCTV-15 闊充箰"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 濂ユ灄鍖瑰厠", "CCTV16 濂ユ灄鍖瑰厠"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 鍐滀笟鍐滄潙", "CCTV-17 鍐滀笟鍐滄潙"],
    "鍏靛櫒绉戞妧": ["CCTV-鍏靛櫒绉戞妧", "CCTV鍏靛櫒绉戞妧"],
    "椋庝簯闊充箰": ["CCTV-椋庝簯闊充箰", "CCTV椋庝簯闊充箰"],
    "椋庝簯瓒崇悆": ["CCTV-椋庝簯瓒崇悆", "CCTV椋庝簯瓒崇悆"],
    "椋庝簯鍓у満": ["CCTV-椋庝簯鍓у満", "CCTV椋庝簯鍓у満"],
    "鎬€鏃у墽鍦?: ["CCTV-鎬€鏃у墽鍦?, "CCTV鎬€鏃у墽鍦?],
    "绗竴鍓у満": ["CCTV-绗竴鍓у満", "CCTV绗竴鍓у満"],
    "濂虫€ф椂灏?: ["CCTV-濂虫€ф椂灏?, "CCTV濂虫€ф椂灏?],
    "涓栫晫鍦扮悊": ["CCTV-涓栫晫鍦扮悊", "CCTV涓栫晫鍦扮悊"],
    "澶鍙扮悆": ["CCTV-澶鍙扮悆", "CCTV澶鍙扮悆"],
    "楂樺皵澶綉鐞?: ["CCTV-楂樺皵澶綉鐞?, "CCTV楂樺皵澶綉鐞?],
    "澶鏂囧寲绮惧搧": ["CCTV-澶鏂囧寲绮惧搧", "CCTV澶鏂囧寲绮惧搧"],
    "鍗敓鍋ュ悍": ["CCTV-鍗敓鍋ュ悍", "CCTV鍗敓鍋ュ悍"],
    "鐢佃鎸囧崡": ["CCTV-鐢佃鎸囧崡", "CCTV鐢佃鎸囧崡"],
    
    # 鍗棰戦亾
    "灞变笢鍗": ["灞变笢鍗 HD", "灞变笢鍙?, "灞变笢鍗楂樻竻"],
    "娴欐睙鍗": ["娴欐睙鍗 HD", "娴欐睙鍙?, "娴欐睙鍗楂樻竻"],
    "姹熻嫃鍗": ["姹熻嫃鍗 HD", "姹熻嫃鍙?, "姹熻嫃鍗楂樻竻"],
    "涓滄柟鍗": ["涓滄柟鍗 HD", "涓滄柟鍙?, "涓婃捣涓滄柟鍗", "涓滄柟鍗楂樻竻"],
    "娣卞湷鍗": ["娣卞湷鍗 HD", "娣卞湷鍙?, "娣卞湷鍗楂樻竻"],
    "鍖椾含鍗": ["鍖椾含鍗 HD", "鍖椾含鍙?, "鍖椾含鍗楂樻竻"],
    "骞夸笢鍗": ["骞夸笢鍗 HD", "骞夸笢鍙?, "骞夸笢鍗楂樻竻"],
    "骞胯タ鍗": ["骞胯タ鍗 HD", "骞胯タ鍙?, "骞胯タ鍗楂樻竻"],
    "涓滃崡鍗": ["涓滃崡鍗 HD", "涓滃崡鍙?, "绂忓缓涓滃崡鍗", "涓滃崡鍗楂樻竻"],
    "娴峰崡鍗": ["娴峰崡鍗 HD", "娴峰崡鍙?, "娴峰崡鍗楂樻竻"],
    "娌冲寳鍗": ["娌冲寳鍗 HD", "娌冲寳鍙?, "娌冲寳鍗楂樻竻"],
    "娌冲崡鍗": ["娌冲崡鍗 HD", "娌冲崡鍙?, "娌冲崡鍗楂樻竻"],
    "婀栧寳鍗": ["婀栧寳鍗 HD", "婀栧寳鍙?, "婀栧寳鍗楂樻竻"],
    "姹熻タ鍗": ["姹熻タ鍗 HD", "姹熻タ鍙?, "姹熻タ鍗楂樻竻"],
    "鍥涘窛鍗": ["鍥涘窛鍗 HD", "鍥涘窛鍙?, "鍥涘窛鍗楂樻竻"],
    "閲嶅簡鍗": ["閲嶅簡鍗 HD", "閲嶅簡鍙?, "閲嶅簡鍗楂樻竻"],
    "璐靛窞鍗": ["璐靛窞鍗 HD", "璐靛窞鍙?, "璐靛窞鍗楂樻竻"],
    "浜戝崡鍗": ["浜戝崡鍗 HD", "浜戝崡鍙?, "浜戝崡鍗楂樻竻"],
    "澶╂触鍗": ["澶╂触鍗 HD", "澶╂触鍙?, "澶╂触鍗楂樻竻"],
    "瀹夊窘鍗": ["瀹夊窘鍗 HD", "瀹夊窘鍙?, "瀹夊窘鍗楂樻竻"],
    "婀栧崡鍗": ["婀栧崡鍗 HD", "婀栧崡鍙?, "婀栧崡鍗楂樻竻"],
    "杈藉畞鍗": ["杈藉畞鍗 HD", "杈藉畞鍙?, "杈藉畞鍗楂樻竻"],
    "榛戦緳姹熷崼瑙?: ["榛戦緳姹熷崼瑙?HD", "榛戦緳姹熷彴", "榛戦緳姹熷崼瑙嗛珮娓?],
    "鍚夋灄鍗": ["鍚夋灄鍗 HD", "鍚夋灄鍙?, "鍚夋灄鍗楂樻竻"],
    "鍐呰挋鍙ゅ崼瑙?: ["鍐呰挋鍙ゅ崼瑙?HD", "鍐呰挋鍙ゅ彴", "鍐呰挋鍙ゅ崼瑙嗛珮娓?],
    "瀹佸鍗": ["瀹佸鍗 HD", "瀹佸鍙?, "瀹佸鍗楂樻竻"],
    "灞辫タ鍗": ["灞辫タ鍗 HD", "灞辫タ鍙?, "灞辫タ鍗楂樻竻"],
    "闄曡タ鍗": ["闄曡タ鍗 HD", "闄曡タ鍙?, "闄曡タ鍗楂樻竻"],
    "鐢樿們鍗": ["鐢樿們鍗 HD", "鐢樿們鍙?, "鐢樿們鍗楂樻竻"],
    "闈掓捣鍗": ["闈掓捣鍗 HD", "闈掓捣鍙?, "闈掓捣鍗楂樻竻"],
    "鏂扮枂鍗": ["鏂扮枂鍗 HD", "鏂扮枂鍙?, "鏂扮枂鍗楂樻竻"],
    "瑗胯棌鍗": ["瑗胯棌鍗 HD", "瑗胯棌鍙?, "瑗胯棌鍗楂樻竻"],
    "涓夋矙鍗": ["涓夋矙鍗 HD", "涓夋矙鍙?, "涓夋矙鍗楂樻竻"],
    "鍘﹂棬鍗": ["鍘﹂棬鍗 HD", "鍘﹂棬鍙?, "鍘﹂棬鍗楂樻竻"],
    "鍏靛洟鍗": ["鍏靛洟鍗 HD", "鍏靛洟鍙?, "鍏靛洟鍗楂樻竻"],
    "寤惰竟鍗": ["寤惰竟鍗 HD", "寤惰竟鍙?, "寤惰竟鍗楂樻竻"],
    "瀹夊鍗": ["瀹夊鍗 HD", "瀹夊鍙?, "瀹夊鍗楂樻竻"],
    "搴峰反鍗": ["搴峰反鍗 HD", "搴峰反鍙?, "搴峰反鍗楂樻竻"],
    "鍐滄灄鍗": ["鍐滄灄鍗 HD", "鍐滄灄鍙?, "鍐滄灄鍗楂樻竻"],
    "灞变笢鏁欒偛": ["灞变笢鏁欒偛鍙?, "灞变笢鏁欒偛鍗"],
    "CETV1": ["CETV-1", "涓浗鏁欒偛1", "涓浗鏁欒偛鍙?"],
    "CETV2": ["CETV-2", "涓浗鏁欒偛2", "涓浗鏁欒偛鍙?"],
    "CETV3": ["CETV-3", "涓浗鏁欒偛3", "涓浗鏁欒偛鍙?"],
    "CETV4": ["CETV-4", "涓浗鏁欒偛4", "涓浗鏁欒偛鍙?"],
    "鏃╂湡鏁欒偛": ["CETV-鏃╂湡鏁欒偛", "涓浗鏁欒偛鍙?鏃╂湡鏁欒偛"],
}

# 榛樿鐩存挱婧怳RL
# 浠庣粺涓€鎾斁婧愭枃浠跺鍏?
from unified_sources import UNIFIED_SOURCES
default_sources = UNIFIED_SOURCES

# 鏈湴鐩存挱婧愭枃浠?
default_local_sources = [
    "ipzyauto.txt",
]

# 鐢ㄦ埛鑷畾涔夌洿鎾簮URL锛堝彲鍦ㄦ湰鍦版坊鍔狅級
user_sources = []

# 鑾峰彇URL鍒楄〃
def get_urls_from_file(file_path):
    """浠庢枃浠朵腑璇诲彇URL鍒楄〃"""
    urls = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"璇诲彇URL鏂囦欢鏃跺嚭閿? {e}")
    return urls

# 妫€鏌RL鏄惁鏈夋晥
def check_url(url, timeout=5):
    """妫€鏌RL鏄惁鍙闂?""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False

# 鏍煎紡鍖栨椂闂撮棿闅?
def format_interval(seconds):
    """鏍煎紡鍖栨椂闂撮棿闅?""
    if seconds < 60:
        return f"{seconds:.2f}绉?
    elif seconds < 3600:
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes)}鍒唟int(seconds)}绉?
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}鏃秢int(minutes)}鍒唟int(seconds)}绉?

# 鑾峰彇IP鍦板潃
def get_ip_address():
    """鑾峰彇鏈湴IP鍦板潃"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 妫€鏌Pv6鏀寔
def check_ipv6_support():
    """妫€鏌ョ郴缁熸槸鍚︽敮鎸両Pv6"""
    try:
        import socket
        socket.inet_pton(socket.AF_INET6, '::1')
        return True
    except:
        return False

# 浠嶮3U鏂囦欢涓彁鍙栭閬撲俊鎭?
def extract_channels_from_m3u(content):
    """浠嶮3U鍐呭涓彁鍙栭閬撲俊鎭?""
    channels = defaultdict(list)
    pattern = r'#EXTINF:.*?tvg-name="([^"]*)".*?(?:group-title="([^"]*)")?,([^\n]+)\n(http[^\n]+)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        tvg_name = match[0].strip() if match[0] else match[2].strip()
        channel_name = match[2].strip()
        url = match[3].strip()
        
        # 瑙勮寖鍖栭閬撳悕绉?
        normalized_name = normalize_channel_name(channel_name)
        if normalized_name:
            # 鑾峰彇棰戦亾鍒嗙被
            category = get_channel_category(normalized_name)
            channels[category].append((normalized_name, url))
        else:
            # 鏈鑼冨寲鐨勯閬撴斁鍦ㄥ叾浠栭閬?
            channels["鍏朵粬棰戦亾"].append((channel_name, url))
    
    return channels

# 鑾峰彇棰戦亾鍒嗙被
def get_channel_category(channel_name):
    """鑾峰彇棰戦亾鎵€灞炵殑鍒嗙被"""
    for category, channels in CHANNEL_CATEGORIES.items():
        if channel_name in channels:
            return category
    return "鍏朵粬棰戦亾"

# 瑙勮寖鍖栭閬撳悕绉?
def normalize_channel_name(name):
    """灏嗛閬撳悕绉拌鑼冨寲涓烘爣鍑嗗悕绉?""
    name = name.strip()
    # 妫€鏌ユ槸鍚︽槸鏍囧噯鍚嶇О
    for standard_name in CHANNEL_MAPPING:
        if name == standard_name:
            return standard_name
    # 妫€鏌ユ槸鍚︽槸鍒悕
    for standard_name, aliases in CHANNEL_MAPPING.items():
        if name in aliases:
            return standard_name
    return None

# 浠嶶RL鑾峰彇M3U鍐呭
def fetch_m3u_content(url):
    """浠嶶RL鑾峰彇M3U鍐呭"""
    try:
        print(f"姝ｅ湪鑾峰彇: {url}")
        # 娣诲姞verify=False鍙傛暟鏉ヨ烦杩嘢SL璇佷功楠岃瘉
        response = requests.get(url, timeout=30, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"鑾峰彇 {url} 鏃跺嚭閿? {e}")
        return None

# 浠庢湰鍦版枃浠惰幏鍙朚3U鍐呭
def fetch_local_m3u_content(file_path):
    """浠庢湰鍦版枃浠惰幏鍙朚3U鍐呭"""
    try:
        print(f"姝ｅ湪璇诲彇鏈湴鏂囦欢: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"璇诲彇鏈湴鏂囦欢 {file_path} 鏃跺嚭閿? {e}")
        return None

# 鐢熸垚M3U鏂囦欢
def generate_m3u_file(channels, output_path):
    """鐢熸垚M3U鏂囦欢"""
    print(f"姝ｅ湪鐢熸垚 {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 鍐欏叆鏂囦欢澶?
        f.write("#EXTM3U x-tvg-url=\"https://kakaxi-1.github.io/IPTV/epg.xml\"\n")
        
        # 鎸塁HANNEL_CATEGORIES涓畾涔夌殑椤哄簭鍐欏叆鍒嗙被
        for category in CHANNEL_CATEGORIES:
            if category in channels:
                for channel_name, url in channels[category]:
                    # 鍐欏叆棰戦亾淇℃伅
                    f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"{category}\",{channel_name}\n")
                    f.write(f"{url}\n")
        
        # 鏈€鍚庡啓鍏ュ叾浠栭閬?
        if "鍏朵粬棰戦亾" in channels:
            for channel_name, url in channels["鍏朵粬棰戦亾"]:
                # 鍐欏叆棰戦亾淇℃伅
                f.write(f"#EXTINF:-1 tvg-name=\"{channel_name}\" group-title=\"鍏朵粬棰戦亾\",{channel_name}\n")
                f.write(f"{url}\n")
    
    print(f"鉁?鎴愬姛鐢熸垚 {output_path}")
    return True

# 鐢熸垚TXT鏂囦欢
def generate_txt_file(channels, output_path):
    """鐢熸垚TXT鏂囦欢"""
    print(f"姝ｅ湪鐢熸垚 {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 鍐欏叆鏂囦欢澶存敞閲?
        f.write(f"# IPTV鐩存挱婧愬垪琛╘n")
        f.write(f"# 鐢熸垚鏃堕棿: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# 鏍煎紡: 棰戦亾鍚嶇О,鎾斁URL\n")
        f.write("# 鎸夊垎缁勬帓鍒梊n")
        f.write("\n")
        
        # 鍐欏叆棰戦亾鍒嗙被璇存槑
        f.write("# 棰戦亾鍒嗙被: 4K棰戦亾,澶棰戦亾,鍗棰戦亾,鍖椾含涓撳睘棰戦亾,灞变笢涓撳睘棰戦亾,娓境棰戦亾,鐢靛奖棰戦亾,鍎跨棰戦亾,iHOT棰戦亾,缁煎悎棰戦亾,浣撹偛棰戦亾,鍓у満棰戦亾,鍏朵粬棰戦亾\n")
        f.write("\n")
        
        # 鎸塁HANNEL_CATEGORIES涓畾涔夌殑椤哄簭鍐欏叆鍒嗙被
        for category in CHANNEL_CATEGORIES:
            if category in channels and channels[category]:
                # 鍐欏叆鍒嗙粍鏍囬锛屾坊鍔?#genre#鍚庣紑
                f.write(f"#{category}#,genre#\n")
                
                # 鍐欏叆璇ュ垎缁勪笅鐨勬墍鏈夐閬?
                for channel_name, url in channels[category]:
                    f.write(f"{channel_name},{url}\n")
                
                # 鍒嗙粍涔嬮棿娣诲姞绌鸿
                f.write("\n")
        
        # 鏈€鍚庡啓鍏ュ叾浠栭閬?
        if "鍏朵粬棰戦亾" in channels and channels["鍏朵粬棰戦亾"]:
            # 鍐欏叆鍒嗙粍鏍囬锛屾坊鍔?#genre#鍚庣紑
            f.write("#鍏朵粬棰戦亾#,#genre#\n")
            
            # 鍐欏叆璇ュ垎缁勪笅鐨勬墍鏈夐閬?
            for channel_name, url in channels["鍏朵粬棰戦亾"]:
                f.write(f"{channel_name},{url}\n")
            
            # 鍒嗙粍涔嬮棿娣诲姞绌鸿
            f.write("\n")
    
    print(f"鉁?鎴愬姛鐢熸垚 {output_path}")
    return True

# 浠庢湰鍦癟XT鏂囦欢鎻愬彇棰戦亾淇℃伅
def extract_channels_from_txt(file_path):
    """浠庢湰鍦癟XT鏂囦欢鎻愬彇棰戦亾淇℃伅"""
    channels = defaultdict(list)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 鍙烦杩囨牸寮忎笉姝ｇ‘鐨勮锛堜笉浠?寮€澶翠絾鍖呭惈,#genre#鐨勮锛?
                # 姝ｇ‘鏍煎紡鐨勫垎缁勬爣棰樿锛堜互#寮€澶翠笖鍖呭惈,#genre#锛夊凡缁忓湪涓婇潰鐨刲ine.startswith('#')鏉′欢涓璺宠繃浜?
                if not line.startswith('#') and (line.endswith(',#genre#') or line.endswith(',genre#')):
                    continue
                
                # 瑙ｆ瀽棰戦亾淇℃伅锛堟牸寮忥細棰戦亾鍚嶇О,URL锛?
                if ',' in line:
                    channel_name, url = line.split(',', 1)
                    channel_name = channel_name.strip()
                    url = url.strip()
                    
                    # 璺宠繃鏃犳晥鐨刄RL
                    if not url.startswith(('http://', 'https://')):
                        continue
                    
                    # 瑙勮寖鍖栭閬撳悕绉?
                    normalized_name = normalize_channel_name(channel_name)
                    if normalized_name:
                        # 鑾峰彇棰戦亾鍒嗙被
                        category = get_channel_category(normalized_name)
                        channels[category].append((normalized_name, url))
                    else:
                        # 鏈鑼冨寲鐨勯閬撴斁鍦ㄥ叾浠栭閬?
                        channels["鍏朵粬棰戦亾"].append((channel_name, url))
    except Exception as e:
        print(f"瑙ｆ瀽鏈湴鏂囦欢 {file_path} 鏃跺嚭閿? {e}")
    
    return channels

# 鍚堝苟鐩存挱婧?
def merge_sources(sources, local_files):
    """鍚堝苟澶氫釜鐩存挱婧?""
    all_channels = defaultdict(list)
    seen = set()
    
    # 澶勭悊杩滅▼鐩存挱婧?
    for source_url in sources:
        content = fetch_m3u_content(source_url)
        if content:
            channels = extract_channels_from_m3u(content)
            for group_title, channel_list in channels.items():
                for channel_name, url in channel_list:
                    # 鍘婚噸
                    if (channel_name, url) not in seen:
                        all_channels[group_title].append((channel_name, url))
                        seen.add((channel_name, url))
    
    # 澶勭悊鏈湴鐩存挱婧愭枃浠?
    for file_path in local_files:
        if os.path.exists(file_path):
            local_channels = extract_channels_from_txt(file_path)
            for group_title, channel_list in local_channels.items():
                for channel_name, url in channel_list:
                    # 鍘婚噸
                    if (channel_name, url) not in seen:
                        all_channels[group_title].append((channel_name, url))
                        seen.add((channel_name, url))
    
    return all_channels


# 蹇界暐requests鐨凷SL璀﹀憡
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_iptv_sources():
    """鏇存柊IPTV鐩存挱婧?""
    logger.info("馃殌 IPTV鐩存挱婧愯嚜鍔ㄧ敓鎴愬伐鍏?)
    logger.info(f"馃搮 杩愯鏃堕棿: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    # 鍚堝苟鎵€鏈夌洿鎾簮
    all_sources = default_sources + user_sources
    logger.info(f"馃摗 姝ｅ湪鑾峰彇{len(all_sources)}涓繙绋嬬洿鎾簮...")
    logger.info(f"馃捇 姝ｅ湪璇诲彇{len(default_local_sources)}涓湰鍦扮洿鎾簮鏂囦欢...")
    
    start_time = time.time()
    all_channels = merge_sources(all_sources, default_local_sources)
    
    # 缁熻棰戦亾鏁伴噺
    total_channels = sum(len(channel_list) for channel_list in all_channels.values())
    total_groups = len(all_channels)
    
    logger.info("=" * 50)
    logger.info(f"馃搳 缁熻淇℃伅:")
    logger.info(f"馃摗 鐩存挱婧愭暟閲? {len(all_sources)}")
    logger.info(f"馃摵 棰戦亾缁勬暟: {total_groups}")
    logger.info(f"馃摎 鎬婚閬撴暟: {total_channels}")
    logger.info(f"鈴憋笍  鑰楁椂: {format_interval(time.time() - start_time)}")
    logger.info("=" * 50)
    
    # 鏄剧ず棰戦亾缁勪俊鎭?
    logger.info("馃搵 棰戦亾缁勮鎯?")
    for group_title, channel_list in all_channels.items():
        logger.info(f"   {group_title}: {len(channel_list)}涓閬?)
    
    # 鐢熸垚M3U鏂囦欢
    output_file_m3u = "jieguo.m3u"  # 灏嗚緭鍑烘枃浠舵敼涓簀ieguo.m3u
    # 鐢熸垚TXT鏂囦欢
    output_file_txt = "jieguo.txt"  # 鏂板TXT鏍煎紡杈撳嚭鏂囦欢
    
    if generate_m3u_file(all_channels, output_file_m3u) and generate_txt_file(all_channels, output_file_txt):
        logger.info(f"馃帀 浠诲姟瀹屾垚锛?)
        return True
    else:
        logger.error("馃挜 鐢熸垚鏂囦欢澶辫触锛?)
        return False


def main():
    """涓诲嚱鏁?""
    import sys
    
    # 妫€鏌ュ懡浠よ鍙傛暟
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        # 鎵嬪姩鏇存柊妯″紡
        update_iptv_sources()
    else:
        # 鏄剧ず甯姪淇℃伅
        print("=" * 60)
        print("      IPTV鐩存挱婧愯嚜鍔ㄧ敓鎴愬伐鍏?)
        print("=" * 60)
        print("鍔熻兘锛?)
        print("  1. 浠庡涓潵婧愯幏鍙朓PTV鐩存挱婧?)
        print("  2. 鐢熸垚M3U鍜孴XT鏍煎紡鐨勭洿鎾簮鏂囦欢")
        print("  3. 鏀寔鎵嬪姩鏇存柊鍜岄€氳繃GitHub Actions宸ヤ綔娴佸畾鏃舵洿鏂?)
        print("")
        print("浣跨敤鏂规硶锛?)
        print("  python IP-TV.py --update     # 绔嬪嵆鎵嬪姩鏇存柊鐩存挱婧?)
        print("  閫氳繃GitHub Actions宸ヤ綔娴佽嚜鍔ㄦ洿鏂?)
        print("")
        print("杈撳嚭鏂囦欢锛?)
        print("  - jieguo.m3u   # M3U鏍煎紡鐨勭洿鎾簮鏂囦欢")
        print("  - jieguo.txt   # TXT鏍煎紡鐨勭洿鎾簮鏂囦欢")
        print("  - iptv_update.log  # 鏇存柊鏃ュ織鏂囦欢")
        print("=" * 60)


if __name__ == "__main__":
    main()
