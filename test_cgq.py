#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本，用于捕获get_cgq_sources.py的执行异常
"""

import sys
import traceback
import os

print("测试get_cgq_sources.py脚本")
print("当前工作目录:", os.getcwd())
print("Python版本:", sys.version)

# 导入并执行main函数
try:
    print("\n尝试导入get_cgq_sources模块...")
    import get_cgq_sources
    print("导入成功!")
    
    print("\n尝试执行main函数...")
    result = get_cgq_sources.main()
    print(f"main函数执行结果: {result}")
    
    print("\n脚本执行完成，无异常!")
    
except Exception as e:
    print("\n捕获到异常:")
    print(f"异常类型: {type(e).__name__}")
    print(f"异常信息: {str(e)}")
    print("\n详细堆栈信息:")
    traceback.print_exc()
