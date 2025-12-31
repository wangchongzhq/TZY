#!/usr/bin/env python3
"""
VLC集成效果测试脚本 - 使用109 live 1221 直播源 有效.txt文件
测试VLC媒体播放器集成在实际IPTV源文件中的效果
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from validator.vlc_detector import detect_with_vlc
from validator.iptv_validator import _ffprobe_get_resolution
import requests
import sys
import os

class VLCEffectivenessAnalyzer:
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
            'detailed_results': []
        }
        
    def load_test_sources(self, filename):
        """加载测试源"""
        sources = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and ',' in line and not line.startswith('#'):
                    # 解析频道名称和URL
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        name = parts[0].strip()
                        url = parts[1].strip()
                        if url and url.startswith(('http://', 'https://')):
                            sources.append((name, url))
            
            print(f"📥 成功加载 {len(sources)} 个测试源")
            return sources
            
        except Exception as e:
            print(f"❌ 文件加载失败: {e}")
            return []
    
    def test_single_url_comprehensive(self, name, url, timeout=3):
        """测试单个URL的完整验证流程"""
        result_info = {
            'name': name,
            'url': url,
            'methods_tried': [],
            'final_result': 'unknown',
            'total_time': 0,
            'vlc_details': {}
        }
        
        start_time = time.time()
        
        # 方法1: HTTP直接检查
        print(f"🔍 {name}: HTTP检查...")
        try:
            # 使用简单的requests HEAD请求检查URL可访问性
            response = requests.head(url, timeout=2, allow_redirects=True)
            result_info['methods_tried'].append(f"HTTP: {response.status_code}")
            if response.status_code < 400:
                self.stats['http_success'] += 1
                result_info['final_result'] = 'http_success'
                print(f"✅ HTTP验证成功: {response.status_code}")
                result_info['total_time'] = time.time() - start_time
                return result_info
        except Exception as e:
            result_info['methods_tried'].append(f"HTTP错误: {str(e)[:30]}")
        
        # 方法2: ffprobe检测
        print(f"🔍 {name}: ffprobe检测...")
        try:
            resolution, codec, info = _ffprobe_get_resolution(url, timeout=timeout)
            result_info['methods_tried'].append(f"ffprobe: {resolution or 'failed'}")
            if resolution:
                self.stats['ffprobe_success'] += 1
                result_info['final_result'] = f'ffprobe_success_{resolution}'
                print(f"✅ ffprobe检测成功: {resolution}")
                result_info['total_time'] = time.time() - start_time
                return result_info
        except Exception as e:
            result_info['methods_tried'].append(f"ffprobe错误: {str(e)[:30]}")
        
        # 方法3: VLC fallback
        print(f"🔍 {name}: VLC fallback检测...")
        self.stats['vlc_triggered'] += 1
        try:
            resolution, codec, vlc_info = detect_with_vlc(url, timeout=timeout)
            result_info['methods_tried'].append(f"VLC: {resolution or 'failed'}")
            result_info['vlc_details'] = vlc_info
            
            if resolution:
                self.stats['vlc_success'] += 1
                result_info['final_result'] = f'vlc_success_{resolution}'
                print(f"✅ VLC检测成功: {resolution}")
                result_info['total_time'] = time.time() - start_time
                return result_info
            else:
                print(f"❌ VLC检测失败: {vlc_info.get('error', '未知错误')}")
                result_info['total_time'] = time.time() - start_time
                return result_info
                
        except Exception as e:
            print(f"❌ VLC检测异常: {e}")
            result_info['methods_tried'].append(f"VLC错误: {str(e)[:30]}")
            result_info['total_time'] = time.time() - start_time
            return result_info
        
        # 所有方法都失败
        self.stats['all_failed'] += 1
        result_info['final_result'] = 'all_failed'
        result_info['total_time'] = time.time() - start_time
        return result_info
    
    def run_comprehensive_test(self, sources, max_test_count=100, test_samples=True):
        """运行综合测试"""
        if not sources:
            print("❌ 没有找到测试源")
            return
            
        # 如果测试样本，随机选择源
        if test_samples:
            import random
            if len(sources) > max_test_count:
                sources = random.sample(sources, max_test_count)
                print(f"🎲 随机选择 {max_test_count} 个源进行测试")
        
        print(f"\n🚀 开始VLC集成效果测试 (样本数: {len(sources)})")
        print("=" * 60)
        
        total_start_time = time.time()
        
        # 使用线程池并行测试（限制并发数以避免资源耗尽）
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 提交所有任务
            future_to_source = {
                executor.submit(self.test_single_url_comprehensive, name, url): (name, url)
                for name, url in sources
            }
            
            completed = 0
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    result = future.result()
                    self.stats['total_tested'] += 1
                    self.stats['detailed_results'].append(result)
                    
                    completed += 1
                    print(f"📊 进度: {completed}/{len(sources)}")
                    
                    # 每完成10个显示一次进度
                    if completed % 10 == 0:
                        self._print_intermediate_stats()
                    
                except Exception as e:
                    print(f"❌ 测试异常: {e}")
                    self.stats['total_tested'] += 1
        
        total_time = time.time() - total_start_time
        self._print_final_report(total_time)
    
    def _print_intermediate_stats(self):
        """打印中间统计信息"""
        print(f"\n📊 中间统计 (已完成 {self.stats['total_tested']}):")
        print(f"   HTTP成功: {self.stats['http_success']}")
        print(f"   ffprobe成功: {self.stats['ffprobe_success']}")
        print(f"   VLC触发: {self.stats['vlc_triggered']}")
        print(f"   VLC成功: {self.stats['vlc_success']}")
        print("=" * 40)
    
    def _print_final_report(self, total_time):
        """打印最终报告"""
        print("\n" + "=" * 60)
        print("📊 VLC集成效果分析报告")
        print("=" * 60)
        
        print(f"\n📈 总体统计:")
        print(f"   总测试数: {self.stats['total_tested']}")
        print(f"   总用时: {total_time:.1f}秒")
        if self.stats['total_tested'] > 0:
            print(f"   平均用时: {total_time/self.stats['total_tested']:.2f}秒/个")
        
        print(f"\n🎯 各方法效果:")
        http_rate = self.stats['http_success'] / self.stats['total_tested'] * 100 if self.stats['total_tested'] > 0 else 0
        ffprobe_rate = self.stats['ffprobe_success'] / self.stats['total_tested'] * 100 if self.stats['total_tested'] > 0 else 0
        vlc_trigger_rate = self.stats['vlc_triggered'] / self.stats['total_tested'] * 100 if self.stats['total_tested'] > 0 else 0
        vlc_success_rate = self.stats['vlc_success'] / self.stats['vlc_triggered'] * 100 if self.stats['vlc_triggered'] > 0 else 0
        fallback_rate = (self.stats['ffprobe_success'] + self.stats['vlc_success']) / self.stats['total_tested'] * 100 if self.stats['total_tested'] > 0 else 0
        all_failed_rate = self.stats['all_failed'] / self.stats['total_tested'] * 100 if self.stats['total_tested'] > 0 else 0
        
        print(f"   HTTP直接成功: {self.stats['http_success']} ({http_rate:.1f}%)")
        print(f"   ffprobe成功: {self.stats['ffprobe_success']} ({ffprobe_rate:.1f}%)")
        print(f"   VLC触发次数: {self.stats['vlc_triggered']} ({vlc_trigger_rate:.1f}%)")
        print(f"   VLC成功: {self.stats['vlc_success']} ({vlc_success_rate:.1f}%)")
        print(f"   Fallback成功: {self.stats['ffprobe_success'] + self.stats['vlc_success']} ({fallback_rate:.1f}%)")
        print(f"   全部失败: {self.stats['all_failed']} ({all_failed_rate:.1f}%)")
        
        print(f"\n🔍 VLC集成价值分析:")
        vlc_contribution = self.stats['vlc_success'] + (self.stats['ffprobe_success'] if self.stats['ffprobe_success'] > 0 else 0)
        total_success = self.stats['http_success'] + self.stats['ffprobe_success'] + self.stats['vlc_success']
        
        if self.stats['vlc_triggered'] > 0:
            print(f"   VLC成功率: {vlc_success_rate:.1f}%")
            print(f"   VLC触发率: {vlc_trigger_rate:.1f}%")
            
            if self.stats['vlc_success'] > 0:
                print(f"   ✅ VLC集成的价值: 成功验证了 {self.stats['vlc_success']} 个源")
                print(f"   在 {self.stats['total_tested']} 个测试源中，VLC贡献了 {self.stats['vlc_success']/self.stats['total_tested']*100:.1f}% 的成功率")
            else:
                print(f"   ⚠️ VLC集成价值有限: 未成功验证任何额外源")
        else:
            print(f"   ⚠️ VLC未被触发")
        
        print(f"\n🎉 总结:")
        if self.stats['vlc_success'] > 0 or self.stats['ffprobe_success'] > 0:
            print(f"   VLC + ffprobe集成的实际效果:")
            print(f"   - HTTP直接成功: {self.stats['http_success']} 个")
            print(f"   - Fallback成功: {self.stats['ffprobe_success'] + self.stats['vlc_success']} 个")
            print(f"   - 总成功数: {total_success} 个")
            print(f"   - 总体成功率: {total_success/self.stats['total_tested']*100:.1f}%")
            if self.stats['vlc_success'] > 0:
                print(f"   - VLC特别贡献: {self.stats['vlc_success']} 个源")
        else:
            print(f"   所有测试源都能被HTTP方法直接验证，VLC集成在此测试中未显著提升效果")
        
        # 分析VLC检测的具体详情
        vlc_results = [r for r in self.stats['detailed_results'] if r.get('vlc_details')]
        if vlc_results:
            print(f"\n🔍 VLC检测详情分析:")
            error_types = {}
            for result in vlc_results:
                error = result['vlc_details'].get('error', 'unknown')
                error_types[error] = error_types.get(error, 0) + 1
            
            print("   VLC检测失败原因统计:")
            for error, count in error_types.items():
                print(f"   - {error}: {count} 次")

def main():
    analyzer = VLCEffectivenessAnalyzer()
    
    # 加载测试源
    filename = "109  live 1221 直播源  有效.txt"
    sources = analyzer.load_test_sources(filename)
    
    if not sources:
        print("❌ 无法加载测试源，程序退出")
        return
    
    # 运行综合测试（测试前100个源作为样本）
    analyzer.run_comprehensive_test(sources, max_test_count=100, test_samples=True)

if __name__ == "__main__":
    main()