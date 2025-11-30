#!/usr/bin/env python3
"""
转换工具：将M3U格式转换为TXT格式
功能：合并了原convert_to_txt.py和convert_to_txtauto.py的功能
支持按分组组织频道或简单列表格式
"""

import os
import re
import datetime
from collections import defaultdict

def convert_m3u_to_txt(m3u_file_path, txt_file_path, group_by_category=True):
    """
    将M3U文件转换为TXT格式
    
    参数：
    m3u_file_path: 输入的M3U文件路径
    txt_file_path: 输出的TXT文件路径
    group_by_category: 是否按分类组织频道
    
    返回：
    转换是否成功
    """
    print(f"🔄 开始将 {m3u_file_path} 转换为 {txt_file_path}...")
    
    if not os.path.exists(m3u_file_path):
        print(f"❌ 输入文件不存在: {m3u_file_path}")
        return False
    
    try:
        with open(m3u_file_path, 'r', encoding='utf-8') as m3u:
            content = m3u.read()
    except UnicodeDecodeError:
        try:
            with open(m3u_file_path, 'r', encoding='gbk') as m3u:
                content = m3u.read()
        except Exception as e:
            print(f"❌ 读取文件时编码错误: {e}")
            return False
    except Exception as e:
        print(f"❌ 读取文件时出错: {e}")
        return False

    if group_by_category:
        # 使用正则表达式匹配每个频道块（支持分组）
        pattern = r'#EXTINF:.*?tvg-name="([^"]*)".*?group-title="([^"]*)",([^\n]+)\n((?:http[^\n]+\n)*)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        group_channels = {}
        total_channels = 0
        
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
                    total_channels += 1
        
        # 写入TXT文件（按分组）
        try:
            with open(txt_file_path, 'w', encoding='utf-8') as txt:
                # 写入文件头部
                txt.write("# IPTV直播源 - 从M3U转换\n")
                txt.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txt.write(f"# 源文件: {m3u_file_path}\n")
                txt.write(f"# 总频道数: {total_channels}\n")
                txt.write("# 格式: 频道名称,播放URL\n\n")
                
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
            
            print(f"✅ 转换完成！按分组组织频道")
            print(f"📊 转换了 {total_channels} 个频道，分为 {len(group_channels)} 个分组")
            return True
            
        except Exception as e:
            print(f"❌ 写入文件时出错: {e}")
            return False
    else:
        # 简单模式：不按分组，直接列出所有频道
        lines = content.split('\n')
        channels = []
        current_channel = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # 提取频道名称
                if ',' in line:
                    current_channel = line.split(',')[-1].strip()
            elif line and not line.startswith('#') and current_channel:
                # 这是URL行
                channels.append((current_channel, line))
                current_channel = None
        
        # 写入TXT文件
        try:
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write("# IPTV直播源 - 从M3U转换\n")
                f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 源文件: {m3u_file_path}\n")
                f.write(f"# 总频道数: {len(channels)}\n")
                f.write("# 格式: 频道名称,播放URL\n\n")
                
                for channel_name, url in channels:
                    f.write(f"{channel_name},{url}\n")
        
            print(f"✅ 转换完成！简单列表格式")
            print(f"📊 转换了 {len(channels)} 个频道")
            return True
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            return False

def main():
    """主函数"""
    m3u_file = "ipzy.m3u"  # 输入的M3U文件
    txt_file = "ipzyauto.txt"  # 输出的TXT文件
    
    if not os.path.exists(m3u_file):
        print(f"❌ 输入文件 {m3u_file} 不存在")
        return
    
    if convert_m3u_to_txt(m3u_file, txt_file, group_by_category=True):
        print(f"🎉 成功生成TXT文件: {txt_file}")
    else:
        print("💥 转换失败")

if __name__ == "__main__":
    main()
