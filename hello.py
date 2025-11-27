#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 最简单的测试脚本 - 使用文件输出
try:
    # 将输出写入文件
    with open('hello_output.txt', 'w') as f:
        f.write('Hello, World!\n')
        f.write('Script executed successfully!\n')
    print "Hello, World!"  # 标准输出
    print "Script executed successfully!"
except Exception as e:
    print "Error:", e

