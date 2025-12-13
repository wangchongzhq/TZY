import os

# 定义OUTPUT_DIR变量
OUTPUT_DIR = "output"

# 测试路径生成
output_file = os.path.join(OUTPUT_DIR, "iptv.m3u")
print(f"生成的路径: {output_file}")
print(f"绝对路径: {os.path.abspath(output_file)}")
print(f"目录是否存在: {os.path.exists(OUTPUT_DIR)}")

# 尝试创建文件
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(output_file, 'w') as f:
    f.write("测试内容")

print(f"文件是否创建在正确位置: {os.path.exists(output_file)}")
print(f"主目录下是否有文件: {os.path.exists('iptv.m3u')}")