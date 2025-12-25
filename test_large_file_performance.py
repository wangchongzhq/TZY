#!/usr/bin/env python3
"""
大文件性能测试脚本，用于找出IPTV验证工具的性能卡点
"""

import sys
import os
import time
import tracemalloc
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from validator.iptv_validator import IPTVValidator

def test_file_reading_performance(file_path, file_type):
    """测试文件读取性能"""
    print(f"\n=== 测试文件读取性能: {file_path} ({file_type}) ===")
    
    # 记录内存使用情况
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # 初始化验证器
        validator = IPTVValidator(file_path, debug=True)
        
        print(f"文件类型检测: {validator.file_type}")
        
        # 定义进度回调
        def progress_callback(progress_data):
            if progress_data.get('stage'):
                print(f"阶段: {progress_data['stage']}")
            elif progress_data.get('progress'):
                if progress_data['progress'] % 10 == 0:  # 每10%输出一次
                    print(f"进度: {progress_data['progress']}%")
        
        # 读取文件
        if file_type == 'm3u':
            validator.read_m3u_file(progress_callback=progress_callback)
        elif file_type == 'txt':
            validator.read_txt_file(progress_callback=progress_callback)
        elif file_type == 'json':
            validator.read_json_file(progress_callback=progress_callback)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n读取完成!")
        print(f"耗时: {end_time - start_time:.2f} 秒")
        print(f"当前内存使用: {current / 10**6:.2f} MB")
        print(f"峰值内存使用: {peak / 10**6:.2f} MB")
        print(f"频道数量: {len(validator.channels)}")
        print(f"分类数量: {len(validator.categories)}")
        
        return {
            'time': end_time - start_time,
            'current_memory': current / 10**6,
            'peak_memory': peak / 10**6,
            'channel_count': len(validator.channels),
            'category_count': len(validator.categories)
        }
        
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_validation_performance(file_path, file_type, skip_resolution=False, max_workers=None):
    """测试频道验证性能"""
    print(f"\n=== 测试频道验证性能: {file_path} ({file_type}) ===")
    print(f"跳过分辨率检测: {skip_resolution}")
    if max_workers:
        print(f"最大工作线程: {max_workers}")
    
    # 先读取文件
    validator = IPTVValidator(file_path, debug=True, skip_resolution=skip_resolution)
    
    if file_type == 'm3u':
        validator.read_m3u_file()
    elif file_type == 'txt':
        validator.read_txt_file()
    elif file_type == 'json':
        validator.read_json_file()
    
    print(f"文件读取完成，共 {len(validator.channels)} 个频道")
    
    # 记录内存使用情况
    tracemalloc.start()
    start_time = time.time()
    
    # 定义详细的进度回调
    def progress_callback(progress_data):
        if progress_data.get('stage'):
            print(f"阶段: {progress_data['stage']} - {progress_data.get('message', '无详细信息')}")
        elif progress_data.get('progress'):
            if progress_data['progress'] % 5 == 0:  # 每5%输出一次
                print(f"验证进度: {progress_data['progress']}% - "
                      f"已处理: {progress_data.get('processed', 0)}/{len(validator.channels)}")
        elif progress_data.get('channel'):
            # 每100个频道输出一次详细信息
            if progress_data.get('processed', 0) % 100 == 0:
                channel = progress_data['channel']
                status = channel.get('status', '未知')
                print(f"频道 {progress_data.get('processed', 0)}: {channel.get('name', '未知')} - {status}")
    
    try:
        # 运行验证
        if max_workers:
            validator.validate_channels(progress_callback=progress_callback, max_workers=max_workers)
        else:
            validator.validate_channels(progress_callback=progress_callback)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n验证完成!")
        print(f"总耗时: {end_time - start_time:.2f} 秒")
        print(f"当前内存使用: {current / 10**6:.2f} MB")
        print(f"峰值内存使用: {peak / 10**6:.2f} MB")
        
        # 统计结果
        valid_count = sum(1 for c in validator.channels if c.get('status') == 'valid')
        invalid_count = sum(1 for c in validator.channels if c.get('status') == 'invalid')
        error_count = sum(1 for c in validator.channels if c.get('status') == 'error')
        
        print(f"验证结果:")
        print(f"  有效频道: {valid_count}")
        print(f"  无效频道: {invalid_count}")
        print(f"  错误频道: {error_count}")
        print(f"  总频道数: {len(validator.channels)}")
        
        return {
            'time': end_time - start_time,
            'current_memory': current / 10**6,
            'peak_memory': peak / 10**6,
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'error_count': error_count,
            'total_count': len(validator.channels)
        }
        
    except Exception as e:
        print(f"验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_step_by_step_performance(file_path, file_type):
    """逐步测试各阶段性能"""
    print(f"\n=== 逐步性能测试: {file_path} ({file_type}) ===")
    
    validator = IPTVValidator(file_path, debug=True, skip_resolution=True)
    
    # 1. 文件类型检测
    print("\n1. 测试文件类型检测性能")
    start_time = time.time()
    file_type = validator.file_type
    end_time = time.time()
    print(f"文件类型检测耗时: {end_time - start_time:.4f} 秒")
    print(f"检测到文件类型: {file_type}")
    
    # 2. 文件读取（仅统计频道数）
    print("\n2. 测试文件读取性能（仅统计频道数）")
    start_time = time.time()
    
    # 使用默认编码utf-8-sig
    encoding = 'utf-8-sig'
    
    if file_type == 'm3u':
        # 只统计频道数
        channel_count = 0
        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                if line.strip().startswith('#EXTINF:'):
                    channel_count += 1
    elif file_type == 'txt':
        # 只统计频道数
        channel_count = 0
        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(',', 2)
                    if len(parts) >= 2:
                        channel_count += 1
    
    end_time = time.time()
    print(f"频道数统计耗时: {end_time - start_time:.4f} 秒")
    print(f"频道数量: {channel_count}")
    
    # 3. 完整文件读取（解析频道信息）
    print("\n3. 测试完整文件读取性能（解析频道信息）")
    tracemalloc.start()
    start_time = time.time()
    
    if file_type == 'm3u':
        validator.read_m3u_file()
    elif file_type == 'txt':
        validator.read_txt_file()
    
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"完整读取耗时: {end_time - start_time:.2f} 秒")
    print(f"峰值内存使用: {peak / 10**6:.2f} MB")
    print(f"解析后频道数量: {len(validator.channels)}")
    
    return {
        'encoding_time': end_time - start_time,
        'count_time': end_time - start_time,
        'read_time': end_time - start_time,
        'peak_memory': peak / 10**6,
        'channel_count': len(validator.channels)
    }

