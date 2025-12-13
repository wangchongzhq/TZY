import chardet

# 读取文件内容
with open('temp_live.txt', 'rb') as f:
    content = f.read()

# 检测编码
detected_encoding = chardet.detect(content)['encoding']
print('Detected encoding:', detected_encoding)

# 尝试解码并查找CCTV4K/CCTV8K频道
print('=== Looking for CCTV4K/CCTV8K channels ===')
try:
    decoded_content = content.decode(detected_encoding or 'utf-8')
    lines = decoded_content.split('\n')
    
    # 打印前50行中包含CCTV4K/CCTV8K的行
    found = False
    for i, line in enumerate(lines[:50]):
        line = line.strip()
        if 'CCTV4K' in line or 'CCTV8K' in line or 'cctv4k' in line or 'cctv8k' in line:
            print(f'Line {i+1}: {line}')
            found = True
    
    if not found:
        print('No CCTV4K/CCTV8K channels found in the first 50 lines.')
        
    # 打印一些示例行以了解格式
    print('\n=== First 10 lines (decoded) ===')
    for i, line in enumerate(lines[:10]):
        print(f'Line {i+1}: {line.strip()}')
        
except Exception as e:
    print(f'Error decoding file: {e}')
