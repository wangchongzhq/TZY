#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：检查直播源获取功能
"""

import sys
import time
import ssl
import json
from urllib.request import urlopen, Request
from urllib.parse import urlparse

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# 忽略SSL验证
ssl._create_default_https_context = ssl._create_unverified_context

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

TIMEOUT = 15

def test_github_api():
    """测试GitHub API是否可访问"""
    print("=== 测试GitHub API ===")
    try:
        api_url = "https://api.github.com/repos/imDazui/Tvlist-awesome-m3u-m3u8/commits?path=m3u/4K.m3u&per_page=1"
        req = Request(api_url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data:
                    commit_date = data[0]['commit']['committer']['date']
                    print(f"✅ GitHub API 访问成功")
                    print(f"✅ 最近提交日期: {commit_date}")
                    return True
    except Exception as e:
        print(f"❌ GitHub API 访问失败: {e}")
    return False

def test_live_source(url, name):
    """测试单个直播源"""
    print(f"\n=== 测试直播源: {name} ===")
    try:
        print(f"正在获取: {url}")
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=TIMEOUT) as response:
            if response.status == 200:
                content = response.read().decode('utf-8', errors='ignore')
                print(f"✅ 获取成功，内容长度: {len(content)} 字符")
                print(f"✅ 内容前100字符: {content[:100]}...")
                return content
            else:
                print(f"❌ 获取失败，状态码: {response.status}")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
    return None

def main():
    print("开始测试直播源获取功能...")
    start_time = time.time()
    
    # 测试GitHub API
    test_github_api()
    
    # 测试几个关键直播源
    test_sources = [
        ("https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u", "4K.m3u"),
        ("https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u", "HDTV.m3u"),
        ("https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_400.txt", "IPTV_400.txt"),
    ]
    
    success_count = 0
    for url, name in test_sources:
        content = test_live_source(url, name)
        if content:
            success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"总测试数: {len(test_sources)}")
    print(f"成功数: {success_count}")
    print(f"成功率: {success_count / len(test_sources) * 100:.1f}%")
    print(f"总耗时: {time.time() - start_time:.2f} 秒")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
