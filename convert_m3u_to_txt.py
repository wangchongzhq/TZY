#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_m3u_to_txt.py

将M3U格式的直播源转换为TXT格式的直播源
增强版：支持多种编码格式，更可靠的正则表达式匹配，完善的错误处理
"""

import re
import os
import sys
from datetime import datetime

class M3UConverter:
    """M3U文件转换器类"""
    
    def __init__(self, debug=True):
        """初始化M3U转换器
        
        Args:
            debug: 是否启用调试模式
        """
        self.debug = debug
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
        print("=== M3U转换器初始化完成 ===")
        print(f"调试模式: {'开启' if self.debug else '关闭'}")
        print(f"支持的编码: {', '.join(self.encodings)}")
    
    def read_file_with_encoding(self, file_path):
        """尝试使用多种编码读取文件"""
        print(f"=== 检测文件 {file_path} 的编码 ===")
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ 使用编码 '{encoding}' 成功读取文件")
                print(f"📄 文件名: {os.path.basename(file_path)}")
                print(f"🔤 编码: {encoding}")
                print(f"📏 文件大小: {len(content)} 字符")
                print(f"📖 行数: {len(content.splitlines())}")
                
                # 显示文件头信息（如果有）
                if '#EXTM3U' in content:
                    print("✅ 文件包含#EXTM3U标记，是有效的M3U文件")
                else:
                    print("⚠️ 文件不包含#EXTM3U标记，可能是简化格式")
                return content, encoding
            except UnicodeDecodeError:
                print(f"❌ 编码 '{encoding}' 解码失败，尝试下一个...")
            except Exception as e:
                print(f"❌ 读取文件时出错 ({encoding}): {e}")
        print("⚠️  所有编码尝试失败！")
        return None, None
    
    def parse_m3u_content(self, content):
        """解析M3U内容，提取频道信息"""
        group_channels = {}
        total_matches = 0
        
        print("\n=== 开始解析M3U内容 ===")
        # 尝试不同的正则表达式模式
        for pattern_idx, pattern in enumerate(self.patterns):
            print(f"\n🔍 尝试使用正则表达式模式 {pattern_idx + 1} 解析...")
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            if matches:
                print(f"✅ 找到 {len(matches)} 个匹配项")
                total_matches += len(matches)
                
                for match_idx, match in enumerate(matches):
                    if len(match) == 4:
                        # 标准格式：tvg_name, group_title, channel_name, urls_text
                        tvg_name, group_title, channel_name, urls_text = match
                        # 如果频道显示名为空，使用tvg_name
                        if not channel_name.strip():
                            channel_name = tvg_name
                    elif len(match) == 3:
                        # 简化格式：tvg_name, channel_name, urls_text
                        tvg_name, channel_name, urls_text = match
                        group_title = "默认分组"
                    else:
                        # 极简格式：channel_name, urls_text
                        channel_name, urls_text = match
                        tvg_name = channel_name
                        group_title = "默认分组"
                    
                    # 提取所有URL
                    urls = re.findall(r'(http[^\s\n]+)', urls_text)
                    
                    # 清理数据
                    tvg_name = tvg_name.strip()
                    group_title = group_title.strip()
                    channel_name = channel_name.strip()
                    
                    # 使用频道显示名作为主要名称，如果为空则使用tvg_name
                    if not channel_name:
                        channel_name = tvg_name
                    
                    # 确保分组名称存在
                    if not group_title:
                        group_title = "默认分组"
                    
                    # 添加到分组
                    if group_title not in group_channels:
                        group_channels[group_title] = []
                    
                    # 为每个URL创建一行，确保每个URL都包含对应的频道名称
                    for url in urls:
                        url = url.strip()
                        if url:
                            group_channels[group_title].append(f"{channel_name},{url}")
                            print(f"    📡 频道: {channel_name} -> URL: {url[:50]}{'...' if len(url) > 50 else ''}")
                    
                    # 显示前3个匹配项的详细信息
                    if match_idx < 3:
                        print(f"\n✅ 匹配项 {match_idx + 1}:")
                        print(f"  📺 频道名称: {channel_name}")
                        print(f"  🏷️  TVG名称: {tvg_name}")
                        print(f"  📁 分组: {group_title}")
                        print(f"  🔗 URL数量: {len(urls)}")
                        for j, url in enumerate(urls[:1]):  # 只显示第一个URL
                            print(f"    📡 URL {j+1}: {url[:100]}{'...' if len(url) > 100 else ''}")
                        if len(urls) > 1:
                            print(f"    ... 等 {len(urls) - 1} 个更多URL")
                    elif match_idx == 3:
                        print("... [省略中间匹配项]")
            else:
                print(f"❌ 没有找到匹配项")
        
        return group_channels, total_matches
    
    def convert_m3u_to_txt(self, m3u_file_path, txt_file_path):
        """将M3U文件转换为TXT格式"""
        print(f"\n🚀 开始转换：{m3u_file_path} -> {txt_file_path}")
        print(f"📅 开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 检查文件是否存在
        if not os.path.exists(m3u_file_path):
            print(f"❌ 错误：找不到M3U文件 {m3u_file_path}")
            return False
        
        # 检查文件是否为空
        file_size = os.path.getsize(m3u_file_path)
        if file_size == 0:
            print(f"❌ 错误：M3U文件 {m3u_file_path} 是空的")
            return False
        
        print(f"📁 文件信息：{m3u_file_path} ({file_size:,} 字节)")
        
        # 读取文件内容
        print("\n📖 正在读取文件内容...")
        content, used_encoding = self.read_file_with_encoding(m3u_file_path)
        if content is None:
            print("❌ 错误：无法解码M3U文件，尝试了所有支持的编码")
            return False
        
        # 解析M3U内容
        print("\n🔧 正在解析M3U内容...")
        group_channels, total_matches = self.parse_m3u_content(content)
        
        if total_matches == 0:
            print("❌ 错误：没有解析到任何频道信息，可能是M3U格式不支持")
            # 显示文件前几行，帮助调试
            print("\n📝 文件前20行内容：")
            lines = content.split('\n')[:20]
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line}")
            return False
        
        # 统计信息
        total_groups = len([g for g in group_channels if group_channels[g]])
        total_sources = sum(len(channels) for channels in group_channels.values())
        
        print(f"\n📊 解析统计：")
        print(f"  匹配的频道块数量：{total_matches}")
        print(f"  有效分组数量：{total_groups}")
        print(f"  总播放源数量：{total_sources}")
        
        # 显示分组详情
        print("\n📋 分组详细统计：")
        sorted_groups = sorted(group_channels.items(), key=lambda x: len(x[1]), reverse=True)
        for i, (group, channels) in enumerate(sorted_groups[:5]):
            if channels:
                print(f"  {i+1}. {group}: {len(channels)} 个播放源")
        if len(sorted_groups) > 5:
            print(f"  ... 等 {len(sorted_groups) - 5} 个更多分组")
        
        # 生成输出内容
        print("\n✍️  正在生成TXT文件内容...")
        output_lines = []
        
        # 添加文件头信息（使用英文避免编码问题）
        output_lines.append(f"# M3U Conversion Result - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"# Source File: {os.path.basename(m3u_file_path)}")
        output_lines.append(f"# Groups: {total_groups}, Total Sources: {total_sources}")
        output_lines.append("")
        
        # 添加频道信息
        for group, channels in sorted(group_channels.items()):
            if channels:  # 只写入有频道的分组
                # 写入分组标题
                output_lines.append(f"{group},#genre#")
                # 写入该分组下的所有频道URL
                for channel_line in channels:
                    output_lines.append(channel_line)
                # 分组之间空一行
                output_lines.append("")
        
        # 写入TXT文件
        print(f"\n💾 正在写入TXT文件...")
        try:
            with open(txt_file_path, 'w', encoding='utf-8-sig') as txt:  # 使用utf-8-sig确保Windows正确识别
                for line in output_lines:
                    txt.write(line + '\n')
            
            # 验证文件是否创建成功
            if os.path.exists(txt_file_path):
                output_size = os.path.getsize(txt_file_path)
                print(f"\n✅ 转换完成！")
                print(f"📁 输出文件：{txt_file_path}")
                print(f"📊 文件大小：{output_size:,} 字节")
                print(f"📝 输出行数：{len(output_lines)}")
                
                return True
            else:
                print(f"❌ 错误：文件创建失败，{txt_file_path} 不存在")
                return False
                
        except Exception as e:
            print(f"❌ 写入TXT文件时出错: {e}")
            import traceback
            print("错误详情:")
            traceback.print_exc()
            return False
    
    def debug_m3u_structure(self, file_path):
        """调试M3U文件结构"""
        print(f"\n🔍 正在分析M3U文件结构: {file_path}")
        
        content, encoding = self.read_file_with_encoding(file_path)
        if content is None:
            print("❌ 无法读取文件")
            return
        
        lines = content.split('\n')
        print(f"📝 文件总行数: {len(lines)}")
        print(f"🔤 使用编码: {encoding}")
        
        # 统计不同类型的行
        extinf_count = 0
        url_count = 0
        comment_count = 0
        empty_count = 0
        other_count = 0
        
        print("\n📋 文件结构预览（前30行）:")
        print("-" * 80)
        for i, line in enumerate(lines[:100]):  # 分析前100行
            line_stripped = line.strip()
            if line_stripped.startswith('#EXTINF:'):
                extinf_count += 1
                if i < 30:  # 只显示前30行的详细信息
                    # 提取关键信息
                    tvg_name_match = re.search(r'tvg-name=["\']?([^\s"\']+)["\']?', line_stripped)
                    group_title_match = re.search(r'group-title=["\']?([^\s"\']+)["\']?', line_stripped)
                    channel_name_match = re.search(r'#EXTINF:[^\n]*,([^\n]*)', line_stripped)
                    
                    tvg_name = tvg_name_match.group(1) if tvg_name_match else "未知"
                    group_title = group_title_match.group(1) if group_title_match else "未知"
                    channel_name = channel_name_match.group(1).strip() if channel_name_match else "未知"
                    
                    print(f"  {i+1:3d}: 📺 EXTINF -> TVG:{tvg_name}, 分组:{group_title}, 显示名:{channel_name}")
            elif line_stripped.startswith('http'):
                url_count += 1
                if i < 30:  # 只显示前30行的URL
                    print(f"  {i+1:3d}: 🔗 URL -> {line_stripped[:80]}{'...' if len(line_stripped) > 80 else ''}")
            elif line_stripped.startswith('#'):
                comment_count += 1
                if i < 30:  # 只显示前30行的注释
                    print(f"  {i+1:3d}: 💬 注释 -> {line_stripped[:80]}{'...' if len(line_stripped) > 80 else ''}")
            elif line_stripped == '':
                empty_count += 1
                if i < 30:  # 只显示前30行的空行
                    print(f"  {i+1:3d}: ⏳ 空行")
            else:
                other_count += 1
                if i < 30:  # 只显示前30行的其他内容
                    print(f"  {i+1:3d}: 📄 其他 -> {line_stripped[:80]}{'...' if len(line_stripped) > 80 else ''}")
        
        print("-" * 80)
        print(f"\n📊 行类型统计 (前100行):")
        print(f"  📺 #EXTINF行: {extinf_count}")
        print(f"  🔗 URL行: {url_count}")
        print(f"  💬 注释行: {comment_count}")
        print(f"  ⏳ 空行: {empty_count}")
        print(f"  📄 其他行: {other_count}")
        print(f"\n🎯 分析结论:")
        if extinf_count > 0 and url_count > 0:
            print(f"  ✅ 这是有效的M3U文件，包含 {extinf_count} 个频道定义和 {url_count} 个URL")
        elif extinf_count == 0:
            print("  ❌ 没有找到#EXTINF行，可能不是标准的M3U文件")
        elif url_count == 0:
            print("  ❌ 没有找到URL行，文件格式可能有问题")
        if extinf_count > 0 and url_count > extinf_count:
            print("  ℹ️  注意：URL数量大于频道定义数量，可能一个频道对应多个URL")
        if empty_count > len(lines[:100]) * 0.5:
            print("  ℹ️  注意：空行比例较高，文件可能经过了特殊处理")

    def show_file_preview(self, file_path, max_lines=30):
        """显示文件预览"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            print(f"\n📄 文件预览 ({file_path}):")
            print(f"  总行数: {len(lines)}")
            print(f"  文件大小: {len(content)} 字节")
            print("\n" + "=" * 70)
            
            # 显示文件内容
            for i, line in enumerate(lines[:max_lines]):
                print(f"{i+1:3d}: {line}")
            
            if len(lines) > max_lines:
                print(f"... 省略 {len(lines) - max_lines} 行")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ 读取文件预览时出错: {e}")

