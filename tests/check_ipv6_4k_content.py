import requests

# 检查IPv6源是否包含4K频道
ipv6_sources = [
    "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u",
    "https://ghfast.top/https://raw.githubusercontent.com/Heiwk/iptv67/refs/heads/main/iptv.m3u",
]

for url in ipv6_sources:
    print(f"\n{'='*50}")
    print(f"检查源: {url}")
    print('='*50)
    
    try:
        response = requests.get(url, timeout=30)
        content = response.text
        
        # 检查4K相关内容
        has_4k = any(keyword in content for keyword in ['4K', '4k', '8K', '8k', '超高清', '2160'])
        has_ipv6 = '[' in content
        
        print(f"源长度: {len(content)} 字符")
        print(f"包含4K内容: {'是' if has_4k else '否'}")
        print(f"包含IPv6地址: {'是' if has_ipv6 else '否'}")
        
        if has_4k:
            print("\n4K相关内容:")
            lines = content.split('\n')
            found = 0
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in ['4K', '4k', '8K', '8k', '超高清', '2160']):
                    print(f"  行 {i+1}: {line.strip()}")
                    found += 1
                    if found >= 5:  # 最多显示5条
                        break
        
    except Exception as e:
        print(f"错误: {e}")

print("\n检查完成")
