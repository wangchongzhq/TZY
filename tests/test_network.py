#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络请求模块单元测试
"""

import os
import sys
import unittest
import requests
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.network import fetch_content, fetch_multiple, check_url_availability, async_fetch_content


class TestNetwork(unittest.TestCase):
    """网络请求功能测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.test_url = "http://example.com/test"
        self.test_urls = [
            "http://example.com/test1",
            "http://example.com/test2",
            "http://example.com/test3"
        ]
    
    @patch('core.network.requests.get')
    def test_fetch_content_success(self, mock_get):
        """测试成功获取内容"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Content</body></html>"
        mock_get.return_value = mock_response
        
        # 调用测试函数
        result = fetch_content(self.test_url)
        
        # 验证结果
        self.assertEqual(result, mock_response.text)
        # 不验证完整的请求头，只验证是否包含User-Agent
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], self.test_url)
        self.assertIn('headers', call_args[1])
        self.assertIn('User-Agent', call_args[1]['headers'])
    
    @patch('core.network.requests.get')
    def test_fetch_content_failure(self, mock_get):
        """测试获取内容失败"""
        # 测试HTTP错误
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        # 调用测试函数
        result = fetch_content(self.test_url)
        
        # 验证结果
        self.assertIsNone(result)
        
        # 测试连接超时
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection timeout")
        result = fetch_content(self.test_url)
        self.assertIsNone(result)
    
    @patch('core.network.fetch_content')
    def test_fetch_multiple(self, mock_fetch_content):
        """测试批量获取内容"""
        # 设置模拟返回值
        mock_fetch_content.side_effect = ["Content 1", "Content 2", None]
        
        # 调用测试函数
        results = fetch_multiple(self.test_urls)
        
        # 验证结果
        self.assertEqual(len(results), 3)
        self.assertEqual(results[self.test_urls[0]], "Content 1")
        self.assertEqual(results[self.test_urls[1]], "Content 2")
        self.assertIsNone(results[self.test_urls[2]])
        
        # 验证调用次数
        self.assertEqual(mock_fetch_content.call_count, 3)
    
    @patch('core.network.requests.head')
    def test_check_url_availability(self, mock_head):
        """测试URL可用性检查"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_head.return_value = mock_response
        
        # 调用测试函数
        result = check_url_availability(self.test_url)
        
        # 验证结果
        self.assertTrue(result['available'])
        self.assertEqual(result['url'], self.test_url)
        self.assertEqual(result['status_code'], 200)
        # 不验证具体的超时时间，只验证是否设置了超时
        mock_head.assert_called_once()
        call_args = mock_head.call_args
        self.assertEqual(call_args[0][0], self.test_url)
        self.assertIn('timeout', call_args[1])
        self.assertIn('allow_redirects', call_args[1])
        self.assertTrue(call_args[1]['allow_redirects'])
        
        # 测试不可用的URL
        mock_response.status_code = 404
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_head.return_value = mock_response
        result = check_url_availability(self.test_url)
        self.assertFalse(result['available'])
        self.assertEqual(result['status_code'], 404)
    
    @patch('core.network.aiohttp.ClientSession.get')
    async def test_async_fetch_content(self, mock_get):
        """测试异步获取内容"""
        # 设置模拟返回值
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Async Test Content")
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # 调用测试函数
        result = await async_fetch_content(self.test_url)
        
        # 验证结果
        self.assertEqual(result, "Async Test Content")


if __name__ == '__main__':
    unittest.main()
