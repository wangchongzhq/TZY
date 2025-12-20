#!/usr/bin/env python3
"""
增量更新机制测试脚本
"""

import sys
import os
from IPTV import load_config, fetch_m3u_content, save_cache, source_cache

# 加载配置
load_config()

# 测试URL
TEST_URL = "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv4.txt"

print("开始测试增量更新机制...")
print(f"测试URL: {TEST_URL}")

# 第一次获取内容
print("\n1. 第一次获取内容...")
content1 = fetch_m3u_content(TEST_URL)
if content1:
    print(f"✅ 成功获取内容，长度: {len(content1)} 字符")
    print(f"✅ 缓存条目: {TEST_URL in source_cache}")
    if TEST_URL in source_cache:
        cached_time, cached_content, etag, last_modified = source_cache[TEST_URL]
        print(f"✅ 缓存信息 - 时间: {cached_time}, ETag: {etag}, Last-Modified: {last_modified}")
else:
    print("❌ 获取内容失败")
    sys.exit(1)

# 保存缓存
print("\n2. 保存缓存到文件...")
save_cache()
if os.path.exists("source_cache.json"):
    print("✅ 缓存文件已创建")
    with open("source_cache.json", "r", encoding="utf-8") as f:
        cache_content = f.read()
        print(f"✅ 缓存文件大小: {len(cache_content)} 字符")
else:
    print("❌ 缓存文件创建失败")

# 第二次获取内容（应该使用缓存或增量更新）
print("\n3. 第二次获取内容（测试增量更新）...")
content2 = fetch_m3u_content(TEST_URL)
if content2:
    print(f"✅ 成功获取内容，长度: {len(content2)} 字符")
    print(f"✅ 内容是否相同: {content1 == content2}")
else:
    print("❌ 获取内容失败")
    sys.exit(1)

print("\n✅ 增量更新机制测试完成！")
