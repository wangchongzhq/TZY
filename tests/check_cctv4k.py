# 检查输出文件中的CCTV4K/CCTV8K频道
print('=== Checking output/iptv.txt for CCTV4K/CCTV8K channels ===')

try:
    with open('output/iptv.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    cctv4k_found = False
    cctv8k_found = False
    
    for line in lines:
        if line.strip() and ',' in line:
            name, url = line.split(',', 1)
            name = name.strip()
            url = url.strip()
            
            if name == 'CCTV4K' and 'cctv4k' in url.lower():
                print(f'✓ Found CCTV4K channel: {name}, {url}')
                cctv4k_found = True
            elif name == 'CCTV8K' and 'cctv8k' in url.lower():
                print(f'✓ Found CCTV8K channel: {name}, {url}')
                cctv8k_found = True
    
    if not cctv4k_found:
        print('✗ No CCTV4K channels found with correct name')
    if not cctv8k_found:
        print('✗ No CCTV8K channels found with correct name')
    
    # 统计CCTV4和CCTV8的出现次数，看看是否有错误的频道名
    print('\n=== Checking for incorrect CCTV4/CCTV8 channel names ===')
    cctv4_count = 0
    cctv8_count = 0
    
    for line in lines:
        if line.strip() and ',' in line:
            name, url = line.split(',', 1)
            name = name.strip()
            url = url.strip()
            
            if name == 'CCTV4' and 'cctv4k' in url.lower():
                print(f'✗ Incorrect: {name}, {url}')
                cctv4_count += 1
            elif name == 'CCTV8' and 'cctv8k' in url.lower():
                print(f'✗ Incorrect: {name}, {url}')
                cctv8_count += 1
    
    if cctv4_count == 0 and cctv8_count == 0:
        print('✓ No incorrect CCTV4/CCTV8 channel names found')
    
except Exception as e:
    print(f'Error reading file: {e}')