import chardet

# 检测IPTV.py文件的编码
with open('IPTV.py', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"IPTV.py文件编码: {result['encoding']}, 置信度: {result['confidence']}")

# 检测jieguo.txt文件的编码
with open('jieguo.txt', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"jieguo.txt文件编码: {result['encoding']}, 置信度: {result['confidence']}")

# 检测jieguo.m3u文件的编码
with open('jieguo.m3u', 'rb') as f:
    result = chardet.detect(f.read())
    print(f"jieguo.m3u文件编码: {result['encoding']}, 置信度: {result['confidence']}")
