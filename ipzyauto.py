import re
import time
import requests
import statistics
import concurrent.futures
from collections import defaultdict

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
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-央视高网", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    
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
    "康巴卫视": ["康巴卫视 HD"],
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
    "北京纪实": ["北京纪实 HD", "北京纪实科教", "北京纪实科教 HD"],
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
    "北京卡酷少儿": ["北京卡酷少儿 HD", "北京KAKU少儿", "北京KAKU少儿 HD", "北京kaku少儿", "北京kaku少儿 HD"],
    
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

# =============================================
# 核心配置
# =============================================

# 正则表达式 - 匹配IPv4和IPv6地址
ipv4_regex = r"http://\d+\.\d+\.\d+\.\d+(?::\d+)?"
ipv6_regex = r"http://\[[0-9a-fA-F:]+\]"

def normalize_channel_name(name: str) -> str:
    """标准化频道名称"""
    if not name:
        return "未知频道"
    return name.strip()

def is_invalid_url(url: str) -> bool:
    """检查是否为无效 URL"""
    invalid_patterns = [
        r"http://\[[a-fA-F0-9:]+\](?::\d+)?/ottrrs\.hl\.chinamobile\.com/.+/.+",
        r"http://\[2409:8087:1a01:df::7005\]/.*",
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, url):
            return True
    return False

def is_preferred_url(url: str) -> bool:
    """判断是否为优选线路"""
    preferred_patterns = [
        r"http://\[2408:.*\]",
        r"http://\d+\.\d+\.\d+\.\d+.*unicom.*",
        r"http://\[240e:.*\]",
        r"http://\d+\.\d+\.\d+\.\d+.*telecom.*",
        r"http://\[2409:.*\]",
        r"http://\d+\.\d+\.\d+\.\d+.*mobile.*",
        r".*\.bj\.",
        r".*\.sd\.",
        r".*\.tj\.",
        r".*\.heb\.",
        r".*\.cn.*",
        r".*\.net.*",
    ]
    
    for pattern in preferred_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False

def should_exclude_url(url):
    """检查是否应该排除某个URL"""
    # 排除特定域名的URL
    exclude_patterns = [
        # 这里可以添加需要排除的域名模式
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, url):
            return True
    
    return False

# 移除URL模糊处理函数，简化代码

# =============================================
# 测速功能配置
# =============================================

# 测速配置
def speed_test_config():
    return {
        'enabled': False,         # 禁用测速功能，减少网络请求
        'timeout': 5,           # 超时时间(秒)
        'test_duration': 3,      # 测速持续时间(秒)
        'max_workers': 10,       # 并发线程数
        'min_download_bytes': 1024.0 * 512.0,  # 最小下载量(KB)
    }

# 测试单个URL的速度
def test_url_speed(url, config):
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        })
        
        start_time = time.time()
        response = session.get(url, stream=True, timeout=config['timeout'])
        
        if response.status_code != 200:
            return {'url': url, 'speed_kbps': 0, 'status': 'unavailable', 'error': f'HTTP {response.status_code}'}
        
        downloaded_bytes = 0
        speed_samples = []
        sample_start = time.time()
        sample_bytes = 0
        
        while time.time() - start_time < config['test_duration']:
            chunk = response.raw.read(8192)
            if not chunk:
                break
            
            downloaded_bytes += len(chunk)
            sample_bytes += len(chunk)
            
            # 每0.5秒采样一次速度
            if time.time() - sample_start >= 0.5:
                if sample_bytes > 0:
                    speed_kbps = (sample_bytes * 8) / (1024 * (time.time() - sample_start))
                    speed_samples.append(speed_kbps)
                    sample_start = time.time()
                    sample_bytes = 0
        
        response.close()
        
        # 计算平均速度
        if speed_samples:
            avg_speed_kbps = statistics.mean(speed_samples)
            # 计算速度稳定性 (标准差/均值，越小越稳定)
            if len(speed_samples) > 1:
                std_dev = statistics.stdev(speed_samples)
                stability = 1.0 / (1.0 + std_dev / avg_speed_kbps) if avg_speed_kbps > 0 else 0
            else:
                stability = 1.0
            
            return {
                'url': url,
                'speed_kbps': avg_speed_kbps,
                'status': 'available',
                'stability': stability,
                'downloaded_kb': downloaded_bytes / 1024
            }
        else:
            return {'url': url, 'speed_kbps': 0, 'status': 'available', 'error': '无法获取速度样本', 'stability': 0}
            
    except Exception as e:
        return {'url': url, 'speed_kbps': 0, 'status': 'unavailable', 'error': str(e)}

