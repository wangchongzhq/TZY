#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版4K超高清直播源合并转换工具
功能：
1. 从输入文件中提取4K直播源
2. 支持测速功能，测试直播源的响应速度
3. 按速度排序并保存结果
"""

import os
import re
import time
import sys
import concurrent.futures
import urllib.request
from urllib.parse import urlparse

class Enhanced4KMerger:
    """增强版4K超高清直播源合并器"""
    
    def __init__(self):
        """初始化合并器"""
        self.input_file = "4K_uhd_channels.txt"
        self.output_file = "4K_uhd_hb.txt"
        self.channel_map = {}  # 用于去重和存储频道名称与URL的映射 {url: channel_name}
        self.channel_data = {}  # 存储频道数据，包括测速结果
        self.update_progress = None
        self.run_ui = False
        self.tasks = []
        self.total = 0
        self.start_time = None
        self.ipv6_support = False
        self.open_speed_test = True  # 开启测速功能
        self.speed_test_filter_host = None  # 测速过滤主机
        
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
                
                # 直接将这些频道添加到channel_map和channel_data中（去重）
                for channel_name, channel_url in direct_channels:
                    if channel_url not in self.channel_map:
                        self.channel_map[channel_url] = channel_name
                        self.channel_data[channel_url] = {
                            'name': channel_name,
                            'url': channel_url,
                            'speed': None,  # 测速结果
                            'online': False  # 是否在线
                        }
                    else:
                        print(f"    ⚠️  跳过重复频道 (URL已存在): {channel_name} -> {channel_url}")
            
            return len(direct_channels) > 0
            
        except Exception as e:
            print(f"❌ 读取文件时发生错误: {e}")
            return False
    
    def test_url_speed(self, url, channel_name):
        """测试单个URL的响应速度"""
        try:
            start_time = time.time()
            # 设置超时
            timeout = 5  # 5秒超时
            
            # 创建请求
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # 发送请求并读取少量数据
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    # 读取少量数据以确认连接成功
                    response.read(1024)
                    end_time = time.time()
                    speed = end_time - start_time
                    return url, speed, True
        except Exception as e:
            # 连接失败，返回超时值
            return url, float('inf'), False
    
    def test_speed(self, data, ipv6=False, callback=None):
        """测试所有URL的响应速度"""
        print(f"🚀 开始测速，共 {len(data)} 个URL")
        
        test_results = {}
        tasks = []
        
        # 创建线程池执行器
        max_workers = min(10, len(data))  # 最多10个并发任务
        
        print(f"📊 并发设置:")
        print(f"   总任务数: {len(data)}")
        print(f"   并发数: {max_workers}")
        
        # 使用进度条显示测试进度
        print("\n⏱️ 测速进度:")
        print("-" * 50)
        
        # 使用线程池并发执行测速
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_url = {}
            for url, info in data.items():
                future = executor.submit(self.test_url_speed, url, info['name'])
                future_to_url[future] = (url, info['name'])
            
            # 处理完成的任务
            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                url, channel_name = future_to_url[future]
                completed += 1
                
                try:
                    url, speed, online = future.result()
                    test_results[url] = {
                        'speed': speed,
                        'online': online,
                        'response_time': speed if online else None
                    }
                    
                    # 更新进度
                    progress = (completed / len(data)) * 100
                    
                    # 显示测速结果
                    if online:
                        print(f"   🟢 {channel_name} - 响应时间: {speed:.2f}s [进度: {progress:.1f}%]")
                    else:
                        print(f"   � {channel_name} - 连接失败 [进度: {progress:.1f}%]")
                    
                    if callback:
                        callback()
                        
                except Exception as e:
                    print(f"   ⚠️ {channel_name} - 测试异常: {e}")
                    test_results[url] = {
                        'speed': float('inf'),
                        'online': False,
                        'response_time': None
                    }
        
        print("-" * 50)
        return test_results
    
    def merge_objects(self, base, update, match_key='url'):
        """合并两个对象，用update中的值更新base"""
        result = base.copy()
        for key, value in update.items():
            if key in result:
                result[key].update(value)
        return result
    
    def sort_channel_result(self, data, result=None, filter_host=None, ipv6_support=False):
        """根据测速结果排序频道"""
        if result:
            # 合并测速结果
            data = self.merge_objects(data, result)
        
        # 按响应时间排序，在线的频道排在前面，离线的排在后面
        sorted_items = sorted(
            data.items(),
            key=lambda x: (
                not x[1].get('online', False),  # 在线的在前
                x[1].get('speed', float('inf'))  # 响应时间短的在前
            )
        )
        
        # 创建排序后的字典
        sorted_data = {}
        for url, info in sorted_items:
            sorted_data[url] = info
        
        return sorted_data
    
    def write_channel_to_file(self, data, ipv6=False):
        """将频道数据写入文件"""
        try:
            # 准备写入的数据
            unique_channels = []
            online_count = 0
            offline_count = 0
            
            for url, info in data.items():
                channel_name = info['name']
                channel_url = url
                online = info.get('online', False)
                speed = info.get('speed', None)
                
                if online:
                    online_count += 1
                    if speed is not None and speed < float('inf'):
                        channel_name = f"{channel_name} [响应:{speed:.2f}s]"
                else:
                    offline_count += 1
                    channel_name = f"{channel_name} [离线]"
                
                unique_channels.append(f"{channel_name},{channel_url}")
            
            with open(self.output_file, 'w', encoding='utf-8-sig') as f:
                # 写入文件头信息
                f.write("# 4K超高清直播源合并列表\n")
                f.write(f"# 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 频道总数: {len(unique_channels)}\n")
                f.write(f"# 在线频道: {online_count}\n")
                f.write(f"# 离线频道: {offline_count}\n")
                f.write(f"# 来源: {self.input_file}\n")
                f.write("# 测速结果: 响应时间越短越好\n")
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
            print(f"📊 频道总数: {len(unique_channels)}")
            print(f"🟢 在线频道: {online_count}")
            print(f"🔴 离线频道: {offline_count}")
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
    
    def pbar_update(self, name="测速", item_name="接口"):
        """更新进度条"""
        pass  # 简单实现，不做实际操作
    
    def main(self):
        """主函数"""
        main_start_time = time.time()
        try:
            print("🚀 增强版4K超高清直播源合并转换工具启动")
            
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
            
            # 3. 测速处理
            test_result = {}
            if self.open_speed_test:
                self.total = len(self.channel_data)
                print(f"\n📊 测速信息:")
                print(f"   总URL数: {self.total}")
                print(f"   需要测速: {self.total}")
                
                if self.update_progress:
                    self.update_progress(
                        f"正在进行测速, 共{self.total}个接口, {self.total}个接口需要进行测速",
                        0,
                    )
                
                self.start_time = time.time()
                
                # 执行测速
                test_result = self.test_speed(
                    self.channel_data,
                    ipv6=self.ipv6_support,
                    callback=lambda: self.pbar_update(name="测速", item_name="接口"),
                )
                
                # 合并测速结果
                self.channel_data = self.merge_objects(self.channel_data, test_result)
            
            # 4. 排序处理
            print("\n🔄 正在排序频道结果...")
            self.channel_data = self.sort_channel_result(
                self.channel_data,
                result=test_result,
                filter_host=self.speed_test_filter_host,
                ipv6_support=self.ipv6_support
            )
            
            # 5. 保存结果
            print("\n💾 正在生成结果文件...")
            success = self.write_channel_to_file(
                self.channel_data,
                ipv6=self.ipv6_support
            )
            
            if success:
                end_time = time.time()
                total_time = end_time - main_start_time
                
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
    merger = Enhanced4KMerger()
    
    # 运行主函数
    try:
        success = merger.main()
    except Exception as e:
        print(f"❌ 运行时发生错误: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if success:
        print("\n✅ 测试成功！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()