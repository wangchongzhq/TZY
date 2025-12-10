import sys
import os
import importlib.util

# 确保使用UTF-8编码
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 动态导入IP-TV模块
print("正在导入IP-TV模块...")
try:
    spec = importlib.util.spec_from_file_location("ip_tv", "IP-TV.py")
    ip_tv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ip_tv)
    print("成功导入IP-TV模块")
except Exception as e:
    print(f"导入IP-TV模块失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 创建测试频道数据
print("\n创建测试频道数据...")
test_channels = {
    "4K频道": [
        ("湖南卫视4K", "http://streaming.tv/hunan4k.m3u8"),
        ("中央电视台4K", "http://cdn.live.com/cctv4k.m3u8")
    ],
    "央视频道": [
        ("CCTV1", "http://live.tv/cctv1.m3u8"),
        ("CCTV2", "http://live.tv/cctv2.m3u8")
    ],
    "卫视频道": [
        ("湖南卫视", "http://streaming.tv/hunan.m3u8"),
        ("浙江卫视", "http://streaming.tv/zhejiang.m3u8")
    ]
}

# 测试直接调用generate_files函数
print("\n测试直接调用generate_files函数...")
try:
    # 定义输出文件路径，与主程序相同
    output_file_m3u = os.path.join("output", "jieguo_merged.m3u")
    output_file_txt = os.path.join("output", "jieguo_merged.txt")
    
    # 获取generate_files函数（需要从update_iptv_sources函数中提取）
    # 由于generate_files是update_iptv_sources函数内部定义的，我们需要重新实现它
    def test_generate_files(channels, m3u_filename, txt_filename, version_name):
        """测试用的generate_files函数"""
        file_success = True
        
        if ip_tv.generate_m3u_file(channels, m3u_filename):
            print(f"✅ 成功生成{version_name}M3U文件: {m3u_filename}")
        else:
            print(f"❌ 生成{version_name}M3U文件失败: {m3u_filename}")
            file_success = False
        
        if ip_tv.generate_txt_file(channels, txt_filename):
            print(f"✅ 成功生成{version_name}TXT文件: {txt_filename}")
        else:
            print(f"❌ 生成{version_name}TXT文件失败: {txt_filename}")
            file_success = False
        
        return file_success
    
    # 调用测试函数
    result = test_generate_files(test_channels, output_file_m3u, output_file_txt, "测试版")
    print(f"\ngenerate_files返回值: {result}")
    
    # 检查文件是否生成
    print("\n检查生成的文件:")
    if os.path.exists(output_file_m3u):
        print(f"{output_file_m3u} - 大小: {os.path.getsize(output_file_m3u)} 字节")
    else:
        print(f"{output_file_m3u} - 未生成")
    
    if os.path.exists(output_file_txt):
        print(f"{output_file_txt} - 大小: {os.path.getsize(output_file_txt)} 字节")
        # 显示文件内容
        with open(output_file_txt, "r", encoding="utf-8") as f:
            content = f.read()
            print("\n文件内容预览:")
            print(content[:500] + ("..." if len(content) > 500 else ""))
    else:
        print(f"{output_file_txt} - 未生成")
        
except Exception as e:
    print(f"\n执行过程中发生错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成")