# 批量测试URL速度
def batch_test_urls(urls, config):
    results = {}
    total_urls = len(urls)
    
    if not urls:
        return results
    
    print(f"\n开始测速，共 {total_urls} 个URL，配置：")
    print(f"  - 超时时间: {config['timeout']}秒")
    print(f"  - 测速时长: {config['test_duration']}秒")
    print(f"  - 并发线程: {config['max_workers']}")
    print(f"  - 最小下载: {config['min_download_bytes']/1024:.1f}KB")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=config['max_workers']) as executor:
        future_to_url = {executor.submit(test_url_speed, url, config): url for url in urls}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                result = future.result()
                results[url] = result
                
                # 显示进度
                progress = (i + 1) / total_urls * 100
                print(f"  测速进度: {i+1}/{total_urls} ({progress:.1f}%)", end="\r")
            except Exception as e:
                results[url] = {'url': url, 'speed_kbps': 0, 'status': 'error', 'error': str(e)}
    
    elapsed_time = time.time() - start_time
    print(f"\n测速完成，耗时: {elapsed_time:.2f}秒")
    
    # 统计结果
    available_count = sum(1 for r in results.values() if r['status'] == 'available' and r['speed_kbps'] > 0)
    print(f"  成功测速: {available_count}/{total_urls} ({available_count/total_urls*100:.1f}%)")
    
    return results

