import sys
import os
import importlib.util

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 备份原始IP-TV.py文件
print("正在备份原始IP-TV.py文件...")
with open("IP-TV.py", "r", encoding="utf-8") as f:
    original_content = f.read()

# 在update_iptv_sources函数中添加调试信息
print("正在修改IP-TV.py文件，添加调试信息...")

# 找到update_iptv_sources函数的开始位置
start_pos = original_content.find("def update_iptv_sources():")
if start_pos == -1:
    print("❌ 找不到update_iptv_sources函数")
    sys.exit(1)

# 在函数开始处添加调试信息
debug_content = original_content[:start_pos] + "def update_iptv_sources():\n    \"\"\"更新IPTV直播源\"\"\"\n    print(\"\\n🚀 IPTV直播源自动生成工具\")\n    print(f\"📅 运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\")\n"

# 找到文件生成部分并添加调试信息
# 找到generate_files函数定义
files_pos = original_content.find("def generate_files(channels, m3u_filename, txt_filename, version_name):")
if files_pos != -1:
    # 在generate_files函数内部添加调试信息
    files_debug = "    def generate_files(channels, m3u_filename, txt_filename, version_name):\n        \"\"\"生成指定版本的M3U和TXT文件\"\"\"\n        print(f\"\\n📁 开始生成{version_name}文件 - M3U: {m3u_filename}, TXT: {txt_filename}\n")\n        print(f\"   输入频道数: {sum(len(chans) for _, chans in channels.items())} 个频道，{len(channels)} 个分类\")\n"
    debug_content = debug_content[:files_pos] + files_debug + original_content[files_pos + len("def generate_files(channels, m3u_filename, txt_filename, version_name):") + 1:]

# 保存修改后的文件
with open("IP-TV_debug.py", "w", encoding="utf-8") as f:
    f.write(debug_content)

print("✅ 已生成调试版本IP-TV_debug.py")

# 运行调试版本
print("\n开始运行调试版本...")
print("="*60)

try:
    spec = importlib.util.spec_from_file_location("ip_tv_debug", "IP-TV_debug.py")
    ip_tv_debug = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ip_tv_debug)
    
    # 运行update_iptv_sources函数
    result = ip_tv_debug.update_iptv_sources()
    print(f"\n{'='*60}")
    print(f"调试完成，最终结果: {result}")
    print(f"{'='*60}")
    
except Exception as e:
    print(f"\n{'='*60}")
    print(f"❌ 运行调试版本时发生错误: {e}")
    import traceback
    traceback.print_exc()
    print(f"{'='*60}")
    
finally:
    # 清理临时文件
    if os.path.exists("IP-TV_debug.py"):
        os.remove("IP-TV_debug.py")
        print("\n✅ 已清理临时文件")