def main():
    print("=== IPTV验证工具大文件性能测试 ===")
    
    # 测试文件路径
    test_files = [
        ('jieguo.m3u', 'm3u'),
        ('jieguo.txt', 'txt')
    ]
    
    for file_path, file_type in test_files:
        if not os.path.exists(file_path):
            print(f"\n警告: {file_path} 不存在，跳过测试")
            continue
        
        print(f"\n{'='*60}")
        print(f"开始测试: {file_path}")
        print(f"{'='*60}")
        
        # 1. 测试文件读取性能
        read_result = test_file_reading_performance(file_path, file_type)
        
        # 2. 测试逐步性能
        step_result = test_step_by_step_performance(file_path, file_type)
        
        # 3. 测试验证性能（跳过分辨率检测）
        validation_result = test_validation_performance(file_path, file_type, skip_resolution=True)
        
        # 保存测试结果
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'file_name': file_path,
            'file_type': file_type,
            'file_size': os.path.getsize(file_path),
            'read_result': read_result,
            'step_result': step_result,
            'validation_result': validation_result
        }
        
        # 保存到JSON文件
        with open(f"performance_test_{file_type}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n测试结果已保存到 performance_test_{file_type}.json")
        print(f"{'='*60}")
        print(f"测试完成: {file_path}")
        print(f"{'='*60}")

if __name__ == "__main__":
    main()
