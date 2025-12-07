import re
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入tvzy模块和配置管理器
try:
    from tvzy import categorize_channel, ChannelInfo
    from core.config import get_config
except ImportError as e:
    print(f"导入模块失败：{e}")
    sys.exit(1)

# 从配置获取本地源开关设置
local_sources_enabled = get_config('local_sources.enabled', True)
local_sources_files = get_config('local_sources.files', [])

def test_categorization():
    """测试频道分类逻辑"""
    print("\n============================================================")
    print("测试频道分类逻辑：")
    print("============================================================")
    
    try:
        from tvzy import CHANNEL_CATEGORIES
        # 打印当前的分类配置
        print("当前的CHANNEL_CATEGORIES配置：")
        for category, channels in CHANNEL_CATEGORIES.items():
            print(f"  {category}: {len(channels)}个频道")
    except ImportError:
        print("无法获取CHANNEL_CATEGORIES配置")
    
    # 测试频道列表
    test_channels = [
        "凤凰中文",
        "凤凰资讯", 
        "凤凰香港",
        "凤凰电影",
        "山东卫视",
        "浙江卫视"
    ]
    
    print("\n频道分类测试结果：")
    for channel_name in test_channels:
        channel = ChannelInfo(channel_name, "http://example.com")
        category = categorize_channel(channel)
        print(f"  频道 '{channel_name}' -> 分类 '{category}'")

def main():
    # 首先测试分类逻辑
    test_categorization()
    
    # 定义要搜索的关键词 - 只检查凤凰卫视频道
    keywords = ['凤凰中文', '凤凰资讯', '凤凰香港', '凤凰电影']
    
    # 检查本地源开关
    if not local_sources_enabled:
        print("\n============================================================")
        print("本地源功能已关闭，跳过检查本地文件")
        print("===========================================================")
        return
    
    # 检查文件是否在允许的本地源列表中
    local_file = 'tzydauto.txt'
    if local_file not in local_sources_files:
        print(f"\n============================================================")
        print(f"文件 '{local_file}' 不在允许的本地源列表中，跳过检查")
        print("===========================================================")
        return
    
    # 读取文件内容
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误：找不到文件 '{local_file}'")
        return
    
    # 将内容按行分割
    lines = content.splitlines()
    
    # 遍历每个关键词，找出包含该关键词的行
    for keyword in keywords:
        print(f"\n============================================================")
        print(f"检查含有 '{keyword}' 的内容的分类情况：")
        print(f"============================================================")
        
        found = False
        current_category = None
        category_line = None
        
        for i, line in enumerate(lines):
            # 检查是否是分类标题
            if line.startswith('# '):
                current_category = line[2:]
                category_line = i + 1
            # 检查是否包含关键词
            elif keyword in line:
                found = True
                print(f"\n{keyword} 在第{i+1}行，所属分类：")
                if current_category:
                    print(f"   {category_line:3d}: --- # {current_category} ---")
                print(f"{i+1:4d}: >>> {line}")
        
        if not found:
            print(f"\n未找到含有 '{keyword}' 的内容")

if __name__ == "__main__":
    main()