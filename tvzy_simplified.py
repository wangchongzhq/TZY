# -*- coding: utf-8 -*-
import re
import requests
import concurrent.futures
import argparse
import time

# 閰嶇疆鍙傛暟
MAX_WORKERS = 10
TIMEOUT = 10
MIN_LINES_PER_CHANNEL = 10
MAX_LINES_PER_CHANNEL = 90
# 榛樿杈撳嚭鏂囦欢鍚?
OUTPUT_FILE = 'tzydauto.txt'
# 鍏佽鐨勭洿鎾簮鍩熷悕鍒楄〃
ALLOWED_DOMAINS = ['http://example.com/']

# 璇锋眰澶?
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 瀵煎叆缁熶竴鏁版嵁婧愬垪琛?
from unified_sources import UNIFIED_SOURCES

# 鏁版嵁婧愬垪琛?- 浣跨敤缁熶竴鐨勬暟鎹簮
GITHUB_SOURCES = UNIFIED_SOURCES

# 棰戦亾鍒嗙被 - 娉ㄦ剰锛氶『搴忓繀椤讳弗鏍兼寜鐓ц姹傜殑椤哄簭
CHANNEL_CATEGORIES = {
    "4K棰戦亾": ['CCTV4K', 'CCTV16 4K', '鍖椾含鍗4K', '鍖椾含IPTV4K', '婀栧崡鍗4K', '灞变笢鍗4K', '骞夸笢鍗4K', '鍥涘窛鍗4K',
                '娴欐睙鍗4K', '姹熻嫃鍗4K', '涓滄柟鍗4K', '娣卞湷鍗4K', '娌冲寳鍗4K', '宄ㄧ湁鐢靛奖4K', '姹傜储4K', '鍜鐣?K', '娆㈢瑧鍓у満4K',
                '鑻忓窞4K', '鑷宠嚮瑙嗙晫4K', '鍗楀浗閮藉競4K', '缈＄繝鍙?K', '鐧句簨閫氱數褰?K', '鐧句簨閫氬皯鍎?K', '鐧句簨閫氱邯瀹?K', '鍗庢暟鐖变笂4K'],

    "澶棰戦亾": ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV4娆ф床', 'CCTV4缇庢床', 'CCTV5', 'CCTV5+', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9',
                'CCTV10', 'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', '鍏靛櫒绉戞妧', '椋庝簯闊充箰', '椋庝簯瓒崇悆',
                '凤凰电影', '寰宇影院', '第一剧场', '靓妆时尚', '世界地理', '卫视体育', '气象影视网络', '卫视文化精品', '北京天文科普',
                '鍗敓鍋ュ悍', '鐢佃鎸囧崡'],
    "鍗棰戦亾": ['灞变笢鍗', '娴欐睙鍗', '姹熻嫃鍗', '涓滄柟鍗', '娣卞湷鍗', '鍖椾含鍗', '骞夸笢鍗', '骞胯タ鍗', '涓滃崡鍗', '娴峰崡鍗',
                '娌冲寳鍗', '娌冲崡鍗', '婀栧寳鍗', '姹熻タ鍗', '鍥涘窛鍗', '閲嶅簡鍗', '璐靛窞鍗', '浜戝崡鍗', '澶╂触鍗', '瀹夊窘鍗',
                '云南卫视', '甘肃卫视', '新疆卫视', '青海卫视', '内蒙古卫视', '宁夏卫视', '西藏卫视', '陕西卫视', '四川卫视',
                '闈掓捣鍗', '鏂扮枂鍗', '瑗胯棌鍗', '涓夋矙鍗', '鍘﹂棬鍗', '鍏靛洟鍗', '寤惰竟鍗', '瀹夊鍗', '搴峰反鍗', '鍐滄灄鍗', '灞变笢鏁欒偛',
                'CETV1', 'CETV2', 'CETV3', 'CETV4', '鏃╂湡鏁欒偛'],

    "鍖椾含涓撳睘棰戦亾": ['鍖椾含鍗', '鍖椾含璐㈢粡', '鍖椾含绾疄', '鍖椾含鐢熸椿', '鍖椾含浣撹偛浼戦棽', '鍖椾含鍥介檯', '鍖椾含鏂囪壓', '鍖椾含鏂伴椈',
                '鍖椾含娣樼數褰?, '鍖椾含娣樺墽鍦?, '鍖椾含娣?K', '鍖椾含娣樺ū涔?, '鍖椾含娣楤ABY', '鍖椾含钀屽疇TV'],

    "灞变笢涓撳睘棰戦亾": ['灞变笢鍗', '灞变笢榻愰瞾', '灞变笢缁艰壓', '灞变笢灏戝効', '灞变笢鐢熸椿',
                '灞变笢鏂伴椈', '灞变笢鍥介檯', '灞变笢浣撹偛', '灞变笢鏂囨梾', '灞变笢鍐滅'],

    "娓境棰戦亾": ['鍑ゅ嚢涓枃', '鍑ゅ嚢璧勮', '鍑ゅ嚢棣欐腐', '鍑ゅ嚢鐢靛奖'],

    "鐢靛奖棰戦亾": ['CHC鍔ㄤ綔鐢靛奖', 'CHC瀹跺涵褰遍櫌', 'CHC褰辫糠鐢靛奖', '娣樼數褰?,
                '娣樼簿褰?, '娣樺墽鍦?, '鏄熺┖鍗', '榛戣帗鐢靛奖', '涓滃寳鐑墽',
                '涓浗鍔熷か', '鍔ㄤ綔鐢靛奖', '瓒呯骇鐢靛奖'],
    "鍎跨棰戦亾": ['鍔ㄦ极绉€鍦?, '鍝掑暤鐢电珵', '榛戣帗鍔ㄧ敾', '鍗￠叿灏戝効',
                '閲戦拱鍗￠€?, '浼樻极鍗￠€?, '鍝堝搱鐐姩', '鍢変匠鍗￠€?],
    "iHOT棰戦亾": ['iHOT鐖卞枩鍓?, 'iHOT鐖辩骞?, 'iHOT鐖遍櫌绾?, 'iHOT鐖辨偓鐤?, 'iHOT鐖卞巻鍙?, 'iHOT鐖辫皪鎴?, 'iHOT鐖辨梾琛?, 'iHOT鐖卞辜鏁?,
                'iHOT鐖辩帺鍏?, 'iHOT鐖变綋鑲?, 'iHOT鐖辫禌杞?, 'iHOT鐖辨氮婕?, 'iHOT鐖卞璋?, 'iHOT鐖辩瀛?, 'iHOT鐖卞姩婕?],
    "缁煎悎棰戦亾": ['閲嶆俯缁忓吀', 'CHANNEL[V]', '姹傜储绾綍', '姹傜储绉戝', '姹傜储鐢熸椿',
                '姹傜储鍔ㄧ墿', '鐫涘僵闈掑皯', '鐫涘僵绔炴妧', '鐫涘僵绡悆', '鐫涘僵骞垮満鑸?, '閲戦拱绾疄', '蹇箰鍨傞挀', '鑼堕閬?, '鍐涗簨璇勮',
                '鍐涙梾鍓у満', '涔愭父', '鐢熸椿鏃跺皻', '閮藉競鍓у満', '娆㈢瑧鍓у満', '娓告垙椋庝簯', '閲戣壊瀛﹀爞', '娉曟不澶╁湴', '鍝掑暤璧涗簨'],
    "鍓у満棰戦亾": ['鍙よ鍓у満', '瀹跺涵鍓у満', '鎯婃倸鎮枒', '鏄庢槦澶х墖', '娆箰鍓у満', '娴峰鍓у満', '娼杈ｅ﹩',
                '鐖辨儏鍠滃墽', '瓒呯骇鐢佃鍓?, '瓒呯骇缁艰壓', '閲戠墝缁艰壓', '姝︽悘涓栫晫', '鍐滀笟鑷村瘜', '鐐垶鏈潵',
                '绮惧搧浣撹偛', '绮惧搧澶у墽', '绮惧搧绾綍', '绮惧搧钀屽疇', '鎬′即鍋ュ悍'],
    "浣撹偛棰戦亾": ['澶╁厓鍥存', '榄呭姏瓒崇悆', '浜旀槦浣撹偛', '鍔茬垎浣撹偛', '瓒呯骇浣撹偛'],
    "闊充箰棰戦亾": ['闊充箰棰戦亾', '椋庝簯闊充箰', 'CCTV闊充箰', 'CHANNEL[V]', '闊充箰Tai', '闊充箰鍙?, 'MTV', 'MTV涓枃', '鍗庤闊充箰', '娴佽闊充箰', '鍙ゅ吀闊充箰']
}

# 棰戦亾鏄犲皠瀛楀吀
CHANNEL_MAPPING = {}

# 濉厖棰戦亾鏄犲皠瀛楀吀
for category, channels in CHANNEL_CATEGORIES.items():
    for channel in channels:
        CHANNEL_MAPPING[channel] = [channel]

additional_mappings = {
    "CCTV4K": ["CCTV 4K", "CCTV-4K"],
    "CCTV16 4K": ["CCTV16 4K", "CCTV16-4K", "CCTV16 濂ユ灄鍖瑰厠 4K", "CCTV16濂ユ灄鍖瑰厠 4K"],
    "鍖椾含鍗4K": ["鍖椾含鍗 4K", "鍖椾含鍗-4K"],
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
    "鍗庢暟鐖变笂4K": ["鍗庢暟鐖变笂 4K", "鐖变笂 4K", "鐖变笂4K", "鐖变笂-4K", "鍗庢暟鐖变笂-4K"],
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
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 鐢佃鍓?, "CCTV-8 鐢佃鍓?],
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
    "楂樺皵澶綉鐞?: ["CCTV-楂樺皵澶綉鐞?, "CCTV楂樺皵澶綉鐞?, "CCTV澶楂樼綉", "CCTV-澶楂樼綉", "澶楂樼綉"],
    "澶鏂囧寲绮惧搧": ["CCTV-澶鏂囧寲绮惧搧", "CCTV澶鏂囧寲绮惧搧", "CCTV鏂囧寲绮惧搧", "澶鏂囧寲绮惧搧", "澶鏂囧寲绮惧搧"],
    "鍖椾含绾疄绉戞暀": ["CCTV-鍖椾含绾疄绉戞暀", "CCTV鍖椾含绾疄绉戞暀"],
    "鍗敓鍋ュ悍": ["CCTV-鍗敓鍋ュ悍", "CCTV鍗敓鍋ュ悍"],
    "鐢佃鎸囧崡": ["CCTV-鐢佃鎸囧崡", "CCTV鐢佃鎸囧崡"],
    "灞变笢鍗": ["灞变笢鍗", "灞变笢鍗 HD", "灞变笢鍗楂樻竻"],
    "娴欐睙鍗": ["娴欐睙鍗", "娴欐睙鍗 HD", "娴欐睙鍗楂樻竻"],
    "姹熻嫃鍗": ["姹熻嫃鍗", "姹熻嫃鍗 HD", "姹熻嫃鍗楂樻竻"],
    "涓滄柟鍗": ["涓滄柟鍗", "涓滄柟鍗 HD", "涓滄柟鍗楂樻竻"],
    "娣卞湷鍗": ["娣卞湷鍗", "娣卞湷鍗 HD", "娣卞湷鍗楂樻竻"],
    "鍖椾含鍗": ["鍖椾含鍗", "鍖椾含鍗 HD", "鍖椾含鍗楂樻竻"],
    "骞夸笢鍗": ["骞夸笢鍗", "骞夸笢鍗 HD", "骞夸笢鍗楂樻竻"],
    "骞胯タ鍗": ["骞胯タ鍗", "骞胯タ鍗 HD", "骞胯タ鍗楂樻竻"],
    "涓滃崡鍗": ["涓滃崡鍗", "涓滃崡鍗 HD", "涓滃崡鍗楂樻竻"],
    "娴峰崡鍗": ["娴峰崡鍗", "娴峰崡鍗 HD", "娴峰崡鍗楂樻竻", "鏃呮父鍗", "鏃呮父鍗 HD"],
    "娌冲寳鍗": ["娌冲寳鍗", "娌冲寳鍗 HD", "娌冲寳鍗楂樻竻"],
    "娌冲崡鍗": ["娌冲崡鍗", "娌冲崡鍗 HD", "娌冲崡鍗楂樻竻"],
    "婀栧寳鍗": ["婀栧寳鍗", "婀栧寳鍗 HD", "婀栧寳鍗楂樻竻"],
    "姹熻タ鍗": ["姹熻タ鍗", "姹熻タ鍗 HD", "姹熻タ鍗楂樻竻"],
    "鍥涘窛鍗": ["鍥涘窛鍗", "鍥涘窛鍗 HD", "鍥涘窛鍗楂樻竻"],
    "閲嶅簡鍗": ["閲嶅簡鍗", "閲嶅簡鍗 HD", "閲嶅簡鍗楂樻竻"],
    "璐靛窞鍗": ["璐靛窞鍗", "璐靛窞鍗 HD", "璐靛窞鍗楂樻竻"],
    "浜戝崡鍗": ["浜戝崡鍗", "浜戝崡鍗 HD", "浜戝崡鍗楂樻竻"],
    "澶╂触鍗": ["澶╂触鍗", "澶╂触鍗 HD", "澶╂触鍗楂樻竻"],
    "瀹夊窘鍗": ["瀹夊窘鍗", "瀹夊窘鍗 HD", "瀹夊窘鍗楂樻竻"],
    "婀栧崡鍗": ["婀栧崡鍗", "婀栧崡鍗 HD", "婀栧崡鍗楂樻竻"],
    "杈藉畞鍗": ["杈藉畞鍗", "杈藉畞鍗 HD", "杈藉畞鍗楂樻竻"],
    "榛戦緳姹熷崼瑙?: ["榛戦緳姹熷崼瑙?, "榛戦緳姹熷崼瑙?HD", "榛戦緳姹熷崼瑙嗛珮娓?],
    "鍚夋灄鍗": ["鍚夋灄鍗", "鍚夋灄鍗 HD", "鍚夋灄鍗楂樻竻"],
    "鍐呰挋鍙ゅ崼瑙?: ["鍐呰挋鍙ゅ崼瑙?, "鍐呰挋鍙ゅ崼瑙?HD", "鍐呰挋鍙ゅ崼瑙嗛珮娓?],
    "瀹佸鍗": ["瀹佸鍗", "瀹佸鍗 HD", "瀹佸鍗楂樻竻"],
    "灞辫タ鍗": ["灞辫タ鍗", "灞辫タ鍗 HD", "灞辫タ鍗楂樻竻"],
    "闄曡タ鍗": ["闄曡タ鍗", "闄曡タ鍗 HD", "闄曡タ鍗楂樻竻"],
    "鐢樿們鍗": ["鐢樿們鍗", "鐢樿們鍗 HD", "鐢樿們鍗楂樻竻"],
    "闈掓捣鍗": ["闈掓捣鍗", "闈掓捣鍗 HD", "闈掓捣鍗楂樻竻"],
    "鏂扮枂鍗": ["鏂扮枂鍗", "鏂扮枂鍗 HD", "鏂扮枂鍗楂樻竻"],
    "瑗胯棌鍗": ["瑗胯棌鍗", "瑗胯棌鍗 HD", "瑗胯棌鍗楂樻竻"],
    "涓夋矙鍗": ["涓夋矙鍗", "涓夋矙鍗 HD", "涓夋矙鍗楂樻竻"],
    "鍘﹂棬鍗": ["鍘﹂棬鍗", "鍘﹂棬鍗 HD", "鍘﹂棬鍗楂樻竻"],
    "鍏靛洟鍗": ["鍏靛洟鍗", "鍏靛洟鍗 HD", "鍏靛洟鍗楂樻竻"],
    "寤惰竟鍗": ["寤惰竟鍗", "寤惰竟鍗 HD", "寤惰竟鍗楂樻竻"],
    "瀹夊鍗": ["瀹夊鍗", "瀹夊鍗 HD", "瀹夊鍗楂樻竻"],
    "搴峰反鍗": ["搴峰反鍗", "搴峰反鍗 HD", "搴峰反鍗楂樻竻"],
    "鍐滄灄鍗": ["鍐滄灄鍗", "鍐滄灄鍗 HD", "鍐滄灄鍗楂樻竻"],
    "灞变笢鏁欒偛": ["灞变笢鏁欒偛", "灞变笢鏁欒偛 HD", "灞变笢鏁欒偛楂樻竻"],
    "CETV1": ["CETV-1", "涓浗鏁欒偛1", "涓浗鏁欒偛-1", "涓浗鏁欒偛鐢佃鍙?"],
    "CETV2": ["CETV-2", "涓浗鏁欒偛2", "涓浗鏁欒偛-2", "涓浗鏁欒偛鐢佃鍙?"],
    "CETV3": ["CETV-3", "涓浗鏁欒偛3", "涓浗鏁欒偛-3", "涓浗鏁欒偛鐢佃鍙?"],
    "CETV4": ["CETV-4", "涓浗鏁欒偛4", "涓浗鏁欒偛-4", "涓浗鏁欒偛鐢佃鍙?"],
    "鏃╂湡鏁欒偛": ["鏃╂湡鏁欒偛", "鏃╂暀", "骞煎効鏁欒偛"],
    "鍖椾含璐㈢粡": ["鍖椾含璐㈢粡", "BTV璐㈢粡", "BTV-璐㈢粡"],
    "鍖椾含绾疄": ["鍖椾含绾疄", "BTV绾疄", "BTV-绾疄"],
    "鍖椾含鐢熸椿": ["鍖椾含鐢熸椿", "BTV鐢熸椿", "BTV-鐢熸椿"],
    "鍖椾含浣撹偛浼戦棽": ["鍖椾含浣撹偛浼戦棽", "BTV浣撹偛浼戦棽", "BTV-浣撹偛浼戦棽"],
    "鍖椾含鍥介檯": ["鍖椾含鍥介檯", "BTV鍥介檯", "BTV-鍥介檯"],
    "鍖椾含鏂囪壓": ["鍖椾含鏂囪壓", "BTV鏂囪壓", "BTV-鏂囪壓"],
    "鍖椾含鏂伴椈": ["鍖椾含鏂伴椈", "BTV鏂伴椈", "BTV-鏂伴椈"],
    "鍖椾含娣樼數褰?: ["鍖椾含娣樼數褰?, "BTV娣樼數褰?],
    "鍖椾含娣樺墽鍦?: ["鍖椾含娣樺墽鍦?, "BTV娣樺墽鍦?],
    "鍖椾含娣?K": ["鍖椾含娣?K", "BTV娣?K"],
    "鍖椾含娣樺ū涔?: ["鍖椾含娣樺ū涔?, "BTV娣樺ū涔?],
    "鍖椾含娣楤ABY": ["鍖椾含娣楤ABY", "BTV娣楤ABY"],
    "鍖椾含钀屽疇TV": ["鍖椾含钀屽疇TV", "BTV钀屽疇TV"],
    "灞变笢榻愰瞾": ["灞变笢榻愰瞾", "榻愰瞾棰戦亾"],
    "灞变笢缁艰壓": ["灞变笢缁艰壓", "缁艰壓棰戦亾"],
    "灞变笢灏戝効": ["灞变笢灏戝効", "灏戝効棰戦亾"],
    "灞变笢鐢熸椿": ["灞变笢鐢熸椿", "鐢熸椿棰戦亾"],
    "灞变笢鏂伴椈": ["灞变笢鏂伴椈", "鏂伴椈棰戦亾"],
    "灞变笢鍥介檯": ["灞变笢鍥介檯", "鍥介檯棰戦亾"],
    "灞变笢浣撹偛": ["灞变笢浣撹偛", "浣撹偛棰戦亾"],
    "灞变笢鏂囨梾": ["灞变笢鏂囨梾", "鏂囨梾棰戦亾"],
    "灞变笢鍐滅": ["灞变笢鍐滅", "鍐滅棰戦亾"],
    "鍑ゅ嚢涓枃": ["鍑ゅ嚢涓枃", "鍑ゅ嚢鍗涓枃鍙?],
    "鍑ゅ嚢璧勮": ["鍑ゅ嚢璧勮", "鍑ゅ嚢鍗璧勮鍙?],
    "鍑ゅ嚢棣欐腐": ["鍑ゅ嚢棣欐腐", "鍑ゅ嚢鍗棣欐腐鍙?],
    "鍑ゅ嚢鐢靛奖": ["鍑ゅ嚢鐢靛奖", "鍑ゅ嚢鍗鐢靛奖鍙?],
    "CHC鍔ㄤ綔鐢靛奖": ["CHC鍔ㄤ綔鐢靛奖", "鍔ㄤ綔鐢靛奖"],
    "CHC瀹跺涵褰遍櫌": ["CHC瀹跺涵褰遍櫌", "瀹跺涵褰遍櫌"],
    "CHC褰辫糠鐢靛奖": ["CHC褰辫糠鐢靛奖", "褰辫糠鐢靛奖"],
    "娣樼數褰?: ["娣樼數褰?, "鐢靛奖"],
    "娣樼簿褰?: ["娣樼簿褰?, "绮惧僵"],
    "娣樺墽鍦?: ["娣樺墽鍦?, "鍓у満"],
    "鏄熺┖鍗": ["鏄熺┖鍗", "鏄熺┖"],
    "榛戣帗鐢靛奖": ["榛戣帗鐢靛奖", "鐢靛奖"],
    "涓滃寳鐑墽": ["涓滃寳鐑墽", "鐑墽"],
    "涓浗鍔熷か": ["涓浗鍔熷か", "鍔熷か"],
    "鍔ㄤ綔鐢靛奖": ["鍔ㄤ綔鐢靛奖", "鐢靛奖鍔ㄤ綔"],
    "瓒呯骇鐢靛奖": ["瓒呯骇鐢靛奖", "鐢靛奖瓒呯骇"],
    "鍔ㄦ极绉€鍦?: ["鍔ㄦ极绉€鍦?, "鍔ㄦ极"],
    "鍝掑暤鐢电珵": ["鍝掑暤鐢电珵", "鐢电珵"],
    "榛戣帗鍔ㄧ敾": ["榛戣帗鍔ㄧ敾", "鍔ㄧ敾"],
    "鍗￠叿灏戝効": ["鍗￠叿灏戝効", "鍗￠叿"],
    "閲戦拱鍗￠€?: ["閲戦拱鍗￠€?, "閲戦拱"],
    "浼樻极鍗￠€?: ["浼樻极鍗￠€?, "浼樻极"],
    "鍝堝搱鐐姩": ["鍝堝搱鐐姩", "鍝堝搱"],
    "鍢変匠鍗￠€?: ["鍢変匠鍗￠€?, "鍢変匠"],
    "iHOT鐖卞枩鍓?: ["iHOT鐖卞枩鍓?, "鐖卞枩鍓?],
    "iHOT鐖辩骞?: ["iHOT鐖辩骞?, "鐖辩骞?],
    "iHOT鐖遍櫌绾?: ["iHOT鐖遍櫌绾?, "鐖遍櫌绾?],
    "iHOT鐖辨偓鐤?: ["iHOT鐖辨偓鐤?, "鐖辨偓鐤?],
    "iHOT鐖卞巻鍙?: ["iHOT鐖卞巻鍙?, "鐖卞巻鍙?],
    "iHOT鐖辫皪鎴?: ["iHOT鐖辫皪鎴?, "鐖辫皪鎴?],
    "iHOT鐖辨梾琛?: ["iHOT鐖辨梾琛?, "鐖辨梾琛?],
    "iHOT鐖卞辜鏁?: ["iHOT鐖卞辜鏁?, "鐖卞辜鏁?],
    "iHOT鐖辩帺鍏?: ["iHOT鐖辩帺鍏?, "鐖辩帺鍏?],
    "iHOT鐖变綋鑲?: ["iHOT鐖变綋鑲?, "鐖变綋鑲?],
    "iHOT鐖辫禌杞?: ["iHOT鐖辫禌杞?, "鐖辫禌杞?],
    "iHOT鐖辨氮婕?: ["iHOT鐖辨氮婕?, "鐖辨氮婕?],
    "iHOT鐖卞璋?: ["iHOT鐖卞璋?, "鐖卞璋?],
    "iHOT鐖辩瀛?: ["iHOT鐖辩瀛?, "鐖辩瀛?],
    "iHOT鐖卞姩婕?: ["iHOT鐖卞姩婕?, "鐖卞姩婕?],
    "閲嶆俯缁忓吀": ["閲嶆俯缁忓吀", "缁忓吀"],
    "CHANNEL[V]": ["CHANNEL[V]", "Channel V"],
    "姹傜储绾綍": ["姹傜储绾綍", "绾綍"],
    "姹傜储绉戝": ["姹傜储绉戝", "绉戝"],
    "姹傜储鐢熸椿": ["姹傜储鐢熸椿", "鐢熸椿"],
    "姹傜储鍔ㄧ墿": ["姹傜储鍔ㄧ墿", "鍔ㄧ墿"],
    "鐫涘僵闈掑皯": ["鐫涘僵闈掑皯", "闈掑皯"],
    "鐫涘僵绔炴妧": ["鐫涘僵绔炴妧", "绔炴妧"],
    "鐫涘僵绡悆": ["鐫涘僵绡悆", "绡悆"],
    "鐫涘僵骞垮満鑸?: ["鐫涘僵骞垮満鑸?, "骞垮満鑸?],
    "閲戦拱绾疄": ["閲戦拱绾疄", "绾疄"],
    "蹇箰鍨傞挀": ["蹇箰鍨傞挀", "鍨傞挀"],
    "鑼堕閬?: ["鑼堕閬?, "鑼?],
    "鍐涗簨璇勮": ["鍐涗簨璇勮", "鍐涗簨"],
    "鍐涙梾鍓у満": ["鍐涙梾鍓у満", "鍐涙梾"],
    "涔愭父": ["涔愭父", "鏃呮父"],
    "鐢熸椿鏃跺皻": ["鐢熸椿鏃跺皻", "鏃跺皻"],
    "閮藉競鍓у満": ["閮藉競鍓у満", "閮藉競"],
    "娆㈢瑧鍓у満": ["娆㈢瑧鍓у満", "娆㈢瑧"],
    "娓告垙椋庝簯": ["娓告垙椋庝簯", "娓告垙"],
    "閲戣壊瀛﹀爞": ["閲戣壊瀛﹀爞", "瀛﹀爞"],
    "娉曟不澶╁湴": ["娉曟不澶╁湴", "娉曟不"],
    "鍝掑暤璧涗簨": ["鍝掑暤璧涗簨", "璧涗簨"],
    "鍙よ鍓у満": ["鍙よ鍓у満", "鍙よ"],
    "瀹跺涵鍓у満": ["瀹跺涵鍓у満", "瀹跺涵"],
    "鎯婃倸鎮枒": ["鎯婃倸鎮枒", "鎮枒"],
    "鏄庢槦澶х墖": ["鏄庢槦澶х墖", "澶х墖"],
    "娆箰鍓у満": ["娆箰鍓у満", "娆箰"],
    "娴峰鍓у満": ["娴峰鍓у満", "娴峰"],
    "娼杈ｅ﹩": ["娼杈ｅ﹩", "娼"],
    "鐖辨儏鍠滃墽": ["鐖辨儏鍠滃墽", "鐖辨儏"],
    "瓒呯骇鐢佃鍓?: ["瓒呯骇鐢佃鍓?, "鐢佃鍓?],
    "瓒呯骇缁艰壓": ["瓒呯骇缁艰壓", "缁艰壓"],
    "閲戠墝缁艰壓": ["閲戠墝缁艰壓", "閲戠墝"],
    "姝︽悘涓栫晫": ["姝︽悘涓栫晫", "姝︽悘"],
    "鍐滀笟鑷村瘜": ["鍐滀笟鑷村瘜", "鍐滀笟"],
    "鐐垶鏈潵": ["鐐垶鏈潵", "鐐垶"],
    "绮惧搧浣撹偛": ["绮惧搧浣撹偛", "绮惧搧"],
    "绮惧搧澶у墽": ["绮惧搧澶у墽", "澶у墽"],
    "绮惧搧绾綍": ["绮惧搧绾綍", "绾綍"],
    "绮惧搧钀屽疇": ["绮惧搧钀屽疇", "钀屽疇"],
    "鎬′即鍋ュ悍": ["鎬′即鍋ュ悍", "鍋ュ悍"],
    "澶╁厓鍥存": ["澶╁厓鍥存", "鍥存"],
    "榄呭姏瓒崇悆": ["榄呭姏瓒崇悆", "瓒崇悆"],
    "浜旀槦浣撹偛": ["浜旀槦浣撹偛", "浜旀槦"],
    "鍔茬垎浣撹偛": ["鍔茬垎浣撹偛", "鍔茬垎"],
    "瓒呯骇浣撹偛": ["瓒呯骇浣撹偛", "瓒呯骇"],
    "闊充箰棰戦亾": ["闊充箰棰戦亾", "闊充箰"],
    "CCTV闊充箰": ["CCTV闊充箰", "闊充箰"],
    "CHANNEL[V]": ["CHANNEL[V]", "Channel V"],
    "闊充箰Tai": ["闊充箰Tai", "闊充箰鍙?],
    "闊充箰鍙?: ["闊充箰鍙?, "闊充箰"],
    "MTV": ["MTV", "闊充箰鐢佃"],
    "MTV涓枃": ["MTV涓枃", "涓枃MTV"],
    "鍗庤闊充箰": ["鍗庤闊充箰", "鍗庤"],
    "娴佽闊充箰": ["娴佽闊充箰", "娴佽"],
    "鍙ゅ吀闊充箰": ["鍙ゅ吀闊充箰", "鍙ゅ吀"]
}

