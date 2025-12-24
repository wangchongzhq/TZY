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
            # 标准格式：#EXTINF:-1 ... tvg-name="频道名" ... group-title="分组名",频道显示名
            # 仅匹配EXTINF行，不包含URL
            r"#EXTINF:[^\n]+?tvg-name=[\"']?([^\"']+)[\"']?[^\n]*?group-title=[\"']?([^\"']+)[\"']?[^\n]*?,([^\n]+)",
            # 简化格式：#EXTINF:-1 ... tvg-name="频道名" ...,频道显示名（没有分组）
            r"#EXTINF:[^\n]+?tvg-name=[\"']?([^\"']+)[\"']?[^\n]*?,([^\n]+)",
            # 极简格式：#EXTINF:-1,频道显示名
            r"#EXTINF:[^\n]+?,([^\n]+)",
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
        processed_channels = set()  # 用于跟踪已处理的频道URL组合
        
        # 按行处理内容，确保每个频道只被处理一次
        lines = content.split('\n')
        i = 0
        total_matches = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF:'):
                # 找到一个频道开始行
                extinf_line = line
                j = i + 1
                urls_text = []
                
                # 收集后续的URL行，直到遇到下一个EXTINF或文件结束
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#'):
                        urls_text.append(next_line)
                    elif next_line.startswith('#EXTINF:'):
                        break
                    j += 1
                
                if urls_text:
                    urls = urls_text
                    total_matches += 1
                    
                    # 尝试匹配不同的格式
                    match = None
                    pattern_used = None
                    
                    # 先尝试最具体的模式
                    for pattern in self.patterns:
                        full_match = re.match(pattern, extinf_line, re.DOTALL)
                        if full_match:
                            match = full_match.groups()
                            pattern_used = pattern
                            break
                    
                    if match:
                        if len(match) == 3:
                            # 标准格式：tvg_name, group_title, channel_name
                            tvg_name, group_title, channel_name = match
                            # 如果频道显示名为空，使用tvg_name
                            if not channel_name.strip():
                                channel_name = tvg_name
                        elif len(match) == 2:
                            # 简化格式：tvg_name, channel_name
                            tvg_name, channel_name = match
                            group_title = ""
                        else:
                            # 极简格式：channel_name
                            channel_name = match[0]
                            tvg_name = channel_name
                            group_title = ""
                        
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
                        
                        # 为每个URL创建一行，确保每个URL都包含对应的频道名称
                        for url in urls:
                            url = url.strip()
                            if url:
                                channel_line = f"{channel_name},{url}"
                                # 使用URL作为唯一标识，避免重复处理相同的频道URL组合
                                if url not in processed_channels:
                                    processed_channels.add(url)
                                    group_channels[group_title].append(channel_line)
                
                # 跳过已处理的行
                i = j
            else:
                i += 1
        
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
    if len(sys.argv) >= 2:
        # 至少提供了一个参数，使用它作为输入文件
        m3u_file = sys.argv[1]
        if len(sys.argv) == 3:
            # 提供了两个参数，使用第二个作为输出文件
            txt_file = sys.argv[2]
        # 如果只提供了一个参数，后面会根据输入文件名自动生成输出文件名
    else:
        # 没有提供参数，查找当前目录下的所有M3U文件
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
