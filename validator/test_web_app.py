import socketio
import time
import base64
import os

# 创建SocketIO客户端
sio = socketio.Client()

# 事件处理函数
@sio.event
def connect():
    print('已连接到服务器')
    
    # 创建一个简单的测试文件
    test_content = "#EXTM3U\n#EXTINF:-1 tvg-id=\"\" tvg-name=\"测试频道\" tvg-logo=\"\" group-title=\"测试分类\"\nhttp://example.com/stream.m3u8"
    test_content_base64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
    
    # 发送验证请求
    sio.emit('start_validation', {
        'type': 'file',
        'file_data': {
            'content': test_content_base64,
            'extension': '.m3u'
        },
        'workers': 2,
        'timeout': 2
    })

@sio.event
def validation_started(data):
    print(f'验证开始: {data}')

@sio.event
def validation_progress(data):
    print(f'验证进度: {data}')

@sio.event
def validation_completed(data):
    print(f'验证完成: {data}')
    sio.disconnect()

@sio.event
def validation_error(data):
    print(f'验证错误: {data}')
    sio.disconnect()

@sio.event
def validation_stopped(data):
    print(f'验证停止: {data}')
    sio.disconnect()

@sio.event
def connection_established(data):
    print(f'连接建立: {data}')

@sio.event
def disconnect():
    print('已断开与服务器的连接')

# 运行测试
if __name__ == '__main__':
    try:
        sio.connect('http://localhost:5001')
        sio.wait()
    except Exception as e:
        print(f'测试失败: {e}')
