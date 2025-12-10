import requests
import re
import sys

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def test_4k_source():
    """测试用户提到的4K频道源"""
    url = "https://ghproxy.it/https://raw.githubusercontent.com/qingtingjjjjjjj/Web-Scraping/main/live.txt"
    print(f"正在获取源: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        content = response.text
        
        print(f"\n源文件大小: {len(content)} 字符")
        
        # 查找4K频道
        lines = content.split('\n')
        print(f"\n源文件总行数: {len(lines)}")
        
        # 查找4K频道
        found_4k = False
        print("\n找到的4K频道:")
        
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#'):
                if '4K' in line or '4k' in line:
                    print(f"  {line.strip()}")
                    found_4k = True
        
        if not found_4k:
            print("  未找到明确标记为4K的频道")
            
        # 查找频道分类标记
        print("\n源文件中的分类标记:")
        for i, line in enumerate(lines):
            if '#genre#' in line:
                print(f"  第{i+1}行: {line.strip()}")
        
        # 检查文件格式
        print("\n源文件前20行:")
        for i, line in enumerate(lines[:20]):
            print(f"  {i+1}: {line}")
            
    except Exception as e:
        print(f"获取源文件失败: {e}")

if __name__ == "__main__":
    test_4k_source()
