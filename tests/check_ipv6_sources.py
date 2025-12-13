# 直接检查IPv6源内容
import requests

# 检查指定URL是否包含4K频道
def check_source(url):
    print(f"\n检查源: {url}")
    try:
        # 使用更宽松的请求设置
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, verify=False, headers=headers)
        response.encoding = response.apparent_encoding
        content = response.text
        
        # 检查是否包含4K相关内容
        if any(keyword in content for keyword in ["4K", "4k", "8K", "8k", "超高清", "2160"]):
            print(f"  ✓ 发现4K相关内容")
            
            # 提取可能的4K频道
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in ["4K", "4k", "8K", "8k", "超高清", "2160"]):
                    # 显示上下文
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    print(f"\n    上下文 ({i+1}行):")
                    for j in range(start, end):
                        print(f"    {j+1:4d}: {lines[j]}")
        else:
            print(f"  ✗ 未发现4K相关内容")
            
        # 检查是否包含IPv6地址
        if '[' in content:
            print(f"  ✓ 发现IPv6地址")
            
            # 提取几个IPv6地址示例
            ipv6_count = content.count('[')
            print(f"    估计有 {ipv6_count} 个IPv6地址")
        else:
            print(f"  ✗ 未发现IPv6地址")
            
    except Exception as e:
        print(f"  ✗ 发生错误: {e}")

# 测试主要的IPv6源
ipv6_sources = [
    "https://ghfast.top/https://raw.githubusercontent.com/kakaxi-1/IPTV/main/ipv6.m3u",
]

print("检查IPv6源中的4K频道")
print("=" * 50)

for url in ipv6_sources:
    check_source(url)

print("\n" + "=" * 50)
print("检查完成")
