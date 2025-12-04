import chardet
import os

# 检测文件编码的函数
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
    result = chardet.detect(raw_data)
    return result

# 检测所有TXT文件的编码
files = [f for f in os.listdir('.') if f.endswith('.txt')]
all_utf8 = True

for file in sorted(files):
    result = detect_encoding(file)
    if result['encoding'] not in ['utf-8', 'UTF-8-SIG', 'ascii']:
        all_utf8 = False
        print(f"✗ {file}: {result['encoding']} (confidence: {result['confidence']:.2f}) - 非UTF-8编码")
    else:
        print(f"✓ {file}: {result['encoding']} (confidence: {result['confidence']:.2f})")

if all_utf8:
    print("\n✓ 所有TXT文件都使用UTF-8编码")
else:
    print("\n✗ 发现非UTF-8编码的文件")