def main():
    """主函数"""
    print("🎯 M3U到TXT转换器（增强版）")
    print(f"📅 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 当前目录: {os.getcwd()}")
    print("=" * 40)
    
    # 创建转换器实例
    converter = M3UConverter(debug=True)
    
    # 尝试找到M3U文件
    possible_m3u_files = ["ipzy.m3u", "iptv.m3u", "cn.m3u", "4K.m3u", "ipvym3a", "iptv.m3a"]
    m3u_file = None
    txt_file = "ipzy.txt"
    
    # 检查命令行参数
    if len(sys.argv) == 3:
        m3u_file = sys.argv[1]
        txt_file = sys.argv[2]
        print(f"\n📄 使用命令行参数:")
        print(f"  M3U文件: {m3u_file}")
        print(f"  TXT文件: {txt_file}")
    else:
        print("\n🔍 正在查找M3U文件...")
        # 获取当前目录下所有M3U文件
        all_m3u_files = [f for f in os.listdir('.') if f.lower().endswith(('.m3u', '.m3a'))]
        
        if all_m3u_files:
            print(f"  📺 找到M3U文件: {', '.join(all_m3u_files)}")
            
            # 检查每个文件是否为空
            valid_m3u_files = []
            empty_m3u_files = []
            
            for file in all_m3u_files:
                if os.path.getsize(file) > 0:
                    valid_m3u_files.append(file)
                else:
                    empty_m3u_files.append(file)
            
            if valid_m3u_files:
                print(f"  ✅ 有效文件: {', '.join(valid_m3u_files)}")
                if empty_m3u_files:
                    print(f"  ❌ 空文件: {', '.join(empty_m3u_files)}")
                
                # 优先选择ipzy.m3u，如果存在的话
                if "ipzy.m3u" in valid_m3u_files:
                    m3u_file = "ipzy.m3u"
                    print(f"  🎯 优先选择: {m3u_file}")
                else:
                    # 否则选择第一个有效文件
                    m3u_file = valid_m3u_files[0]
                    print(f"  🎯 选择第一个有效文件: {m3u_file}")
            else:
                print("  ❌ 错误：所有M3U文件都是空的！")
        else:
            print("  ❌ 错误：没有找到M3U文件")
            
    if not m3u_file:
        print("\n❌ 错误：找不到可用的M3U文件")
        print("\n📁 当前目录文件列表:")
        for f in sorted(os.listdir('.')):
            if f.endswith(('.m3u', '.m3a')):
                size = os.path.getsize(f)
                status = "❌" if size == 0 else "✅"
                print(f"  📺 {status} {f} ({size:,} 字节)")
            else:
                print(f"  📄 {f}")
        sys.exit(1)
    
    # 确保输入文件存在
    if not os.path.exists(m3u_file):
        print(f"\n❌ 错误：M3U文件不存在: {m3u_file}")
        sys.exit(1)
    
    # 调试文件结构
    converter.debug_m3u_structure(m3u_file)
    
    # 执行转换
    print("\n🚀 开始转换操作...")
    success = converter.convert_m3u_to_txt(m3u_file, txt_file)
    
    if success:
        print(f"\n🎉 转换成功！")
        print(f"📥 输入文件: {m3u_file}")
        print(f"📤 输出文件: {txt_file}")
        print(f"📊 转换统计:")
        print(f"  ✅ 转换成功")
        
        # 显示输出文件预览
        converter.show_file_preview(txt_file, max_lines=30)
        
    else:
        print("\n💥 转换失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
