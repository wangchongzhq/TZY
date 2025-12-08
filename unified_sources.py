# -*- coding: utf-8 -*-
# 统一播放源列表
# 此文件由update_sources.py自动生成，请勿手动修改

# 播放源URL列表
UNIFIED_SOURCES = [
    "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt",
    "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u"
]

# 带名称的播放源列表（用于collect_ipzy.py）
SOURCES_WITH_NAMES = [
    ("cdn.jsdelivr.net", "https://cdn.jsdelivr.net/gh/Guovin/iptv-api@gd/output/result.txt"),
    ("kakaxi-1-ipv6", "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u"),
    ("kakaxi-1-ipv4", "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt"),
    ("iptv-org-tw", "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/tw.m3u"),
    ("iptv-org-hk", "https://ghfast.top/https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hk.m3u")
]