def fetch_lines_with_retry(url: str, max_retries=3):
    """带重试机制的下载函数"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    })
    
    for attempt in range(max_retries):
        try:
            timeout = 25 if 'tv.html-5.me' in url else 15
            response = session.get(url, timeout=timeout)
            response.encoding = "utf-8"
            
            if response.status_code == 200:
                return response.text.splitlines()
        except Exception:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    
    return []

def parse_lines(lines):
    """解析 M3U 或 TXT 内容，返回 {频道名: [url列表]}"""
    channels_dict = defaultdict(list)
    current_name = None
    total_lines = len(lines)
    processed_lines = 0
    m3u_count = 0
    txt_count = 0

    print(f"解析开始，共{total_lines}行数据")

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        processed_lines += 1
        print(f"处理行 {i+1}: {line[:100]}{'...' if len(line) > 100 else ''}")

        # M3U #EXTINF 格式
        if line.startswith("#EXTINF"):
            m3u_count += 1
            if "," in line:
                current_name = line.split(",")[-1].strip()
                print(f"  找到M3U频道: {current_name}")
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                print(f"  找到URL: {url}")
                if url.startswith("http://") or url.startswith("https://"):
                    norm_name = normalize_channel_name(current_name)
                    channels_dict[norm_name].append(url)
                    print(f"  添加到字典: {norm_name} -> {url}")
            current_name = None

        # TXT 频道名,URL 格式
        elif "," in line and not line.startswith("#"):
            txt_count += 1
            parts = line.split(",", 1)
            if len(parts) == 2:
                ch_name, url = parts[0].strip(), parts[1].strip()
                print(f"  找到TXT频道: {ch_name}, URL: {url}")
                if url.startswith("http://") or url.startswith("https://"):
                    norm_name = normalize_channel_name(ch_name)
                    channels_dict[norm_name].append(url)
                    print(f"  添加到字典: {norm_name} -> {url}")
    
    # 添加调试信息
    print(f"解析结果: 共{total_lines}行，处理{processed_lines}行，M3U格式{str(m3u_count)}行，TXT格式{str(txt_count)}行")
    print(f"解析到频道数: {len(channels_dict)}个频道")
    print(f"解析到URL数: {sum(len(urls) for urls in channels_dict.values())}个URL")
    
    # 打印前10个频道作为示例
    print("前10个频道示例:")
    for i, (ch, urls) in enumerate(list(channels_dict.items())[:10]):
        print(f"  {i+1}. {ch}: {len(urls)}个URL")
    
    return channels_dict

def create_txt_file(all_channels, filename="ipzyauto.txt", speed_results=None):
    """生成带分类的 TXT 文件，每个频道和URL各占一行，并添加测速结果"""
    print(f"\n开始生成文件 {filename}...")
    print(f"总频道数: {len(all_channels)}")
    
    # 添加调试信息：打印所有频道
    print("所有频道列表：")
    channel_list = list(all_channels.keys())
    for i, channel in enumerate(channel_list[:20]):  # 只打印前20个频道
        print(f"  {i+1}. {channel}: {len(all_channels[channel])}个URL")
    if len(channel_list) > 20:
        print(f"  ... 还有 {len(channel_list) - 20} 个频道")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("公告,#genre#\n")
        f.write("IPTV直播源 - 自动生成\n")
        f.write("格式: 频道名称,播放URL\n")
        f.write("分组: 4K频道,央视频道,卫视频道,北京频道,山东频道,港澳频道,电影频道,儿童频道,iHOT频道,综合频道,体育频道,剧场频道,其他频道\n")
        f.write("备注: 每个频道后的测速结果仅供参考，实际播放效果可能因网络环境而异\n\n")
        
        # 写入央视频道分类
        f.write("央视频道,#genre#\n")
        print("  处理分类: 央视频道")
        
        # 先处理央视频道
        common_cctv_channels = ['CCTV1', 'CCTV2', 'CCTV3', 'CCTV4', 'CCTV5', 'CCTV6', 'CCTV7', 'CCTV8', 'CCTV9', 'CCTV10',
                               'CCTV11', 'CCTV12', 'CCTV13', 'CCTV14', 'CCTV15', 'CCTV16', 'CCTV17', 'CCTV4K', 'CCTV8K']
        cctv_written = 0
        
        # 先处理特定的央视频道
        for channel in common_cctv_channels:
            if channel in all_channels and all_channels[channel]:
                url = all_channels[channel][0]  # 只取第一个URL
                # 添加测速结果作为注释
                speed_comment = ""
                if speed_results and url in speed_results:
                    speed_data = speed_results[url]
                    if speed_data['status'] == 'available' and speed_data['speed_kbps'] > 0:
                        speed_comment = f"$测速:{speed_data['speed_kbps']:.1f}kbps"
                    else:
                        speed_comment = "$测速:不可用"
                
                f.write(f"{channel},{url}{speed_comment}\n")
                print(f"      写入: {channel},{url}{speed_comment}")
                cctv_written += 1
        
        # 再处理其他CCTV频道（以CCTV开头但不在common列表中的）
        for channel, urls in list(all_channels.items()):
            if channel.startswith('CCTV') and channel not in common_cctv_channels and urls:
                url = urls[0]  # 只取第一个URL
                # 添加测速结果作为注释
                speed_comment = ""
                if speed_results and url in speed_results:
                    speed_data = speed_results[url]
                    if speed_data['status'] == 'available' and speed_data['speed_kbps'] > 0:
                        speed_comment = f"$测速:{speed_data['speed_kbps']:.1f}kbps"
                    else:
                        speed_comment = "$测速:不可用"
                
                f.write(f"{channel},{url}{speed_comment}\n")
                print(f"      写入: {channel},{url}{speed_comment}")
                cctv_written += 1
        
        print(f"  央视频道写入完成，共 {cctv_written} 个频道")
        f.write("\n")
        
        # 写入其他频道分类
        f.write("其他频道,#genre#\n")
        print("  处理分类: 其他频道")
        
        # 写入所有非CCTV频道
        other_written = 0
        for channel, urls in list(all_channels.items()):
            if not channel.startswith('CCTV') and urls:
                url = urls[0]  # 只取第一个URL
                # 添加测速结果作为注释
                speed_comment = ""
                if speed_results and url in speed_results:
                    speed_data = speed_results[url]
                    if speed_data['status'] == 'available' and speed_data['speed_kbps'] > 0:
                        speed_comment = f"$测速:{speed_data['speed_kbps']:.1f}kbps"
                    else:
                        speed_comment = "$测速:不可用"
                
                f.write(f"{channel},{url}{speed_comment}\n")
                print(f"      写入: {channel},{url}{speed_comment}")
                other_written += 1
                
                # 每写入50个频道就打印进度
                if other_written % 50 == 0:
                    print(f"      已写入 {other_written} 个其他频道...")
        
        print(f"  其他频道写入完成，共 {other_written} 个频道")
        f.write("\n")
    
    print(f"\n文件生成完成！")
    print(f"总计写入: {len(all_channels)} 个频道")
    return filename

# 移除统计日志生成功能

# =============================================
# 主函数
# =============================================

def main():
    # 获取测速配置
    speed_config = speed_test_config()
    print(f"测速功能: {'已启用' if speed_config['enabled'] else '已禁用'}")
    
    # 直播源URL列表
    default_sources = [
        "https://ghfast.top/https://raw.githubusercontent.com/moonkeyhoo/iptv-api/master/output/result.m3u",
        "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u",
        "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt",
        "http://106.53.99.30/2025.txt",
    ]
    
    user_sources = [
        "http://tv.html-5.me/i/9390107.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/Supprise0901/TVBox_live/refs/heads/main/live.txt",
        "https://ghfast.top/raw.githubusercontent.com/ffmking/tv1/main/888.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/kimwang1978/collect-txt/refs/heads/main/bbxx.txt",
        "https://ghfast.top/https://raw.githubusercontent.com/Heiwk/iptv67/refs/heads/main/iptv.m3u",
    ]
    
    urls = default_sources + user_sources

    all_channels = defaultdict(list)

    # 从每个URL获取频道数据
    for url in urls:
        print(f"正在获取: {url}")
        max_retries = 5 if 'tv.html-5.me' in url else 3
        lines = fetch_lines_with_retry(url, max_retries=max_retries)
        
        if lines:
            parsed = parse_lines(lines)
            # 合并到总频道列表
            for ch, urls_list in parsed.items():
                all_channels[ch].extend(urls_list)
    
    print(f"\n获取完成，开始数据处理...")
    print(f"总频道数: {len(all_channels)}")
    print(f"总URL数: {sum(len(urls) for urls in all_channels.values())}")
    
    # 添加调试信息：打印all_channels的前10个频道
    print("\n前10个频道详情：")
    for i, (channel, urls) in enumerate(list(all_channels.items())[:10]):
        print(f"  {i+1}. 频道: '{channel}', URL数量: {len(urls)}")
        if urls:  # 如果该频道有URL，打印第一个URL
            print(f"      第一个URL: {urls[0]}")
    
    # 收集所有需要测速的URL（限制数量，避免测试时间过长）
    all_urls_for_testing = []
    for ch, urls_list in all_channels.items():
        unique_urls = list(dict.fromkeys(urls_list))
        filtered_urls = [url for url in unique_urls if not should_exclude_url(url)]
        # 每个频道最多测试3个URL
        all_urls_for_testing.extend(filtered_urls[:3])
    
    # 去重URL列表并限制总数
    all_urls_for_testing = list(set(all_urls_for_testing))[:200]  # 最多测试200个URL
    print(f"需要测速的URL数: {len(all_urls_for_testing)}")
    
    # 执行测速（如果启用）
    speed_results = {}
    if speed_config['enabled'] and all_urls_for_testing:
        speed_results = batch_test_urls(all_urls_for_testing, speed_config)
    
    # 生成TXT文件
    print("\n调用create_txt_file函数生成文件...")
    print(f"  传递的all_channels长度: {len(all_channels)}")
    print(f"  传递的speed_results长度: {len(speed_results) if speed_results else 0}")
    filename = create_txt_file(all_channels, "ipzyauto_full.txt", speed_results)
    
    # 显示生成结果
    print(f"\n文件生成完成: {filename}")
    
    # 验证文件内容
    print(f"\n验证文件内容:")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"  文件总行数: {len(lines)}")
            print(f"  文件前20行:")
            for i, line in enumerate(lines[:20]):
                print(f"    {i+1}: {line.rstrip()}")
            # 查找包含频道数据的行
            data_lines = [line for line in lines if ',' in line and not line.startswith('#') and not line.strip().endswith('#genre#')]
            print(f"  包含频道数据的行数: {len(data_lines)}")
            if data_lines:
                print(f"  前5行频道数据:")
                for i, line in enumerate(data_lines[:5]):
                    print(f"    {i+1}: {line.rstrip()}")
    except Exception as e:
        print(f"  读取文件时出错: {e}")
    
    # 统计频道信息
    total_channels = len(all_channels)
    total_urls = sum(len(urls) for urls in all_channels.values())
    print(f"频道统计: {total_channels}个频道，{total_urls}个URL")
    
    # 如果启用了测速，显示测速统计
    if speed_config['enabled'] and speed_results:
        available_urls = sum(1 for r in speed_results.values() if r['status'] == 'available')
        working_with_speed = sum(1 for r in speed_results.values() if r['status'] == 'available' and r['speed_kbps'] > 0)
        print(f"测速统计: 有效URL {available_urls}个，可测速URL {working_with_speed}个")

def test_fixed_channels():
    """测试函数：使用固定的频道数据生成文件"""
    print("\n=== 开始测试固定频道数据生成 ===")
    
    # 创建固定的频道数据
    fixed_channels = {
        'CCTV1': ['http://example.com/cctv1'],
        'CCTV2': ['http://example.com/cctv2'],
        'CCTV3': ['http://example.com/cctv3'],
        '湖南卫视': ['http://example.com/hntv'],
        '江苏卫视': ['http://example.com/jstv'],
    }
    
    print("固定频道数据:")
    for ch, urls in fixed_channels.items():
        print(f"  频道: '{ch}', URL数量: {len(urls)}")
        if urls:
            print(f"      第一个URL: {urls[0]}")
    
    # 生成文件
    filename = create_txt_file(fixed_channels, "fixed_test.txt")
    
    # 验证文件内容
    print(f"\n验证文件内容 ({filename}):")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"  文件总行数: {len(lines)}")
            print(f"  文件内容:")
            for i, line in enumerate(lines):
                print(f"    {i+1}: {line.rstrip()}")
    except Exception as e:
        print(f"  读取文件时出错: {e}")
    
    print("=== 测试固定频道数据生成完成 ===")

if __name__ == "__main__":
    # 先运行测试函数
    test_fixed_channels()
    
    # 然后运行主函数
    print("\n\n=== 开始运行主函数 ===")
    main()