# 娣诲姞棰濆鐨勬槧灏勫叧绯?
for channel, aliases in additional_mappings.items():
    if channel in CHANNEL_MAPPING:
        CHANNEL_MAPPING[channel].extend(aliases)

# 寤虹珛棰戦亾鍒扮被鍒殑鏄犲皠
CHANNEL_TO_CATEGORY = {}
for category, channels in CHANNEL_CATEGORIES.items():
    for channel in channels:
        CHANNEL_TO_CATEGORY[channel] = category

# 绫诲埆椤哄簭鍒楄〃
CATEGORY_ORDER = list(CHANNEL_CATEGORIES.keys())

# 娓呮櫚搴︽鍒欒〃杈惧紡 - 澧炲己鐗堬紝鏇村ソ鍦拌瘑鍒珮娓呯嚎璺?
HD_PATTERNS = [
    # 4K鍙婁互涓?
    r'[48]k',
    r'2160[pdi]',
    r'uhd',
    r'瓒呴珮娓?,
    r'4k',
    # 2K
    r'1440[pdi]',
    r'qhd',
    # 1080P鍙婁互涓?
    r'1080[pdi]',
    r'fhd',
    # 鍏朵粬楂樻竻鏍囪瘑
    r'楂樻竻',
    r'瓒呮竻',
    r'hd',
    r'high.?definition',
    r'high.?def',
    # 鐗瑰畾鐨勯珮娓呮爣璇?
    r'hdmi',
    r'钃濆厜',
    r'blue.?ray',
    r'hd.?live',
    # 鐮佺巼鏍囪瘑
    r'[89]m',
    r'[1-9]\d+m',
    # 鐗瑰畾鐨刄RL鍙傛暟鏍囪瘑
    r'quality=high',
    r'resolution=[1-9]\d{3}',
    r'hd=true',
    r'fhd=true'
]

