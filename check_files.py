import os
import time

for filename in ['jieguo.m3u', 'jieguo.txt']:
    try:
        size = os.path.getsize(filename)
        mtime = os.path.getmtime(filename)
        print(f"{filename}: 大小={size} 字节, 最后修改时间={time.ctime(mtime)}")
    except FileNotFoundError:
        print(f"{filename}: 文件不存在")
    except Exception as e:
        print(f"{filename}: 错误 - {e}")