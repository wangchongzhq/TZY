# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
绮剧畝IP-TV.py鏂囦欢鐨勮剼鏈?"""

def simplify_file():
    with open('IP-TV.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    simplified_lines = []
    blank_line_count = 0
    
    for line in lines:
        # 绉婚櫎琛屽熬绌虹櫧瀛楃
        line = line.rstrip()
        
        # 濡傛灉鏄┖琛岋紝璁℃暟浣嗕笉绔嬪嵆娣诲姞
        if not line:
            blank_line_count += 1
            # 鏈€澶氫繚鐣欎竴涓繛缁┖鐧借
            if blank_line_count <= 1:
                simplified_lines.append("\n")
            continue
        else:
            blank_line_count = 0
        
        # 1. 绉婚櫎涓嶅繀瑕佺殑瀵煎叆
        if line.strip() in ['import os', 'import threading']:
            continue
        
        # 2. 绉婚櫎debug绾у埆鏃ュ織
        if 'logger.debug(' in line:
            continue
        
        # 3. 淇濈暀鍏朵粬鍐呭
        simplified_lines.append(line + "\n")
    
    # 淇濆瓨绮剧畝鍚庣殑鏂囦欢
    with open('IP-TV_simplified.py', 'w', encoding='utf-8') as f:
        f.writelines(simplified_lines)
    
    print("鏂囦欢绮剧畝瀹屾垚锛屽凡淇濆瓨涓?IP-TV_simplified.py")

if __name__ == "__main__":
    simplify_file()
