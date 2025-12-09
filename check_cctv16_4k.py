import re
import sys

# 设置编码为utf-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def check_cctv16_4k():
    """检查生成的文件中是否包含CCTV16 4K频道"""
    print("=== 检查CCTV16 4K频道 ===")
    
    # 检查jieguo.m3u文件
    try:
        with open('jieguo.m3u', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 搜索CCTV16相关内容
        cctv16_pattern = re.compile(r'CCTV16.*4K|4K.*CCTV16|CCTV16.*\(4K\)', re.IGNORECASE)
        cctv16_matches = cctv16_pattern.findall(content)
        
        print(f"\n1. jieguo.m3u中找到的CCTV16 4K相关匹配:")
        if cctv16_matches:
            for match in set(cctv16_matches):  # 使用set去重
                print(f"   - {match}")
        else:
            print("   没有找到CCTV16 4K相关频道")
        
        # 统计所有CCTV16频道
        all_cctv16_pattern = re.compile(r'CCTV16[\w\W]*?\n[^#]', re.IGNORECASE)
        all_cctv16_matches = all_cctv16_pattern.findall(content)
        print(f"\n2. jieguo.m3u中所有CCTV16频道数量: {len(all_cctv16_matches)}")
        
        # 查看前几个CCTV16频道的完整信息
        print(f"\n3. 前5个CCTV16频道的完整信息:")
        for i, match in enumerate(all_cctv16_matches[:5]):
            print(f"   {i+1}. {match.strip()}")
            
    except Exception as e:
        print(f"读取jieguo.m3u时出错: {e}")
    
    # 检查4K频道分组
    try:
        with open('jieguo.m3u', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 搜索4K频道分组
        group_pattern = re.compile(r'group-title=["\'].*4K.*["\']', re.IGNORECASE)
        group_matches = group_pattern.findall(content)
        
        print(f"\n4. 4K相关的频道分组:")
        if group_matches:
            for group in set(group_matches):  # 使用set去重
                print(f"   - {group}")
        
        # 统计4K频道数量
        channel_pattern = re.compile(r'group-title=["\'].*4K.*["\'].*?\n[^#]', re.IGNORECASE | re.DOTALL)
        channel_matches = channel_pattern.findall(content)
        print(f"\n5. 4K频道总数: {len(channel_matches)}")
        
    except Exception as e:
        print(f"检查4K频道时出错: {e}")

if __name__ == "__main__":
    check_cctv16_4k()