HD_REGEX = re.compile('|'.join(HD_PATTERNS), re.IGNORECASE)

def should_exclude_url(url):
    """妫€鏌ユ槸鍚﹀簲璇ユ帓闄ょ壒瀹歎RL"""
    if not url:
        return True
    # 鍏佽鎵€鏈塇TTP鍜孒TTPS鐨刄RL锛屼絾鎺掗櫎浠ttp://example鎴杊ttps://example寮€澶寸殑URL锛屼互鍙婂寘鍚?demo"瀛楃鐨刄RL
    return not (url.startswith('http://') or url.startswith('https://')) or url.startswith('http://example') or url.startswith('https://example') or "demo" in url.lower()

def fetch_content(url, timeout=10, max_retries=3):
    """鑾峰彇URL鍐呭锛屾敮鎸佽秴鏃跺拰閲嶈瘯"""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=timeout, headers=HEADERS)
            response.raise_for_status()  # 濡傛灉鐘舵€佺爜涓嶆槸200锛屾姏鍑哄紓甯?
            return response.text
        except requests.RequestException:
            retries += 1
            if retries >= max_retries:
                return None
            time.sleep(2)  # 閲嶈瘯鍓嶇瓑寰?绉?

def is_high_quality(line):
    """鍒ゆ柇绾胯矾鏄惁涓洪珮娓呯嚎璺紙1080P浠ヤ笂锛?""
    # 浼樺厛妫€鏌ユ槸鍚︽槑纭寘鍚?080p鎴栨洿楂樻竻鐨勬爣璇?
    high_def_patterns = re.compile(r'(1080[pdi]|1440[pdi]|2160[pdi]|[48]k|fhd|uhd|瓒呴珮娓厊4k)', re.IGNORECASE)
    if high_def_patterns.search(line):
        return True

    # 鍏舵妫€鏌ユ槸鍚﹀寘鍚叾浠栭珮娓呮爣璇?
    if HD_REGEX.search(line):
        # 鎺掗櫎涓€浜涘彲鑳借鍒ょ殑鎯呭喌
        low_quality_patterns = re.compile(r'(360|480|576|鏍囨竻|sd|low)', re.IGNORECASE)
        if not low_quality_patterns.search(line):
            return True

    # 妫€鏌RL涓槸鍚﹀寘鍚壒瀹氱殑楂樻竻鍙傛暟
    url_high_patterns = re.compile(r'(\bhd\b|quality=high|res=[1-9]\d{3}|bitrate=[8-9]\d{2}|bitrate=\d{4,})', re.IGNORECASE)
    return bool(url_high_patterns.search(line))

def normalize_channel_name(name):
    """鏍囧噯鍖栭閬撳悕绉帮紝杩涜绮剧‘鍖归厤銆佸寘鍚尮閰嶃€佸弽鍚戝尮閰嶅拰鍏抽敭璇嶅尮閰?""
    if not name:
        return None

    # 绉婚櫎涓€浜涘父瑙佺殑鍚庣紑鎴栨爣璇嗙
    name = name.strip()
    for suffix in ['楂樻竻', 'HD', '(楂樻竻)', '[楂樻竻]', '(HD)', '[HD]', '-HD', '路HD', '\t']:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()

    # 绮剧‘鍖归厤
    if name in CHANNEL_MAPPING:
        return name

    # 鍖呭惈鍖归厤 - 妫€鏌ラ閬撳悕鏄惁鍖呭惈瑙勮寖鍚?
    for canonical_name, aliases in CHANNEL_MAPPING.items():
        # 妫€鏌ヨ鑼冨悕鏄惁鍦ㄥ綋鍓嶅悕绉颁腑
        if canonical_name in name:
            return canonical_name

        # 妫€鏌ュ埆鍚嶆槸鍚﹀湪褰撳墠鍚嶇О涓?
        for alias in aliases:
            if alias in name:
                return canonical_name

    # 鍙嶅悜鍖归厤 - 妫€鏌ヨ鑼冨悕鏄惁鍖呭惈褰撳墠鍚嶇О
    for canonical_name in CHANNEL_MAPPING:
        if name in canonical_name:
            return canonical_name

    # 鍏抽敭璇嶅尮閰?- 鎻愬彇鍚嶇О涓殑鍏抽敭璇嶈繘琛屽尮閰?
    keywords = re.findall(r'[a-zA-Z0-9\u4e00-\u9fa5]+', name)
    for keyword in keywords:
        if keyword in CHANNEL_MAPPING:
            return keyword

    # 鐗规畩澶勭悊CCTV棰戦亾
    cctv_match = re.search(r'CCTV(\d{1,2})', name, re.IGNORECASE)
    if cctv_match:
        cctv_num = cctv_match.group(1)
        canonical_cctv = f"CCTV{cctv_num}"
        if canonical_cctv in CHANNEL_MAPPING:
            return canonical_cctv

    # 鏃犲尮閰嶏紝杩斿洖鍘熷鍚嶇О
    return None

