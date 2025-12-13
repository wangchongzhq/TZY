#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网络模块功能
"""

import sys
import time
import asyncio

# 添加项目根目录到路径
sys.path.append('.')

# 导入网络模块
from core.network import (
    fetch_content, fetch_multiple, async_fetch_content, async_fetch_multiple,
    is_streaming_url, clear_cache, check_url_availability
)

async def main():
    """主测试函数"""
    print("=== 测试网络模块功能 ===\n")
    
    # 测试1: 单个URL请求
    print("1. 测试单个URL请求:")
    try:
        result = fetch_content('https://example.com', retries=2)
        if result:
            print(f"   ✓ example.com: 成功获取，长度: {len(result)}字符")
        else:
            print(f"   ✗ example.com: 获取失败")
    except Exception as e:
        print(f"   ✗ example.com: 发生错误 - {e}")
    
    # 测试2: 缓存机制
    print("\n2. 测试缓存机制:")
    try:
        start_time = time.time()
        result2 = fetch_content('https://example.com')
        cache_time = time.time() - start_time
        if result2:
            print(f"   ✓ example.com (缓存): 成功获取，长度: {len(result2)}字符")
            print(f"   ✓ 缓存响应时间: {cache_time:.3f}秒")
        else:
            print(f"   ✗ example.com (缓存): 获取失败")
    except Exception as e:
        print(f"   ✗ 缓存测试: 发生错误 - {e}")
    
    # 测试3: 流媒体URL检查
    print("\n3. 测试流媒体URL检查:")
    test_urls = [
        ('https://example.com', False),
        ('https://example.com/test.m3u8', True),
        ('https://example.com/video.mp4', True),
    ]
    
    for url, expected in test_urls:
        try:
            result = is_streaming_url(url)
            status = "✓" if result == expected else "✗"
            print(f"   {status} {url}: {result} {'(正确)' if result == expected else '(错误，期望: ' + str(expected) + ')'}")
        except Exception as e:
            print(f"   ✗ {url}: 发生错误 - {e}")
    
    # 测试4: 并发请求
    print("\n4. 测试并发请求:")
    urls = ['https://example.com', 'https://httpbin.org/get']
    try:
        start_time = time.time()
        results = fetch_multiple(urls)
        elapsed_time = time.time() - start_time
        print(f"   ✓ 并发请求完成，耗时: {elapsed_time:.2f}秒")
        for url, result in results.items():
            if result:
                print(f"     ✓ {url}: {len(result)}字符")
            else:
                print(f"     ✗ {url}: 获取失败")
    except Exception as e:
        print(f"   ✗ 并发请求: 发生错误 - {e}")
    
    # 测试5: 异步并发请求
    print("\n5. 测试异步并发请求:")
    import aiohttp
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async_results = await async_fetch_multiple(urls)
            elapsed_time = time.time() - start_time
            print(f"   ✓ 异步并发请求完成，耗时: {elapsed_time:.2f}秒")
            for url, result in async_results.items():
                if result:
                    print(f"     ✓ {url}: {len(result)}字符")
                else:
                    print(f"     ✗ {url}: 获取失败")
        except Exception as e:
            print(f"   ✗ 异步并发请求: 发生错误 - {e}")
    
    # 测试6: URL可用性检查
    print("\n6. 测试URL可用性检查:")
    try:
        result = check_url_availability('https://example.com', timeout=5)
        print(f"   ✓ example.com: 可用={result['available']}, Content-Type={result['content_type']}, 状态码={result['status_code']}")
    except Exception as e:
        print(f"   ✗ URL可用性检查: 发生错误 - {e}")
    
    # 清理缓存
    clear_cache()
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n测试被中断")
    except Exception as e:
        print(f"\n测试发生严重错误: {e}")
        import traceback
        traceback.print_exc()
