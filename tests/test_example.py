#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试示例文件
用于验证测试框架是否正常工作
"""

import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def test_basic_functionality():
    """测试基本功能"""
    logging.info("测试基本功能...")
    assert 1 + 1 == 2, "1 + 1 应该等于 2"
    assert len("hello") == 5, "'hello' 应该有 5 个字符"
    logging.info("✓ 基本功能测试通过")
    return True

def test_string_operations():
    """测试字符串操作"""
    logging.info("测试字符串操作...")
    assert "hello".upper() == "HELLO", "字符串大写转换失败"
    assert "HELLO".lower() == "hello", "字符串小写转换失败"
    assert "  test  ".strip() == "test", "字符串去空格失败"
    logging.info("✓ 字符串操作测试通过")
    return True

def test_list_operations():
    """测试列表操作"""
    logging.info("测试列表操作...")
    my_list = [1, 2, 3, 4, 5]
    assert len(my_list) == 5, "列表长度不正确"
    assert my_list[0] == 1, "列表第一个元素不正确"
    assert 3 in my_list, "列表应包含元素 3"
    logging.info("✓ 列表操作测试通过")
    return True

if __name__ == "__main__":
    logging.info("开始运行示例测试...")
    
    try:
        # 运行所有测试
        test_basic_functionality()
        test_string_operations()
        test_list_operations()
        
        logging.info("\n🎉 所有示例测试通过！")
        sys.exit(0)
    except AssertionError as e:
        logging.error(f"✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"✗ 测试过程中发生错误: {e}")
        sys.exit(1)