def extract_channels(content):
    """浠庡唴瀹逛腑鎻愬彇棰戦亾淇℃伅"""
    if not content:
        return []

    channels = []

    # 1. M3U鏍煎紡
    if '#EXTM3U' in content:
        lines = content.splitlines()
        for i in range(len(lines)):
            if lines[i].startswith('#EXTINF:'):
                # 鎻愬彇棰戦亾鍚嶇О
                name_match = re.search(r',([^,]+)$', lines[i])
                if name_match and i + 1 < len(lines):
                    name = name_match.group(1).strip()
                    url = lines[i + 1].strip()
                    if url.startswith(('http://', 'https://')) and not should_exclude_url(url):
                        channels.append((name, url))

    # 2. 鏂囨湰鏍煎紡: 棰戦亾鍚?URL
    elif ',' in content:
        lines = content.splitlines()
        for line in lines:
            if ',' in line and ('http://' in line or 'https://' in line):
                try:
                    name, url = line.rsplit(',', 1)
                    name = name.strip()
                    url = url.strip()
                    if url.startswith(('http://', 'https://')) and not should_exclude_url(url):
                        channels.append((name, url))
                except ValueError:
                    continue

    # 3. 姣忚涓€涓猆RL锛屽皾璇曚粠URL涓彁鍙栦俊鎭?
    else:
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith(('http://', 'https://')) and not should_exclude_url(line):
                    # 灏濊瘯浠嶶RL涓彁鍙栧悕绉?
                    name = line.split('/')[-1].split('?')[0].split('#')[0]
                    channels.append((name, line))

    return channels

