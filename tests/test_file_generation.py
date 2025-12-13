# -*- coding: utf-8 -*-
import os
import sys

# 模拟ipzyauto.py的文件生成过程
def test_file_generation():
    print("测试文件生成...")
    
    # 创建一个简单的M3U文件
    m3u_content = "#EXTM3U\n#EXTINF:-1,CCTV1\nhttp://example.com/cctv1.m3u8\n"
    with open("ipzyauto.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print("已创建ipzyauto.m3u文件")
    
    # 创建一个简单的TXT文件
    txt_content = "CCTV1,http://example.com/cctv1.m3u8\n"
    with open("ipzyauto.txt", "w", encoding="utf-8") as f:
        f.write(txt_content)
    print("已创建ipzyauto.txt文件")
    
    # 检查文件是否存在
    if os.path.exists("ipzyauto.m3u") and os.path.exists("ipzyauto.txt"):
        print("文件生成成功！")
        
        # 显示文件内容
        print("\nipzyauto.m3u内容：")
        with open("ipzyauto.m3u", "r", encoding="utf-8") as f:
            print(f.read())
        
        print("\nipzyauto.txt内容：")
        with open("ipzyauto.txt", "r", encoding="utf-8") as f:
            print(f.read())
        
        # 删除测试文件
        os.remove("ipzyauto.m3u")
        os.remove("ipzyauto.txt")
        print("\n已删除测试文件")
    else:
        print("文件生成失败！")

if __name__ == "__main__":
    test_file_generation()