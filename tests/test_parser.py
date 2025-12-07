#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析器模块单元测试
"""

import os
import sys
import unittest
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.parser import (ChannelInfo, parse_m3u_content, parse_txt_content, 
                       detect_content_format, parse_content, generate_m3u_content, generate_txt_content)


class TestChannelInfo(unittest.TestCase):
    """频道信息类测试"""
    
    def test_channel_info_initialization(self):
        """测试频道信息对象的初始化"""
        channel = ChannelInfo(
            name="测试频道",
            url="http://example.com/stream",
            tvg_id="test.channel",
            tvg_name="Test Channel",
            tvg_logo="http://example.com/logo.png",
            group="测试分组"
        )
        
        self.assertEqual(channel.name, "测试频道")
        self.assertEqual(channel.url, "http://example.com/stream")
        self.assertEqual(channel.tvg_id, "test.channel")
        self.assertEqual(channel.tvg_name, "Test Channel")
        self.assertEqual(channel.tvg_logo, "http://example.com/logo.png")
        self.assertEqual(channel.group, "测试分组")


class TestParser(unittest.TestCase):
    """解析器功能测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 准备测试数据
        self.m3u_content = '''#EXTM3U
#EXTINF:-1 tvg-id="cctv1" tvg-name="CCTV1" tvg-logo="http://example.com/cctv1.png" group-title="央视",CCTV-1
http://example.com/cctv1
#EXTINF:-1 tvg-id="cctv2" tvg-name="CCTV2" tvg-logo="http://example.com/cctv2.png" group-title="央视",CCTV-2
http://example.com/cctv2
'''        
        
        self.txt_content = '''CCTV-1|http://example.com/cctv1
CCTV-2|http://example.com/cctv2
CCTV-3|http://example.com/cctv3
'''        
        
        # 创建测试用的频道列表
        self.channels = [
            ChannelInfo(name="CCTV-1", url="http://example.com/cctv1", tvg_id="cctv1", tvg_name="CCTV1", tvg_logo="http://example.com/cctv1.png", group="央视"),
            ChannelInfo(name="CCTV-2", url="http://example.com/cctv2", tvg_id="cctv2", tvg_name="CCTV2", tvg_logo="http://example.com/cctv2.png", group="央视")
        ]
    
    def test_parse_m3u_content(self):
        """测试解析M3U格式内容"""
        channels = parse_m3u_content(self.m3u_content)
        
        # 验证解析结果
        self.assertEqual(len(channels), 2)
        self.assertEqual(channels[0].name, "CCTV-1")
        self.assertEqual(channels[0].url, "http://example.com/cctv1")
        self.assertEqual(channels[0].tvg_id, "cctv1")
        self.assertEqual(channels[0].group, "央视")
    
    def test_parse_txt_content(self):
        """测试解析TXT格式内容"""
        channels = parse_txt_content(self.txt_content)
        
        # 验证解析结果
        self.assertEqual(len(channels), 3)
        self.assertEqual(channels[0].name, "CCTV-1")
        self.assertEqual(channels[0].url, "http://example.com/cctv1")
        self.assertEqual(channels[0].tvg_id, "")  # TXT格式不包含tvg_id，返回空字符串
    
    def test_detect_content_format(self):
        """测试内容格式检测"""
        # 测试M3U格式
        self.assertEqual(detect_content_format(self.m3u_content), "m3u")
        
        # 测试TXT格式
        self.assertEqual(detect_content_format(self.txt_content), "txt")
        
        # 测试空内容
        self.assertEqual(detect_content_format(""), "txt")  # 空内容返回txt
        
        # 测试未知格式
        self.assertEqual(detect_content_format("unknown content"), "txt")  # 未知格式返回txt
    
    def test_parse_content(self):
        """测试统一解析接口"""
        # 测试解析M3U内容
        m3u_channels = parse_content(self.m3u_content, "m3u")
        self.assertEqual(len(m3u_channels), 2)
        
        # 测试解析TXT内容
        txt_channels = parse_content(self.txt_content, "txt")
        self.assertEqual(len(txt_channels), 3)
        
        # 测试自动检测格式
        auto_m3u_channels = parse_content(self.m3u_content)
        self.assertEqual(len(auto_m3u_channels), 2)
        
        auto_txt_channels = parse_content(self.txt_content)
        self.assertEqual(len(auto_txt_channels), 3)
    
    def test_generate_m3u_content(self):
        """测试生成M3U格式内容"""
        m3u_content = generate_m3u_content(self.channels)
        
        # 验证生成的内容
        self.assertIn("#EXTM3U", m3u_content)
        self.assertIn("CCTV-1", m3u_content)
        self.assertIn("CCTV-2", m3u_content)
        self.assertIn("http://example.com/cctv1", m3u_content)
        self.assertIn("http://example.com/cctv2", m3u_content)
        self.assertIn("tvg-id=\"cctv1\"", m3u_content)
    
    def test_generate_txt_content(self):
        """测试生成TXT格式内容"""
        txt_content = generate_txt_content(self.channels)
        
        # 验证生成的内容
        self.assertIn("CCTV-1|http://example.com/cctv1", txt_content)
        self.assertIn("CCTV-2|http://example.com/cctv2", txt_content)
    
    def test_extract_channel_name(self):
        """测试频道名称提取逻辑"""
        import re
        
        def extract_channel_name(extinf_line):
            """提取频道名称的逻辑"""
            print(f"原始#EXTINF行: {extinf_line}")
            
            # 移除#EXTINF:-1部分
            if '#EXTINF:-1' in extinf_line:
                extinf_line = extinf_line.replace('#EXTINF:-1', '')
            
            # 优先从tvg-name提取频道名称
            if 'tvg-name=' in extinf_line:
                match = re.search(r'tvg-name="([^"]+)"', extinf_line)
                if match:
                    tvg_name = match.group(1)
                    print(f"从tvg-name提取到: {tvg_name}")
                    return tvg_name
            
            # 如果没有tvg-name，再从行末提取频道名称
            if ',' in extinf_line:
                line_end_name = extinf_line.split(',', 1)[1].strip()
                if line_end_name:
                    print(f"从行末提取到: {line_end_name}")
                    return line_end_name
            
            return extinf_line.strip()
        
        # 测试用例
        test_cases = [
            '#EXTINF:-1 tvg-id="cctv1" tvg-name="CCTV1" tvg-logo="http://example.com/cctv1.png" group-title="央视",CCTV-1',
            '#EXTINF:-1 tvg-id="cctv2" tvg-name="CCTV2" tvg-logo="http://example.com/cctv2.png" group-title="央视",CCTV-2',
            '#EXTINF:-1 tvg-name="CCTV3" tvg-logo="http://example.com/cctv3.png",CCTV-3',
            '#EXTINF:-1,CCTV-4'
        ]
        
        expected_results = ["CCTV1", "CCTV2", "CCTV3", "CCTV-4"]
        
        for test_case, expected in zip(test_cases, expected_results):
            result = extract_channel_name(test_case)
            self.assertEqual(result, expected)
    
    def test_find_cctv_channels(self):
        """测试查找CCTV相关的#EXTINF行"""
        # 使用setUp中定义的m3u_content进行测试
        lines = self.m3u_content.split('\n')
        cctv_extinf_lines = [line for line in lines if 'CCTV' in line and '#EXTINF' in line]
        
        # 验证结果
        self.assertEqual(len(cctv_extinf_lines), 2)
        self.assertIn('CCTV1', cctv_extinf_lines[0])
        self.assertIn('CCTV2', cctv_extinf_lines[1])


if __name__ == '__main__':
    unittest.main()
