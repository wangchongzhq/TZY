# convert_to_txt.py

import re
import os

def convert_m3u_to_txt(m3u_file_path, txt_file_path):
    """
    将M3U文件转换为TXT格式，格式为：
    分组名称,#genre#
    频道名称,URL1
    频道名称,URL2
    """
    if not os.path.exists(m3u_file_path):
        return False
    
    try:
        with open(m3u_file_path, 'r', encoding='utf-8') as m3u:
            content = m3u.read()
    except UnicodeDecodeError:
        try:
            with open(m3u_file_path, 'r', encoding='gbk') as m3u:
                content = m3u.read()
        except:
            return False

    # 使用正则表达式匹配每个频道块
    pattern = r'#EXTINF:.*?tvg-name="([^"]*)".*?group-title="([^"]*)",([^\n]+)\n((?:http[^\n]+\n)*)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    group_channels = {}
    
    for match in matches:
        tvg_name = match[0]  # tvg-name
        group_title = match[1]  # group-title
        channel_name = match[2]  # 显示名称
        urls_text = match[3]  # 所有URL
        
        # 提取所有URL（每行一个URL）
        urls = re.findall(r'(http[^\s\n]+)', urls_text)
        
        if group_title not in group_channels:
            group_channels[group_title] = []
        
        # 为每个URL创建一行
        for url in urls:
            # 清理URL
            url = url.strip()
            if url:
                # 格式：频道名称,URL
                group_channels[group_title].append(f"{channel_name},{url}")
    
    # 写入TXT文件
    try:
        with open(txt_file_path, 'w', encoding='utf-8') as txt:
            # 按分组名称排序，让输出更整齐
            for group in sorted(group_channels.keys()):
                channels = group_channels[group]
                if channels:  # 只写入有频道的分组
                    # 写入分组标题
                    txt.write(f"{group},#genre#\n")
                    # 写入该分组下的所有频道URL
                    for channel_line in channels:
                        txt.write(f"{channel_line}\n")
                    # 分组之间空一行
                    txt.write("\n")
        
        return True
        
    except:
        return False

def main():
    """主函数"""
    m3u_file = "ipzy.m3u"
    txt_file = "ipzyauto.txt"  # 修改为ipzyauto.txt
    
    if not os.path.exists(m3u_file):
        return
    
    convert_m3u_to_txt(m3u_file, txt_file)

if __name__ == "__main__":
    main()
