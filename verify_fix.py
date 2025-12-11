import os
import re

def verify_files():
    """验证文件生成是否成功，并检查是否包含本地频道数据"""
    print("=== 验证修复结果 ===")
    
    # 检查输出文件是否存在且有内容
    output_files = [
        'output/ip-tv.m3u',
        'output/ip-tv_i4.m3u',
        'output/ip-tv_i6.m3u',
        'output/ip-tv.txt',
        'output/ip-tv_i4.txt',
        'output/ip-tv_i6.txt'
    ]
    
    all_exist = True
    for file_path in output_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path}: 存在 ({size} 字节)")
        else:
            print(f"❌ {file_path}: 不存在")
            all_exist = False
    
    if not all_exist:
        return False
    
    # 检查配置文件
    print("\n=== 检查配置文件 ===")
    config_file = "config/config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 检查local_sources配置
        local_sources_files = []
        if '"local_sources": {' in config_content:
            # 使用正则表达式提取local_sources.files
            match = re.search(r'"local_sources":\s*\{[^}]*"files":\s*\[(.*?)\]', config_content, re.DOTALL)
            if match:
                files_str = match.group(1)
                local_sources_files = [f.strip('" ') for f in files_str.split(',') if f.strip()]
                
        print(f"配置文件中的本地源: {local_sources_files}")
        
        # 检查是否包含输出文件
        output_file_patterns = ['jieguo.m3u', 'jieguo_i4.m3u', 'jieguo_i6.m3u', 'jieguo_ipv4.m3u', 'jieguo_ipv6.m3u', 'ip-tv.m3u', 'ip-tv_i4.m3u', 'ip-tv_i6.m3u']
        has_output_files = False
        for file in local_sources_files:
            if any(pattern in file for pattern in output_file_patterns):
                print(f"❌ 配置文件包含输出文件: {file}")
                has_output_files = True
        
        if not has_output_files:
            print("✅ 配置文件不包含输出文件")
    else:
        print("❌ 配置文件不存在")
    
    # 检查IP-TV.py代码
    print("\n=== 检查IP-TV.py代码 ===")
    iptv_file = "IP-TV.py"
    if os.path.exists(iptv_file):
        with open(iptv_file, 'r', encoding='utf-8') as f:
            iptv_content = f.read()
        
        # 检查是否从配置文件加载local_sources
        if "get_config('local_sources.enabled'" in iptv_content and "get_config('local_sources.files'" in iptv_content:
            print("✅ 代码从配置文件加载local_sources")
        else:
            print("❌ 代码未从配置文件加载local_sources")
        
        # 检查是否有输出文件过滤逻辑
        if "output_files" in iptv_content and "if file_name in output_files:" in iptv_content:
            print("✅ 代码包含输出文件过滤逻辑")
        else:
            print("❌ 代码不包含输出文件过滤逻辑")
        
        # 检查是否有兼容文件生成逻辑
        if "兼容版本文件" in iptv_content and "shutil.copy" in iptv_content:
            print("✅ 代码包含兼容文件生成逻辑")
        else:
            print("❌ 代码不包含兼容文件生成逻辑")
    else:
        print("❌ IP-TV.py文件不存在")
    
    return True

if __name__ == "__main__":
    success = verify_files()
    if success:
        print("\n🎉 修复验证成功！文件生成功能已恢复正常。")
    else:
        print("\n❌ 修复验证失败！文件生成仍有问题。")
