#!/usr/bin/env python3
"""
测试配置文件加载功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from IPTV import load_config, config

if __name__ == "__main__":
    print("🔍 开始测试配置文件加载功能")
    
    # 加载配置文件
    load_config()
    
    # 打印配置内容
    print("✅ 配置文件加载成功")
    print("\n📋 加载的配置内容：")
    print(f"🔹 分辨率过滤：{'开启' if config['filter']['resolution'] else '关闭'}")
    print(f"🔹 最小分辨率：{config['filter']['min_resolution']}")
    print(f"🔹 只获取4K频道：{'开启' if config['filter']['only_4k'] else '关闭'}")
    print(f"🔹 URL测试：{'开启' if config['url_testing']['enable'] else '关闭'}")
    print(f"🔹 URL超时时间：{config['url_testing']['timeout']}秒")
    print(f"🔹 URL测试并发数：{config['url_testing']['workers']}")
    print(f"🔹 缓存有效期：{config['cache']['expiry_time']}秒")
    print(f"🔹 缓存文件：{config['cache']['file']}")
    print(f"🔹 M3U输出文件：{config['output']['m3u_file']}")
    print(f"🔹 TXT输出文件：{config['output']['txt_file']}")
    
    # 验证配置是否被正确覆盖
    print("\n📊 配置覆盖验证：")
    if config['cache']['expiry_time'] == 7200:
        print("✅ 缓存有效期已从默认的3600秒修改为7200秒")
    else:
        print("❌ 缓存有效期配置未被正确覆盖")
        
    if config['output']['m3u_file'] == "iptv_channels.m3u":
        print("✅ M3U输出文件已从默认的jieguo.m3u修改为iptv_channels.m3u")
    else:
        print("❌ M3U输出文件配置未被正确覆盖")
    
    if config['url_testing']['workers'] == 64:
        print("✅ URL测试并发数已从默认的128修改为64")
    else:
        print("❌ URL测试并发数配置未被正确覆盖")
    
    print("\n🎉 配置文件加载测试完成")
