#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_m3u_to_txt.py

M3U/TXT格式双向转换工具
支持 M3U → TXT 和 TXT → M3U 双向转换
"""

import re
import argparse
import os
import sys
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
                        elif len(match) == 2:
                            # 简化格式：tvg_name, channel_name
                            tvg_name, channel_name = match
                            group_title = ""
                        else:
                            # 极简格式：channel_name
                            channel_name = match[0]
                            tvg_name = match[0]  # 没有tvg-name时，使用频道显示名
                            group_title = ""
                        
                        # 清理数据，保持原始频道名称不变
                        tvg_name = tvg_name.strip() if tvg_name else ""
                        group_title = group_title.strip() if group_title else ""
                        channel_name = channel_name.strip() if channel_name else ""
                        
                        # 如果没有频道显示名，使用tvg-name作为频道显示名
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
                        
                        # 为每个URL创建一行，只包含频道显示名和URL，不包含分组名
                        for url in urls:
                            url = url.strip()
                            if url:
                                # 格式: 频道显示名,URL （不包含分组名）
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
    
    def convert_txt_to_m3u(self, txt_file_path, m3u_file_path):
        """将TXT格式转换为M3U格式"""
        try:
            # 读取TXT文件
            content, _ = self.read_file_with_encoding(txt_file_path)
            if not content:
                return False
                
            lines = content.strip().split('\n')
            output_lines = ['#EXTM3U']
            
            current_group = ""  # 当前分组名称
            
            for line in lines:
                original_line = line  # 保存原始行
                line = line.strip()
                if not line:
                    continue
                
                # 处理分组标记行 (凡是每行的结尾是,#genre# 或 ,genre#，都看作频道分类)
                if line.endswith(',#genre#') or line.endswith(',genre#'):
                    # 提取分组名：去掉相应的后缀
                    if line.endswith(',#genre#'):
                        group_name = line[:-8].strip()  # 去掉 ",#genre#" (8个字符)
                    elif line.endswith(',genre#'):
                        group_name = line[:-7].strip()  # 去掉 ",genre#" (7个字符)
                    
                    # 清理前后的#符号
                    while group_name.startswith('#'):
                        group_name = group_name[1:].strip()
                    while group_name.endswith('#'):
                        group_name = group_name[:-1].strip()
                    
                    # 清理BOM字符和其他不可见字符
                    group_name = group_name.replace('﻿', '').replace('\ufeff', '').strip()
                    current_group = group_name
                    continue
                
                # 跳过注释行（以#开头的行） - 但要确保分类行已经处理过了
                if line.startswith('#'):
                    continue
                
                # 解析TXT格式: 频道名,http://xxx 或 频道名|http://xxx
                if ',' in line:
                    parts = line.split(',', 1)  # 只分割第一个逗号
                    if len(parts) == 2:
                        # 格式: 频道名,http://xxx
                        channel_name = parts[0].strip()
                        url = parts[1].strip()
                    else:
                        continue  # 跳过不正确的格式
                elif '|' in line:
                    parts = line.split('|', 1)  # 只分割第一个管道符
                    if len(parts) == 2:
                        channel_name = parts[0].strip()
                        url = parts[1].strip()
                    else:
                        continue  # 跳过不正确的格式
                else:
                    # 没有分隔符的行，跳过
                    continue
                
                # 构建EXTINF行，使用当前分组信息
                extinf_attrs = ['-1', f'tvg-name="{channel_name}"']
                if current_group:  # 如果有当前分组，添加group-title
                    extinf_attrs.append(f'group-title="{current_group}"')
                # 频道显示名保持原始名称
                extinf_line = f"#EXTINF:{','.join(extinf_attrs)},{channel_name}"
                
                output_lines.append(extinf_line)
                output_lines.append(url)
            
            # 写入M3U文件
            with open(m3u_file_path, 'w', encoding='utf-8') as f:
                for line in output_lines:
                    f.write(line + '\n')
            
            return True
            
        except Exception:
            return False
    


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='M3U/TXT双向转换工具')
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('output_file', nargs='?', help='输出文件路径（可选）')
    parser.add_argument('--direction', choices=['m3u_to_txt', 'txt_to_m3u'], 
                       help='转换方向: m3u_to_txt 或 txt_to_m3u')
    
    args = parser.parse_args()
    
    input_file = args.input_file
    output_file = args.output_file
    conversion_type = args.direction
    
    # 创建转换器实例
    converter = M3UConverter()
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)
    
    # 获取输入文件扩展名
    _, input_ext = os.path.splitext(input_file)
    input_ext = input_ext.lower()
    
    # 如果没有指定转换方向，根据输入文件自动判断
    if not conversion_type:
        if input_ext in ['.m3u', '.m3a']:
            conversion_type = 'm3u_to_txt'
        elif input_ext == '.txt':
            conversion_type = 'txt_to_m3u'
        else:
            print(f"错误: 无法从文件扩展名 '{input_ext}' 判断转换方向")
            print("请使用 --direction 参数明确指定转换方向")
            sys.exit(1)
    
    # 如果没有指定输出文件，使用原文件名但改变扩展名
    if not output_file:
        # 使用与输入文件相同的路径和文件名，但改变扩展名
        input_dir = os.path.dirname(input_file)
        input_name = os.path.splitext(os.path.basename(input_file))[0]
        
        if conversion_type == 'm3u_to_txt':
            # M3U -> TXT，保持文件名相同，只改变扩展名
            output_file = os.path.join(input_dir, f"{input_name}.txt")
        else:  # txt_to_m3u
            # TXT -> M3U，保持文件名相同，只改变扩展名
            output_file = os.path.join(input_dir, f"{input_name}.m3u")
    
    # 验证输入文件是否与指定的转换方向匹配
    if conversion_type == 'm3u_to_txt' and input_ext not in ['.m3u', '.m3a']:
        print(f"错误: 使用 --direction m3u_to_txt 时，输入文件必须是 .m3u 或 .m3a 格式")
        print(f"当前输入文件: {input_file} (扩展名: {input_ext})")
        sys.exit(1)
    elif conversion_type == 'txt_to_m3u' and input_ext != '.txt':
        print(f"错误: 使用 --direction txt_to_m3u 时，输入文件必须是 .txt 格式")
        print(f"当前输入文件: {input_file} (扩展名: {input_ext})")
        sys.exit(1)
    
    print(f"转换方向: {conversion_type}")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 执行转换
    success = False
    if conversion_type == 'm3u_to_txt':
        print("开始M3U → TXT转换...")
        success = converter.convert_m3u_to_txt(input_file, output_file)
    else:  # txt_to_m3u
        print("开始TXT → M3U转换...")
        success = converter.convert_txt_to_m3u(input_file, output_file)
    
    if success:
        print(f"转换成功！输出文件: {output_file}")
        print(f"文件大小: {os.path.getsize(output_file)} 字节")
    else:
        print("转换失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
