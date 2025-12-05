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


if __name__ == '__main__':
    unittest.main()
