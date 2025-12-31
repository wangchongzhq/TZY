#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLC集成效果测试脚本
专门测试VLC作为fallback方法在实际验证中的触发和使用情况
"""

import os
import sys
import time
import json
from collections import defaultdict

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from validator.iptv_validator import IPTVValidator
from validator.vlc_detector import detect_with_vlc

class VLCIntegrationAnalyzer:
    """VLC集成效果分析器"""
    
    def __init__(self):
        self.stats = {
            'total_tested': 0,
            'http_success': 0,
            'ffprobe_success': 0,
            'vlc_triggered': 0,
            'vlc_success': 0,
            'fallback_success': 0,
            'all_failed': 0,
            'vlc_details': []
        }
    
    def test_single_url_with_vlc(self, url, name, timeout=3):
        """测试单个URL的完整验证流程，包括VLC集成"""
        print(f"\n🧪 测试: {name}")
        print(f"📡 URL: {url}")
        
        result_info = {
            'name': name,
            'url': url,
            'methods_tried': [],
            'final_result': None,
            'timing': {}
        }
        
        start_time = time.time()
        
        # 方法1: HTTP状态检查
        print("🔍 方法1: HTTP状态检查...")
        try:
            from url_validator import check_url_status
            is_valid, status = check_url_status(url, timeout=2, retries=1)
            result_info['methods_tried'].append(f"HTTP状态: {status}")
            if is_valid:
                self.stats['http_success'] += 1
                result_info['final_result'] = 'http_success'
                print(f"✅ HTTP验证成功: {status}")
                return result_info
        except Exception as e:
            print(f"❌ HTTP验证失败: {e}")
            result_info['methods_tried'].append(f"HTTP错误: {str(e)[:50]}")
        
        # 方法2: ffprobe检测
        print("🔍 方法2: ffprobe检测...")
        try:
            from validator.iptv_validator import _ffprobe_get_resolution
            resolution, codec, info = _ffprobe_get_resolution(url, timeout=3)
            result_info['methods_tried'].append(f"ffprobe: {resolution or 'failed'}")
            if resolution:
                self.stats['ffprobe_success'] += 1
                result_info['final_result'] = f'ffprobe_success_{resolution}'
                print(f"✅ ffprobe检测成功: {resolution} ({codec})")
                return result_info
            else:
                print(f"❌ ffprobe检测失败")
        except Exception as e:
            print(f"❌ ffprobe检测异常: {e}")
            result_info['methods_tried'].append(f"ffprobe错误: {str(e)[:50]}")
        
        # 方法3: VLC fallback
        print("🔍 方法3: VLC fallback检测...")
        self.stats['vlc_triggered'] += 1
        try:
            resolution, codec, vlc_info = detect_with_vlc(url, timeout=timeout)
            result_info['methods_tried'].append(f"VLC: {resolution or 'failed'}")
            result_info['vlc_details'] = vlc_info
            
            if resolution:
                self.stats['vlc_success'] += 1
                result_info['final_result'] = f'vlc_success_{resolution}'
                print(f"✅ VLC检测成功: {resolution} ({codec})")
                print(f"   VLC详情: {vlc_info}")
            else:
                print(f"❌ VLC检测失败: {vlc_info.get('error', '未知错误')}")
                self.stats['fallback_success'] += 1
        except Exception as e:
            print(f"❌ VLC检测异常: {e}")
            result_info['methods_tried'].append(f"VLC异常: {str(e)[:50]}")
        
        total_time = time.time() - start_time
        result_info['timing']['total'] = total_time
        
        if not result_info['final_result']:
            self.stats['all_failed'] += 1
            result_info['final_result'] = 'all_failed'
            print(f"❌ 所有方法都失败")
        
        print(f"⏱️  总用时: {total_time:.2f}秒")
        return result_info
    
    def run_focused_test(self, test_urls):
        """运行聚焦测试"""
        print("🚀 开始VLC集成效果测试")
        print("=" * 60)
        
        start_time = time.time()
        
        for i, (name, url) in enumerate(test_urls, 1):
            print(f"\n📊 进度: {i}/{len(test_urls)}")
            result = self.test_single_url_with_vlc(url, name)
            self.stats['total_tested'] += 1
        
        total_time = time.time() - start_time
        
        self.print_analysis_report(total_time)
    
    def print_analysis_report(self, total_time):
        """打印分析报告"""
        print("\n" + "=" * 60)
        print("📊 VLC集成效果分析报告")
        print("=" * 60)
        
        print(f"📈 总体统计:")
        print(f"   总测试数: {self.stats['total_tested']}")
        print(f"   总用时: {total_time:.1f}秒")
        print(f"   平均用时: {total_time/self.stats['total_tested']:.2f}秒/个")
        
        print(f"\n🎯 各方法效果:")
        print(f"   HTTP直接成功: {self.stats['http_success']} ({self.stats['http_success']/self.stats['total_tested']*100:.1f}%)")
        print(f"   ffprobe成功: {self.stats['ffprobe_success']} ({self.stats['ffprobe_success']/self.stats['total_tested']*100:.1f}%)")
        print(f"   VLC触发次数: {self.stats['vlc_triggered']} ({self.stats['vlc_triggered']/self.stats['total_tested']*100:.1f}%)")
        print(f"   VLC成功: {self.stats['vlc_success']} ({self.stats['vlc_success']/self.stats['total_tested']*100:.1f}%)")
        print(f"   Fallback成功: {self.stats['fallback_success']} ({self.stats['fallback_success']/self.stats['total_tested']*100:.1f}%)")
        print(f"   全部失败: {self.stats['all_failed']} ({self.stats['all_failed']/self.stats['total_tested']*100:.1f}%)")
        
        print(f"\n🔍 VLC集成价值分析:")
        vlc_value = self.stats['vlc_success'] + self.stats['fallback_success']
        if self.stats['vlc_triggered'] > 0:
            vlc_success_rate = self.stats['vlc_success'] / self.stats['vlc_triggered'] * 100
            print(f"   VLC成功率: {vlc_success_rate:.1f}%")
            print(f"   VLC贡献: {vlc_value}/{self.stats['total_tested']} = {vlc_value/self.stats['total_tested']*100:.1f}%")
            
            if vlc_value > 0:
                print(f"   ✅ VLC集成的价值: 帮助验证了{vlc_value}个源，占总数的{vlc_value/self.stats['total_tested']*100:.1f}%")
            else:
                print(f"   ⚠️ VLC集成价值有限: 未成功验证任何额外源")
        else:
            print(f"   ⚠️ VLC未被触发")
        
        print(f"\n🎉 总结:")
        if vlc_value > 0:
            print(f"   VLC集成的实际效果: 为验证过程贡献了{vlc_value}个有效结果")
            print(f"   在{self.stats['total_tested']}个测试源中，VLC帮助提高了{vlc_value/self.stats['total_tested']*100:.1f}%的成功率")
        else:
            print(f"   VLC集成在此测试中未显著提升验证效果")

def main():
    # 创建测试URL列表（包含各种类型的源）
    test_sources = [
        # 高质量HTTP源（应该被HTTP直接验证）
        ("浙江卫视4K", "https://play-qukan.cztv.com/live/1758879019692345.m3u8"),
        ("翡翠台4K", "https://cdn6.163189.xyz/163189/fct4k"),
        
        # 中等质量源（可能需要ffprobe）
        ("湖南卫视4K", "http://hlsal-ldvt.qing.mgtv.com/nn_live/nn_x64/dWlwPTEyNy4wLjAuMSZ1aWQ9cWluZy1jbXMmbm5fdGltZXpvbmU9OCZjZG5leF9pZD1hbF9obHNfbGR2dCZ1dWlkPTliODY4NmU5ZTM2YzYwMmMmZT02OTE0NjA0JnY9MSZpZD1ITldTWkdTVCZzPTcwN2RiYTc2YzJjNmJmMTQ4MmUyZGYzOWU2NWM3YWFi/HNWSZGST.m3u8"),
        
        # 可能需要VLC的复杂源
        ("咪视界4K", "http://gslbserv.itv.cmvideo.cn:80/3000000010000005180/1.m3u8?channel-id=FifastbLive&Contentid=3000000010000005180&livemode=1&stbId=fy666"),
        ("CCTV4K", "http://btjg.net:809/hls/141/index.m3u8"),
        
        # 很可能需要VLC的源
        ("深圳卫视4K", "https://cdn3.163189.xyz/163189/szws4k"),
        ("河北卫视4K", "https://event.pull.hebtv.com:443/live/live101.m3u8"),
        ("苏州4K", "https://tylive.kan0512.com/norecord/csztv4k_4k.m3u8"),
        
        # 复杂参数的源
        ("CCTV16 4K", "http://nas.201606.xyz:4022/rtp/239.10.0.187:5140"),
        ("北京卫视4K", "http://yp.qqqtv.top/1/api.php?id=%E5%8C%97%E4%BA%AC%E5%8D%AB%E8%A7%864K&auth=666858"),
    ]
    
    analyzer = VLCIntegrationAnalyzer()
    analyzer.run_focused_test(test_sources)

if __name__ == "__main__":
    main()