def process_source(source_url):
    """澶勭悊鍗曚釜鏁版嵁婧?""
    # 娓呯悊URL锛岀Щ闄ゅ彲鑳界殑寮曞彿鍜岀┖鏍?
    url = source_url.strip('"`\' ')
    content = fetch_content(url)
    if not content:
        return []

    channels = extract_channels(content)
    if not channels:
        return []

    # 杩囨护鍜屾爣鍑嗗寲棰戦亾
    processed_channels = []
    for name, url in channels:
        # 妫€鏌RL鍜屽悕绉?
        if not url or not url.startswith(('http://', 'https://')) or should_exclude_url(url):
            continue

        # 杩囨护楂樻竻绾胯矾
        combined = name + ' ' + url
        if not is_high_quality(combined):
            continue

        # 鏍囧噯鍖栭閬撳悕绉?
        normalized_name = normalize_channel_name(name)
        if normalized_name:
            processed_channels.append((normalized_name, url))

    return processed_channels

def sort_and_limit_lines(lines):
    """鎺掑簭骞堕檺鍒剁嚎璺暟閲忥紝纭繚浼樺厛淇濈暀楂樿川閲忕嚎璺?""
    # 鏇寸簿纭殑娓呮櫚搴︽帓搴忓嚱鏁?
    def sort_key(line):
        name, url = line
        combined = (name + ' ' + url).lower()

        # 4K鍙婁互涓?(鏈€楂樹紭鍏堢骇)
        if any(keyword in combined for keyword in ['4k', '2160p', '2160i', 'uhd', '瓒呴珮娓?]):
            return (0, len(combined))  # 闀垮害浣滀负娆¤鎺掑簭鏉′欢锛屾洿绠€娲佺殑URL鍙兘鏇村ソ

        # 2K (绗簩浼樺厛绾?
        elif any(keyword in combined for keyword in ['1440p', 'qhd', '2k']):
            return (1, len(combined))

        # 1080p/i (绗笁浼樺厛绾?
        elif any(keyword in combined for keyword in ['1080p', '1080i', '1080d', 'fhd']):
            # 杩涗竴姝ョ粏鍒嗭細1080p浼樺厛浜?080i
            if '1080p' in combined:
                return (2, 0, len(combined))
            else:
                return (2, 1, len(combined))

        # 楂樻竻 (绗洓浼樺厛绾?
        elif any(keyword in combined for keyword in ['楂樻竻', 'hd', 'high definition']):
            return (3, len(combined))

        # 鍏朵粬楂樻竻鏍囪瘑 (绗簲浼樺厛绾?
        elif any(keyword in combined for keyword in ['瓒呮竻', '钃濆厜', 'blue-ray']):
            return (4, len(combined))

        # 鏅€氱嚎璺?(鏈€浣庝紭鍏堢骇)
        return (5, len(combined))

    # 鎺掑簭
    sorted_lines = sorted(lines, key=sort_key)

    # 闄愬埗鏁伴噺 - 纭繚鍦ㄨ寖鍥村唴
    if len(sorted_lines) < MIN_LINES_PER_CHANNEL:
        # 绾胯矾涓嶈冻鏃讹紝淇濈暀鎵€鏈夌嚎璺?
        return sorted_lines
    elif len(sorted_lines) > MAX_LINES_PER_CHANNEL:
        # 绾胯矾杩囧鏃讹紝鍙繚鐣欏墠MAX_LINES_PER_CHANNEL涓?
        return sorted_lines[:MAX_LINES_PER_CHANNEL]
    else:
        # 鏁伴噺鍦ㄥ悎鐞嗚寖鍥村唴锛屽叏閮ㄤ繚鐣?
        return sorted_lines

def write_output_file(category_channels, debug_mode=False):
    """鍐欏叆杈撳嚭鏂囦欢"""
    output_lines = []

    if debug_mode:

    # 鎸夌収鎸囧畾鐨勯『搴忛亶鍘嗙被鍒?
    for category in CATEGORY_ORDER:
        if category not in category_channels:
            continue

        if debug_mode:

        # 娣诲姞绫诲埆鏍囪
        output_lines.append(f"#{category},#genre#")

        # 娣诲姞璇ョ被鍒殑棰戦亾
        for channel_name, lines in category_channels[category].items():
            if debug_mode:

            output_lines.append(f"##{channel_name}")
            for name, url in lines:
                # 楠岃瘉URL
                if url and url.startswith(('http://', 'https://')):
                    output_lines.append(f"{name},{url}")

        # 鍦ㄧ被鍒箣闂存坊鍔犵┖琛?
        output_lines.append("")

    if debug_mode:

    # 鍐欏叆鏂囦欢
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    return True

def main():
    """涓诲嚱鏁?""
    args = parse_args()

    if debug_mode:

    # 骞跺彂澶勭悊鎵€鏈夋暟鎹簮
    all_channels = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_source = {executor.submit(process_source, source): source for source in GITHUB_SOURCES}
        for future in concurrent.futures.as_completed(future_to_source):
            try:
                channels = future.result()
                if debug_mode:
                all_channels.extend(channels)
            except Exception as e:
                if debug_mode:

    # 鎸夐閬撳悕绉板垎缁?
    channel_map = {}
    for name, url in all_channels:
        if name not in channel_map:
            channel_map[name] = []
        channel_map[name].append((name, url))

    # 鎺掑簭骞堕檺鍒舵瘡涓閬撶殑绾胯矾鏁伴噺
    for name in channel_map:
        channel_map[name] = sort_and_limit_lines(channel_map[name])

    # 鎸夌被鍒垎缁?
    category_channels = {}
    for channel_name, lines in channel_map.items():
        if channel_name in CHANNEL_TO_CATEGORY:
            category = CHANNEL_TO_CATEGORY[channel_name]
            if category not in category_channels:
                category_channels[category] = {}
            category_channels[category][channel_name] = lines

    # 鍐欏叆杈撳嚭鏂囦欢
    write_output_file(category_channels, debug_mode=debug_mode)

def parse_args():
    """瑙ｆ瀽鍛戒护琛屽弬鏁?""
    parser = argparse.ArgumentParser(description='TV Channel Processor')
    parser.add_argument('-o', '--output', type=str, default=OUTPUT_FILE, help='Output file name')
    return parser.parse_args()

if __name__ == "__main__":
    # 瑙ｆ瀽鍛戒护琛屽弬鏁?
    args = parse_args()

    # 濡傛灉鎸囧畾浜嗚緭鍑烘枃浠跺悕锛屾洿鏂板叏灞€鍙橀噺
    if args.output:
        OUTPUT_FILE = args.output

    main()
