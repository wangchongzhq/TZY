#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import tempfile
import threading
from validator.iptv_validator import IPTVValidator

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_file(file_path):
    """创建一个包含大量频道的测试文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        # 创建1000个测试频道，其中一些包含外部URL
        for i in range(1000):
            if i % 100 == 0:
                # 添加一个外部URL频道，指向一个可能很慢的资源
                f.write(f'#EXTINF:-1 tvg-name="外部频道{i}" group-title="外部",外部频道{i}\n')
                f.write('https://example.com/slow_resource.m3u\n')
            else:
                # 添加一个普通频道
                f.write(f'#EXTINF:-1 tvg-name="测试频道{i}" group-title="测试",测试频道{i}\n')
                f.write(f'http://example.com/channel{i}.ts\n')

def test_stop_mechanism():
    """测试停止机制是否能快速响应"""
    print("开始测试停止机制...")
    
    # 创建临时测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as temp_file:
        temp_file_path = temp_file.name
    
    try:
        # 创建测试内容
        create_test_file(temp_file_path)
        print(f"创建测试文件: {temp_file_path}")
        
        # 初始化验证器
        validator = IPTVValidator(temp_file_path, debug=True)
        
        # 定义进度回调
        def progress_callback(data):
            print(f"进度: {data['progress']}%, 阶段: {data['stage']}")
        
        # 启动验证线程
        validation_thread = threading.Thread(target=validator.validate_channels, args=(progress_callback,))
        validation_thread.start()
        
        # 运行5秒后发送停止请求
        time.sleep(5)
        print("发送停止请求...")
        start_stop_time = time.time()
        validator.stop()
        
        # 等待验证线程结束
        validation_thread.join(timeout=10)
        stop_duration = time.time() - start_stop_time
        
        if validation_thread.is_alive():
            print("ERROR: 验证线程未能在10秒内停止")
            return False
        else:
            print(f"SUCCESS: 验证线程已停止，停止耗时: {stop_duration:.2f}秒")
            if stop_duration < 2:
                print("SUCCESS: 停止请求响应迅速")
            else:
                print(f"WARNING: 停止请求响应较慢，耗时{stop_duration:.2f}秒")
            return True
            
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    success = test_stop_mechanism()
    sys.exit(0 if success else 1)
