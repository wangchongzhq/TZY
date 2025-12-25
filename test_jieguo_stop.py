#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import threading
from validator.iptv_validator import IPTVValidator

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_jieguo_stop():
    """测试jieguo.m3u文件的停止机制"""
    print("开始测试jieguo.m3u文件的停止机制...")
    print("按Enter键发送停止请求...")
    
    # jieguo.m3u文件路径
    file_path = "C:\\Users\\Administrator\\Documents\\GitHub\\TZY\\jieguo.m3u"
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 - {file_path}")
        return False
    
    try:
        # 初始化验证器，禁用分辨率检查以加快测试
        validator = IPTVValidator(file_path, debug=True, skip_resolution=True)
        
        # 定义进度回调
        def progress_callback(data):
            print(f"进度: {data['progress']}%, 阶段: {data['stage']}, 已处理: {data.get('processed', 0)}/{data.get('total_channels', 0)}")
            if 'total_external' in data:
                print(f"  外部URL: {data['processed_external']}/{data['total_external']}")
        
        # 先解析M3U文件
        print("开始解析M3U文件...")
        validator.read_m3u_file(progress_callback)
        
        # 启动验证线程
        validation_thread = threading.Thread(target=validator.validate_channels, args=(progress_callback,))
        validation_thread.start()
        
        # 等待10秒后自动发送停止请求
        print("等待10秒后自动发送停止请求...")
        time.sleep(10)
        
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
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jieguo_stop()
    sys.exit(0 if success else 1)
