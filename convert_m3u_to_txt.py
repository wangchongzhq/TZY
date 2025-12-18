#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_m3u_to_txt.py

将M3U格式的直播源转换为TXT格式的直播源
"""

import re
from datetime import datetime

class M3UConverter:
    """M3U文件转换器类"""
    
    def __init__(self):
        """初始化M3U转换器"""
        # 支持的编码格式列表，按优先级排序
        self.encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'iso-8859-1']
        # 改进的正则表达式模式，支持更多M3U格式变体
        self.patterns = [
            # 标准格式：#EXTINF:-1 tvg-name="频道名" group-title="分组名",频道显示名
            r"#EXTINF:[^\n]+?tvg-name=[\"']?([^\s\"']+)[\"']?[^\n]*?group-title=[\"']?([^\s\"']+)[\"']?[^\n]*?,([^\n]+)\n((?:http[^\s\n]+\n*)+)",
            # 简化格式：#EXTINF:-1 tvg-name="频道名",频道显示名（没有分组）
            r"#EXTINF:[^\n]+?tvg-name=[\"']?([^\s\"']+)[\"']?[^\n]*?,([^\n]+)\n((?:http[^\s\n]+\n*)+)",
            # 极简格式：#EXTINF:-1,频道显示名
            r"#EXTINF:[^\n]+?,([^\n]+)\n((?:http[^\s\n]+\n*)+)",
        ]
    
    def read_file_with_encoding(self, file_path):
        """尝试使用多种编码读取文件"""
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        return None, None
    
    def parse_m3u_content(self, content):
        """解析M3U内容，提取频道信息"""
        group_channels = {}
        total_matches = 0
        processed_entries = set()  # 跟踪已处理的频道URL组合，避免重复
        
        # 尝试不同的正则表达式模式
        for pattern in self.patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            if matches:
                total_matches += len(matches)
                
                for match in matches:
                    if len(match) == 4:
                        # 标准格式：tvg_name, group_title, channel_name, urls_text
                        tvg_name, group_title, channel_name, urls_text = match
                        # 如果频道显示名为空，使用tvg_name
                        if not channel_name.strip():
                            channel_name = tvg_name
                    elif len(match) == 3:
                        # 简化格式：tvg_name, channel_name, urls_text
                        tvg_name, channel_name, urls_text = match
                        group_title = ""
                    else:
                        # 极简格式：channel_name, urls_text
                        channel_name, urls_text = match
                        tvg_name = channel_name
                        group_title = ""
                    
                    # 提取所有URL
                    urls = re.findall(r'(http[^\s\n]+)', urls_text)
                    
                    # 清理数据
                    tvg_name = tvg_name.strip()
                    group_title = group_title.strip()
                    channel_name = channel_name.strip()
                    
                    # 使用频道显示名作为主要名称，如果为空则使用tvg_name
                    if not channel_name:
                        channel_name = tvg_name
                    
                    # 保持原有的分组信息，不添加额外分组
                    group_title = group_title.strip()
                    # 如果没有分组信息，保持为空字符串
                    if not group_title:
                        group_title = ""
                    
                    # 添加到分组
                    if group_title not in group_channels:
                        group_channels[group_title] = []
                    
                    # 为每个URL创建一行，确保每个URL都包含对应的频道名称，避免重复
                    for url in urls:
                        url = url.strip()
                        if url:
                            entry_key = f"{channel_name},{url}"
                            if entry_key not in processed_entries:
                                group_channels[group_title].append(entry_key)
                                processed_entries.add(entry_key)
        
        return group_channels, total_matches
    
    def convert_m3u_to_txt(self, m3u_file_path, txt_file_path):
        """将M3U文件转换为TXT格式"""
        try:
            # 检查文件是否存在
            with open(m3u_file_path, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            return False
        
        # 检查文件是否为空
        import os
        file_size = os.path.getsize(m3u_file_path)
        if file_size == 0:
            return False
        
        # 读取文件内容
        content, used_encoding = self.read_file_with_encoding(m3u_file_path)
        if content is None:
            return False
        
        # 解析M3U内容
        group_channels, total_matches = self.parse_m3u_content(content)
        
        if total_matches == 0:
            return False
        
        # 统计信息
        total_groups = len([g for g in group_channels if group_channels[g]])
        total_sources = sum(len(channels) for channels in group_channels.values())
        
        # 生成输出内容
        output_lines = []
        
        # 添加文件头信息
        output_lines.append(f"# M3U Conversion Result - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"# Source File: {os.path.basename(m3u_file_path)}")
        output_lines.append(f"# Groups: {total_groups}, Total Sources: {total_sources}")
        output_lines.append("")
        
        # 添加频道信息
        for group, channels in sorted(group_channels.items()):
            if channels:  # 只写入有频道的分组
                if group:  # 只有当分组名称非空时才写入分组标题
                    output_lines.append(f"{group},#genre#")
                # 写入该分组下的所有频道URL
                for channel_line in channels:
                    output_lines.append(channel_line)
                # 分组之间空一行
                output_lines.append("")
        
        # 写入TXT文件
        try:
            with open(txt_file_path, 'w', encoding='utf-8-sig') as txt:  # 使用utf-8-sig确保Windows正确识别
                for line in output_lines:
                    txt.write(line + '\n')
            
            return True
                
        except Exception:
            return False
    


def main():
    """主函数"""
    import sys
    import os
    
    # 创建转换器实例
    converter = M3UConverter()
    
    # 尝试找到M3U文件
    possible_m3u_files = ["iptv.m3u", "cn.m3u", "4K.m3u", "ipvym3a", "iptv.m3a"]
    m3u_file = None
    txt_file = "output.txt"
    
    # 检查命令行参数
    if len(sys.argv) == 3:
        m3u_file = sys.argv[1]
        txt_file = sys.argv[2]
    else:
        # 获取当前目录下所有M3U文件
        all_m3u_files = [f for f in os.listdir('.') if f.lower().endswith(('.m3u', '.m3a'))]
        
        if all_m3u_files:
            # 检查每个文件是否为空
            valid_m3u_files = [f for f in all_m3u_files if os.path.getsize(f) > 0]
            
            if valid_m3u_files:
                # 选择第一个有效文件
                m3u_file = valid_m3u_files[0]
    
    if not m3u_file:
        sys.exit(1)
    
    # 根据输入文件自动生成输出文件名
    if m3u_file:
        txt_file = f"{os.path.splitext(m3u_file)[0]}.txt"
    else:
        txt_file = "output.txt"
    
    # 执行转换
    success = converter.convert_m3u_to_txt(m3u_file, txt_file)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
