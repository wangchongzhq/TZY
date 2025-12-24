#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试直播源验证工具的按钮响应速度
"""

import time
import requests
import socketio
import base64
import json
import os

sio = socketio.Client()

# 测试配置
TEST_FILE_PATH = r"C:\Users\Administrator\Documents\GitHub\TZY\109  live 1205 直播源 -减.txt"
SERVER_URL = "http://localhost:5001"

# 测试结果
results = {
    "start_button_response": None,
    "stop_button_response": None,
    "validation_start_time": None,
    "validation_stop_time": None
}

# Socket.IO事件处理
@sio.event
def connect():
    print("Connected to server")

@sio.event
def connection_established(data):
    print(f"Connection established: {data['message']}")

@sio.event
def validation_started(data):
    print(f"Validation started: {data['message']}")
    results["validation_start_time"] = time.time()
    if results["start_button_response"] is None:
        results["start_button_response"] = results["validation_start_time"] - results["start_button_click_time"]

@sio.event
def validation_stopped(data):
    print(f"Validation stopped: {data['message']}")
    results["validation_stop_time"] = time.time()
    if results["stop_button_response"] is None:
        results["stop_button_response"] = results["validation_stop_time"] - results["stop_button_click_time"]
    sio.disconnect()

@sio.event
def validation_error(data):
    print(f"Validation error: {data['message']}")
    sio.disconnect()

@sio.event
def validation_progress(data):
    print(f"Progress: {data['progress']}% ({data['processed']}/{data['total_channels']})")

@sio.event
def disconnect():
    print("Disconnected from server")

def test_button_responsiveness():
    """测试按钮响应速度"""
    global results
    
    print("测试按钮响应速度开始...")
    
    try:
        # 读取测试文件内容并转换为base64
        print(f"正在读取测试文件: {TEST_FILE_PATH}")
        with open(TEST_FILE_PATH, 'rb') as f:
            file_content = f.read()
        
        base64_content = base64.b64encode(file_content).decode('utf-8')
        file_extension = os.path.splitext(TEST_FILE_PATH)[1]
        
        # 连接到Socket.IO服务器
        sio.connect(SERVER_URL)
        time.sleep(1)  # 等待连接稳定
        
        # 测试开始按钮响应速度
        print("测试开始按钮响应速度...")
        results["start_button_click_time"] = time.time()
        
        # 发送开始验证请求
        validation_id = str(int(time.time() * 1000))
        sio.emit('start_validation', {
            'type': 'file',
            'file_data': {
                'content': base64_content,
                'extension': file_extension
            },
            'workers': 20,
            'timeout': 5,
            'validation_id': validation_id
        })
        
        # 等待验证开始，最多等待10秒
        start_wait_time = time.time()
        while results["validation_start_time"] is None and time.time() - start_wait_time < 10:
            time.sleep(0.1)
        
        if results["validation_start_time"] is None:
            print("验证开始超时")
            return False
        
        print(f"开始按钮响应时间: {results['start_button_response']:.3f} 秒")
        
        # 等待验证进行一段时间，然后测试停止按钮
        time.sleep(2)  # 让验证运行2秒
        
        print("测试停止按钮响应速度...")
        results["stop_button_click_time"] = time.time()
        
        # 发送停止验证请求
        sio.emit('stop_validation')
        
        # 等待验证停止，最多等待10秒
        stop_wait_time = time.time()
        while results["validation_stop_time"] is None and time.time() - stop_wait_time < 10:
            time.sleep(0.1)
        
        if results["validation_stop_time"] is None:
            print("验证停止超时")
            return False
        
        print(f"停止按钮响应时间: {results['stop_button_response']:.3f} 秒")
        
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        return False

def main():
    """主函数"""
    try:
        success = test_button_responsiveness()
        
        print("\n=== 测试结果 ===")
        if success:
            print(f"开始按钮响应时间: {results['start_button_response']:.3f} 秒")
            print(f"停止按钮响应时间: {results['stop_button_response']:.3f} 秒")
            
            # 判断响应速度是否符合要求
            if results['start_button_response'] < 1.0 and results['stop_button_response'] < 1.0:
                print("✅ 按钮响应速度符合要求 (均小于1秒)")
            else:
                print("⚠️  按钮响应速度仍需优化 (大于1秒)")
        else:
            print("❌ 测试失败")
            
    except KeyboardInterrupt:
        print("测试被用户中断")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    main()
