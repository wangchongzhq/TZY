#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频道处理工具模块单元测试
"""

import os
import sys
import unittest
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.parser import ChannelInfo
from core.channel_utils import (generate_channel_hash, deduplicate_channels, 
                               filter_channels, group_channels, validate_channels)


class TestChannelUtils(unittest.TestCase):
    """频道处理工具测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 准备测试数据
        self.channels = [
            ChannelInfo(name="CCTV-1", url="http://example.com/cctv1", tvg_id="cctv1", tvg_name="CCTV1", tvg_logo="http://example.com/cctv1.png", group="央视"),
            ChannelInfo(name="CCTV-2", url="http://example.com/cctv2", tvg_id="cctv2", tvg_name="CCTV2", tvg_logo="http://example.com/cctv2.png", group="央视"),
            ChannelInfo(name="北京卫视", url="http://example.com/btv1", tvg_id="btv1", tvg_name="BTV1", tvg_logo="http://example.com/btv1.png", group="卫视"),
            ChannelInfo(name="北京卫视", url="http://example.com/btv1_duplicate", tvg_id="btv1", tvg_name="BTV1", tvg_logo="http://example.com/btv1.png", group="卫视"),  # 重复频道，URL不同
            ChannelInfo(name="CCTV-3", url="http://example.com/cctv3", tvg_id="cctv3", tvg_name="CCTV3", tvg_logo="", group="央视"),  # 没有logo
        ]
    
    def test_generate_channel_hash(self):
        """测试生成频道哈希值"""
        channel = self.channels[0]
        
        # 测试基于名称和URL的哈希
        hash1 = generate_channel_hash(channel, use_name=True, use_url=True, use_tvg_id=False)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 32)  # MD5哈希值长度
        
        # 测试基于tvg_id的哈希
        hash2 = generate_channel_hash(channel, use_name=False, use_url=False, use_tvg_id=True)
        self.assertIsInstance(hash2, str)
        
        # 测试默认哈希方法
        hash3 = generate_channel_hash(channel)
        self.assertEqual(hash3, hash1)  # 默认应该是基于name_url
    
    def test_deduplicate_channels(self):
        """测试频道去重功能"""
        # 测试基于name_url去重
        unique_channels = deduplicate_channels(self.channels, by_name=True, by_url=True, by_tvg_id=False)
        self.assertEqual(len(unique_channels), 5)  # 基于name_url，所有频道都不同
        
        # 测试基于tvg_id去重
        unique_channels_by_tvg = deduplicate_channels(self.channels, by_name=False, by_url=False, by_tvg_id=True)
        self.assertEqual(len(unique_channels_by_tvg), 4)  # 基于tvg_id，北京卫视会被去重
        
        # 测试基于name去重
        unique_channels_by_name = deduplicate_channels(self.channels, by_name=True, by_url=False, by_tvg_id=False)
        self.assertEqual(len(unique_channels_by_name), 4)  # 基于name，北京卫视会被去重
    
    def test_filter_channels(self):
        """测试频道过滤功能"""
        # 测试按名称过滤
        filtered = filter_channels(self.channels, name_pattern="CCTV")
        self.assertEqual(len(filtered), 3)  # 只有CCTV开头的频道
        
        # 测试按分组过滤
        filtered = filter_channels(self.channels, group_pattern="卫视")
        self.assertEqual(len(filtered), 2)  # 只有卫视分组的频道
        
        # 测试组合过滤
        filtered = filter_channels(self.channels, name_pattern="CCTV", group_pattern="央视")
        self.assertEqual(len(filtered), 3)  # 央视分组中的CCTV频道
        
        # 测试包含logo过滤 - 使用自定义过滤函数
        filtered = filter_channels(self.channels, custom_filter=lambda x: x.tvg_logo != "")
        self.assertEqual(len(filtered), 4)  # 排除没有logo的CCTV-3
    
    def test_group_channels(self):
        """测试频道分组功能"""
        # 分组频道
        grouped = group_channels(self.channels)
        
        # 验证分组结果
        self.assertIn("央视", grouped)
        self.assertIn("卫视", grouped)
        
        self.assertEqual(len(grouped["央视"]), 3)
        self.assertEqual(len(grouped["卫视"]), 2)
    
    def test_validate_channels(self):
        """测试频道验证功能"""
        # 添加一个无效频道（URL格式错误）
        invalid_channel = ChannelInfo(name="无效频道", url="invalid_url", tvg_id="invalid", tvg_name="Invalid", tvg_logo="", group="其他")
        self.channels.append(invalid_channel)
        
        # 验证频道
        valid, invalid = validate_channels(self.channels)
        
        # 验证结果
        self.assertEqual(len(valid), 5)  # 有效频道数
        self.assertEqual(len(invalid), 1)  # 无效频道数
        self.assertEqual(invalid[0].name, "无效频道")
    
    def test_should_exclude_resolution(self):
        """测试分辨率过滤功能"""
        from core.channel_utils import should_exclude_resolution
        
        # 测试央视频道分辨率过滤
        self.assertFalse(should_exclude_resolution("http://example.com/cctv1", "CCTV1"))  # 未显示分辨率
        self.assertFalse(should_exclude_resolution("http://example.com/cctv1", "CCTV1 (1080p)"))  # 1080p
        self.assertTrue(should_exclude_resolution("http://example.com/cctv1", "CCTV1 (720p)"))  # 720p
        self.assertTrue(should_exclude_resolution("http://example.com/cctv1", "CCTV1 (480p)"))  # 480p
        
        # 测试非央视频道分辨率过滤
        self.assertFalse(should_exclude_resolution("http://example.com/btv1", "北京卫视 (1080p)"))  # 1080p
        self.assertTrue(should_exclude_resolution("http://example.com/btv1", "北京卫视 (720p)"))  # 720p
    
    def test_categorize_channels(self):
        """测试频道分类功能"""
        from core.config import get_config
        import re
        from collections import defaultdict
        
        # 获取分类规则
        CATEGORY_RULES = get_config('category.rules', {
            "春晚": [r'春晚', r'春节联欢晚会'],
            "央视": [r'CCTV', r'中央电视台', r'CGTN', r'央视'],
            "卫视": [r'北京卫视', r'上海卫视', r'江苏卫视', r'浙江卫视', r'湖南卫视', r'东方卫视', r'广东卫视', r'深圳卫视', r'安徽卫视', r'山东卫视', r'天津卫视', r'四川卫视', r'重庆卫视', r'河南卫视', r'湖北卫视', r'江西卫视', r'云南卫视', r'辽宁卫视', r'黑龙江卫视', r'吉林卫视', r'福建卫视', r'广西卫视', r'河北卫视', r'山西卫视', r'陕西卫视', r'贵州卫视', r'甘肃卫视', r'海南卫视', r'宁夏卫视', r'青海卫视', r'新疆卫视', r'内蒙古卫视', r'西藏卫视', r'兵团卫视'],
            "电影": [r'电影'],
            "电视剧": [r'电视剧'],
            "体育": [r'体育'],
            "综艺": [r'综艺'],
            "少儿": [r'少儿', r'动画'],
            "新闻": [r'新闻'],
            "音乐": [r'音乐'],
            "财经": [r'财经'],
            "科教": [r'科教', r'科学', r'教育'],
            "生活": [r'生活'],
            "法制": [r'法制'],
            "旅游": [r'旅游'],
            "戏曲": [r'戏曲'],
            "购物": [r'购物'],
            "纪实": [r'纪实'],
            "农业": [r'农业'],
            "国际": [r'国际'],
            "其他": []
        })
        
        def categorize_channel(channel_name):
            """根据分类规则分类单个频道"""
            for cat, patterns in CATEGORY_RULES.items():
                for pattern in patterns:
                    if re.search(pattern, channel_name, re.IGNORECASE):
                        return cat
            return "其他"
        
        # 测试分类功能
        self.assertEqual(categorize_channel("CCTV-1 综合"), "央视")
        self.assertEqual(categorize_channel("CCTV-5 体育"), "央视")
        self.assertEqual(categorize_channel("北京卫视"), "卫视")
        self.assertEqual(categorize_channel("江苏卫视"), "卫视")
        self.assertEqual(categorize_channel("电影频道"), "电影")
        self.assertEqual(categorize_channel("体育频道"), "体育")
        self.assertEqual(categorize_channel("新闻频道"), "新闻")
        self.assertEqual(categorize_channel("未知频道"), "其他")


if __name__ == '__main__':
    unittest.main()
