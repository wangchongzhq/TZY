#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具模块单元测试
"""

import os
import sys
import unittest
from unittest.mock import patch, mock_open

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
from core.file_utils import (read_file, write_file, append_to_file, delete_file, 
                            copy_file, move_file, list_files, get_file_size, 
                            get_file_info, backup_file)


class TestFileUtils(unittest.TestCase):
    """文件处理工具测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.test_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.txt')
        self.test_content = "Test content for file utilities"
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试文件（如果存在）
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)
    
    @patch('builtins.open', new_callable=mock_open, read_data="Test content")
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_read_file(self, mock_isfile, mock_exists, mock_file):
        """测试读取文件内容"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # 调用测试函数
        content = read_file(self.test_file_path)
        
        # 验证结果
        self.assertEqual(content, "Test content")
        mock_file.assert_called_once_with(self.test_file_path, 'r', encoding='utf-8', errors='strict')
    
    @patch('builtins.open', new_callable=mock_open)
    def test_write_file(self, mock_file):
        """测试写入文件内容"""
        # 调用测试函数
        result = write_file(self.test_file_path, self.test_content)
        
        # 验证结果
        self.assertTrue(result)
        mock_file.assert_called_once_with(self.test_file_path, 'w', encoding='utf-8-sig')
        mock_file().write.assert_called_once_with(self.test_content)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_append_to_file(self, mock_makedirs, mock_exists, mock_file):
        """测试追加文件内容"""
        # 设置模拟返回值
        mock_exists.return_value = True
        
        # 调用测试函数
        result = append_to_file(self.test_file_path, self.test_content)
        
        # 验证结果
        self.assertTrue(result)
        mock_file.assert_called_once_with(self.test_file_path, 'a', encoding='utf-8-sig')
        mock_file().write.assert_called_once_with(self.test_content)
    
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_delete_file(self, mock_isfile, mock_exists, mock_remove):
        """测试删除文件"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # 调用测试函数
        result = delete_file(self.test_file_path)
        
        # 验证结果
        self.assertTrue(result)
        mock_remove.assert_called_once_with(self.test_file_path)
    
    @patch('shutil.copy2')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_copy_file(self, mock_makedirs, mock_isfile, mock_exists, mock_copy2):
        """测试复制文件"""
        dest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_copy.txt')
        
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # 调用测试函数
        result = copy_file(self.test_file_path, dest_path)
        
        # 验证结果
        self.assertTrue(result)
        mock_copy2.assert_called_once_with(self.test_file_path, dest_path)
        
        # 清理 - 由于我们模拟了所有操作，文件实际上并不存在，所以不需要删除
    
    @patch('shutil.move')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_move_file(self, mock_makedirs, mock_isfile, mock_exists, mock_move):
        """测试移动文件"""
        dest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_move.txt')
        
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # 调用测试函数
        result = move_file(self.test_file_path, dest_path)
        
        # 验证结果
        self.assertTrue(result)
        mock_move.assert_called_once_with(self.test_file_path, dest_path)
    
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.path.exists')
    def test_list_files(self, mock_exists, mock_isfile, mock_listdir):
        """测试列出文件"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_listdir.return_value = ["file1.txt", "file2.txt", "dir1", "file3.py"]
        mock_isfile.side_effect = lambda x: not x.endswith("dir1")  # 除了dir1都是文件
        
        # 调用测试函数
        files = list_files(os.path.dirname(os.path.abspath(__file__)))
        
        # 验证结果
        self.assertEqual(len(files), 3)  # 过滤掉目录
        
        # 测试按模式过滤 - 由于使用glob，我们不验证具体结果
    
    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_get_file_size(self, mock_isfile, mock_exists, mock_getsize):
        """测试获取文件大小"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024
        
        # 调用测试函数
        size = get_file_size(self.test_file_path)
        
        # 验证结果
        self.assertEqual(size, 1024)
        mock_getsize.assert_called_once_with(self.test_file_path)
    
    @patch('os.stat')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('core.file_utils.get_file_line_count')
    def test_get_file_info(self, mock_line_count, mock_isfile, mock_exists, mock_stat):
        """测试获取文件信息"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_line_count.return_value = 10
        mock_stat_obj = mock_stat.return_value
        mock_stat_obj.st_size = 1024
        mock_stat_obj.st_mtime = 1609459200
        mock_stat_obj.st_ctime = 1609459200
        mock_stat_obj.st_atime = 1609459200
        
        # 调用测试函数
        info = get_file_info(self.test_file_path)
        
        # 验证结果
        self.assertIsInstance(info, dict)
        self.assertEqual(info['size'], 1024)
        # 检查时间格式但不检查具体时区时间
        self.assertRegex(info['modified_time'], r'^2021-01-01 \d{2}:\d{2}:\d{2}$')
        self.assertRegex(info['created_time'], r'^2021-01-01 \d{2}:\d{2}:\d{2}$')
        self.assertRegex(info['accessed_time'], r'^2021-01-01 \d{2}:\d{2}:\d{2}$')
        mock_stat.assert_called_once_with(self.test_file_path)
    
    @patch('shutil.copy2')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_backup_file(self, mock_makedirs, mock_isfile, mock_exists, mock_copy2):
        """测试备份文件"""
        # 设置模拟返回值
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        # 调用测试函数
        backup_path = backup_file(self.test_file_path)
        
        # 验证结果
        self.assertIsNotNone(backup_path)
        self.assertTrue(mock_copy2.called)


if __name__ == '__main__':
    unittest.main()
