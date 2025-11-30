#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4K超高清直播源合并转换测试工具
功能：测试4K_uhd_merger.py的核心功能
"""

import os
import re
import time
import sys

class Simple4KMerger:
    """简化版4K超高清直播源合并器"""
    
    def __init__(self):
        """初始化合并器"""
        self.input_file = "4K_uhd_channels.txt"
        self.output_file = "4K_uhd_hb.txt"
        self.channel_map = {}  # 用于去重和存储频道名称与URL的映射 {url: channel_name}
    
    def process_direct_channels(self):
        """处理直接的频道URL"""
        print(f"📝 正在读取输入文件: {self.input_file}")
        
        try:
            with open(self.input_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            direct_channels = []
            
            for line in lines:
                line = line.strip()
                
                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue
                
                # 检查是否是频道名称,URL格式
                if ',' in line:
                    parts = line.split(',', 1)  # 只按第一个逗号分割
                    if len(parts) == 2:
                        channel_name, channel_url = parts[0].strip(), parts[1].strip()
                        
                        # 验证URL格式
                        if channel_url.startswith(('http://', 'https://')):
                            direct_channels.append((channel_name, channel_url))
                            print(f"   📡 直接频道: {channel_name} -> {channel_url}")
            
            # 处理直接的频道（去重）
            if direct_channels:
                print(f"📊 找到 {len(direct_channels)} 个直接频道URL")
                
                # 直接将这些频道添加到channel_map中（去重）
                for channel_name, channel_url in direct_channels:
                    if channel_url not in self.channel_map:
                        self.channel_map[channel_url] = channel_name
                    else:
                        print(f"    ⚠️  跳过重复频道 (URL已存在): {channel_name} -> {channel_url}")
            
            return len(direct_channels) > 0
            
        except Exception as e:
            print(f"❌ 读取文件时发生错误: {e}")
            return False
    
    def save_results(self):
        """保存处理结果到文件（格式：频道名称,URL）"""
        try:
            # 从channel_map中获取所有频道（已自动去重）
            unique_channels = [f"{name},{url}" for url, name in self.channel_map.items()]
            unique_channels.sort()  # 按频道名称排序
            
            with open(self.output_file, 'w', encoding='utf-8-sig') as f:
                # 写入文件头信息
                f.write("# 4K超高清直播源合并列表\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 频道总数: {len(unique_channels)}\n")
                f.write(f"# 来源: {self.input_file}\n")
                f.write("\n")
                f.write("# 频道列表（格式：频道名称,频道URL）\n")
                f.write("\n")
                
                # 写入频道信息
                for channel in unique_channels:
                    f.write(f"{channel}\n")
            
            # 获取文件大小
            file_size = os.path.getsize(self.output_file) / 1024
            
            print(f"✅ 保存成功!")
            print(f"📁 文件名: {self.output_file}")
            print(f"📊 频道数: {len(unique_channels)}")
            print(f"📏 文件大小: {file_size:.2f} KB")
            
            # 显示示例内容
            print(f"\n📄 文件示例内容:")
            with open(self.output_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()[:10]  # 只显示前10行
                for line in lines:
                    print(f"   {line.rstrip()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 保存文件时发生错误: {e}")
            return False
    
    def run(self):
        """主运行函数"""
        print("🚀 简化版4K超高清直播源合并转换工具启动")
        start_time = time.time()
        
        try:
            # 1. 处理直接的频道URL
            has_channels = self.process_direct_channels()
            
            if not has_channels and not self.channel_map:
                print("🚫 没有找到任何频道")
                return False
            
            # 2. 统计结果
            print("\n📊 合并统计:")
            print(f"   去重后频道数: {len(self.channel_map)}")
            
            if not self.channel_map:
                print("🚫 没有解析到任何频道信息")
                return False
            
            # 3. 保存结果
            success = self.save_results()
            
            if success:
                end_time = time.time()
                total_time = end_time - start_time
                
                print("\n" + "=" * 60)
                print(f"🏆 操作完成!")
                print(f"⏱️ 总耗时: {total_time:.2f} 秒")
                print(f"📝 结果文件: {self.output_file}")
                print("=" * 60)
            
            return success
            
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断操作")
            return False
        except Exception as e:
            print(f"\n❌ 程序运行时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

# 主函数
def main():
    """主函数"""
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("❌ 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 创建合并器实例并运行
    merger = Simple4KMerger()
    success = merger.run()
    
    if success:
        print("\n✅ 测试成功！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
