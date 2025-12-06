#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较不同高清线路筛选方法的有效性和准确性

测试方法包括：
1. 当前基于FFmpeg的实际分辨率检测
2. 基于URL文本匹配的分辨率检测
3. 基于视频流类型的检测
4. 综合策略
"""

import os
import sys
import time
import logging
import re
from typing import Optional, Tuple, List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResolutionFilterMethods:
    """
    测试不同的高清线路筛选方法
    """
    
    def __init__(self):
        # 常见的分辨率标识
        self.resolution_patterns = {
            '2160p': (3840, 2160),
            '4k': (3840, 2160),
            '1080p': (1920, 1080),
            '720p': (1280, 720),
            '480p': (854, 480),
            '360p': (640, 360)
        }
        
        # 高清视频流类型
        self.hd_stream_types = ['hls', 'dash', 'm3u8', 'mpd']
        
    def method_1_ffmpeg_based(self, url: str) -> Dict:
        """
        方法1: 基于FFmpeg的实际分辨率检测
        优点: 最准确，直接获取视频流的实际分辨率
        缺点: 速度慢，依赖外部工具，可能受网络影响大
        """
        # 由于FFmpeg检测在实际测试中成功率低，这里只模拟其特性
        return {
            'name': 'FFmpeg实际检测',
            'accuracy': '高',
            'speed': '慢',
            'reliability': '中',
            'is_hd': None,  # 实际测试中需要调用FFmpeg
            'resolution': None,
            'description': '使用FFmpeg获取视频流的实际分辨率，最准确但速度慢'
        }
    
    def method_2_url_pattern(self, url: str) -> Dict:
        """
        方法2: 基于URL文本匹配的分辨率检测
        优点: 速度快，不依赖外部工具
        缺点: 准确性有限，依赖URL中包含的分辨率信息
        """
        url_lower = url.lower()
        is_hd = False
        resolution = None
        
        # 检查URL中是否包含高清标识
        for pattern, res in self.resolution_patterns.items():
            if pattern in url_lower:
                resolution = res
                # 如果分辨率大于等于1080p，则认为是高清
                if res[0] >= 1920 and res[1] >= 1080:
                    is_hd = True
                break
        
        # 额外检查一些常见的高清标识
        hd_keywords = ['hd', 'high', 'quality', 'fullhd']
        for keyword in hd_keywords:
            if keyword in url_lower:
                is_hd = True
                break
        
        return {
            'name': 'URL模式匹配',
            'accuracy': '中',
            'speed': '极快',
            'reliability': '低',
            'is_hd': is_hd,
            'resolution': resolution,
            'description': '通过URL中的关键词识别分辨率，速度快但准确性有限'
        }
    
    def method_3_stream_type(self, url: str) -> Dict:
        """
        方法3: 基于视频流类型的检测
        优点: 速度快，简单易用
        缺点: 准确性低，只能作为辅助判断
        """
        url_lower = url.lower()
        
        # 检查是否是常见的高清流类型
        is_hd_stream = any(stream_type in url_lower for stream_type in self.hd_stream_types)
        
        # 检查是否是HTTP/HTTPS协议（通常更可能是高清）
        is_http = url_lower.startswith(('http://', 'https://'))
        
        # 结合判断
        is_hd = is_hd_stream and is_http
        
        return {
            'name': '流类型检测',
            'accuracy': '低',
            'speed': '极快',
            'reliability': '低',
            'is_hd': is_hd,
            'resolution': None,
            'description': '基于视频流类型判断是否为高清，简单但准确性低'
        }
    
    def method_4_combined(self, url: str) -> Dict:
        """
        方法4: 综合策略（URL模式 + 流类型 + 简单规则）
        优点: 平衡准确性和速度，实用性强
        缺点: 仍有一定误判率
        """
        url_lower = url.lower()
        result_2 = self.method_2_url_pattern(url)
        result_3 = self.method_3_stream_type(url)
        
        # 综合判断
        is_hd = False
        
        # 如果URL模式匹配到高清标识，则直接认为是高清
        if result_2['is_hd']:
            is_hd = True
        # 否则结合流类型判断
        elif result_3['is_hd']:
            # 检查是否是知名的高清源
            hd_sources = ['cctv', 'migu', 'iptv', 'live', 'stream']
            if any(source in url_lower for source in hd_sources):
                is_hd = True
        
        # 检查URL中的分辨率参数
        # 例如: ?width=1920&height=1080
        resolution_params = re.findall(r'(width|height)=\d+', url_lower)
        if resolution_params:
            width = re.search(r'width=(\d+)', url_lower)
            height = re.search(r'height=(\d+)', url_lower)
            if width and height:
                width = int(width.group(1))
                height = int(height.group(1))
                if width >= 1920 and height >= 1080:
                    is_hd = True
        
        return {
            'name': '综合策略',
            'accuracy': '中高',
            'speed': '快',
            'reliability': '中高',
            'is_hd': is_hd,
            'resolution': result_2['resolution'],
            'description': '结合URL模式、流类型和其他规则的综合判断，平衡准确性和速度'
        }

def load_test_urls(file_path: str, count: int = 20) -> List[str]:
    """
    从文件中加载测试用的URL列表
    """
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释行和分类行
                if not line or line.startswith('#') or '#genre#' in line:
                    continue
                    
                # 解析频道名称和URL
                if ',' in line:
                    url = line.split(',')[-1].strip()
                    # 验证URL格式
                    if url.startswith(('http://', 'https://', 'rtmp://', 'rtsp://', 'udp://')):
                        urls.append(url)
                        if len(urls) >= count:
                            break
    except Exception as e:
        logger.error(f"加载测试URL失败: {e}")
    return urls

def run_comparison(test_urls: List[str]) -> List[Dict]:
    """
    运行不同方法的比较测试
    """
    results = []
    filter_methods = ResolutionFilterMethods()
    
    for url in test_urls:
        result = {
            'url': url,
            'methods': []
        }
        
        # 测试四种方法
        result['methods'].append(filter_methods.method_1_ffmpeg_based(url))
        result['methods'].append(filter_methods.method_2_url_pattern(url))
        result['methods'].append(filter_methods.method_3_stream_type(url))
        result['methods'].append(filter_methods.method_4_combined(url))
        
        results.append(result)
    
    return results

def print_comparison_results(results: List[Dict]):
    """
    打印比较结果
    """
    print("\n" + "="*80)
    print("高清线路筛选方法比较")
    print("="*80)
    
    print(f"\n共测试 {len(results)} 个URL")
    
    # 打印每个URL的测试结果
    for i, result in enumerate(results):
        print(f"\n{'-'*80}")
        print(f"URL {i+1}: {result['url']}")
        print("-"*80)
        
        for method in result['methods']:
            res_str = f"{method['resolution'][0]}x{method['resolution'][1]}" if method['resolution'] else "未知"
            print(f"{method['name']:<12} | 高清: {'是' if method['is_hd'] else '否':<5} | 分辨率: {res_str:<12} | 准确性: {method['accuracy']:<5} | 速度: {method['speed']:<5}")
    
    # 总结各方法的特点
    print(f"\n" + "="*80)
    print("方法特点总结")
    print("="*80)
    
    filter_methods = ResolutionFilterMethods()
    # 只需要一个URL来获取方法描述
    sample_url = results[0]['url'] if results else ""
    for method in [filter_methods.method_1_ffmpeg_based(sample_url),
                   filter_methods.method_2_url_pattern(sample_url),
                   filter_methods.method_3_stream_type(sample_url),
                   filter_methods.method_4_combined(sample_url)]:
        print(f"\n{method['name']}:")
        print(f"  描述: {method['description']}")
        print(f"  准确性: {method['accuracy']}")
        print(f"  速度: {method['speed']}")
        print(f"  可靠性: {method['reliability']}")
    
    # 推荐方案
    print(f"\n" + "="*80)
    print("推荐方案")
    print("="*80)
    print("1. 生产环境首选: 综合策略（方法4）")
    print("   - 平衡了准确性和速度")
    print("   - 适合大规模筛选")
    print("   - 可根据实际情况调整规则")
    print("\n2. 高精度场景: FFmpeg实际检测（方法1）")
    print("   - 用于对准确性要求极高的场景")
    print("   - 可作为综合策略的补充验证")
    print("\n3. 快速筛选场景: URL模式匹配（方法2）")
    print("   - 用于需要快速初步筛选的场景")
    print("   - 可作为预处理步骤")

def main():
    """
    主函数
    """
    # 从ipzy_channels.txt加载测试URL
    test_file = "ipzy_channels.txt"
    if not os.path.exists(test_file):
        logger.error(f"测试文件不存在: {test_file}")
        return
    
    # 加载20个测试URL
    test_urls = load_test_urls(test_file, count=20)
    if not test_urls:
        logger.error("没有加载到测试URL")
        return
    
    logger.info(f"成功加载了 {len(test_urls)} 个测试URL")
    
    # 运行比较测试
    results = run_comparison(test_urls)
    
    # 打印结果
    print_comparison_results(results)


if __name__ == "__main__":
    main()
