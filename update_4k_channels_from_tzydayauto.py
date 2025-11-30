import re
import time

# 从tzydayauto.txt中提取4K直播源
def extract_4k_channels():
    print("🔍 正在从tzydayauto.txt中提取4K直播源...")
    
    try:
        with open('tzydayauto.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式匹配4K频道
        # 匹配格式：频道名称（包含4K）,URL
        pattern = r'([^,]+4K[^,]*),([^\n]+)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        print(f"✅ 成功提取到 {len(matches)} 个4K直播源")
        return matches
    except Exception as e:
        print(f"❌ 提取4K直播源时出错: {e}")
        return []

# 更新4K_uhd_channels.txt文件
def update_4k_channels_file(channels):
    print("\n📝 正在更新4K_uhd_channels.txt文件...")
    
    try:
        with open('4K_uhd_channels.txt', 'w', encoding='utf-8') as f:
            # 写入文件头部
            f.write("# 4K超高清直播源列表\n")
            f.write(f"# 更新时间: {time.strftime('%Y-%m-%d')}\n")
            f.write(f"# 共包含 {len(channels)} 个4K超高清频道\n")
            f.write("\n")
            
            # 写入4K央视频道部分
            f.write("# 4K央视频道\n")
            f.write("\n")
            
            # 写入实际的4K频道
            for i, (name, url) in enumerate(channels, 1):
                f.write(f"{name},{url}\n")
                if i % 20 == 0:
                    print(f"🔄 已写入 {i} 个频道...")
            
            f.write("\n")
            f.write("# 以下是GitHub直播源URL（需要时可启用）\n")
            f.write("# 注意：以下URL可能需要验证后才能使用\n")
        
        print(f"✅ 成功更新4K_uhd_channels.txt文件，添加了 {len(channels)} 个4K直播源")
        return True
    except Exception as e:
        print(f"❌ 更新文件时出错: {e}")
        return False

# 主函数
def main():
    print("🚀 4K直播源提取与更新工具启动")
    
    # 提取4K直播源
    channels = extract_4k_channels()
    
    if not channels:
        print("❌ 没有找到有效的4K直播源，程序退出")
        return
    
    # 去重（基于URL）
    unique_channels = []
    seen_urls = set()
    
    for name, url in channels:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_channels.append((name, url))
    
    if len(unique_channels) < len(channels):
        print(f"🔍 去重处理：从 {len(channels)} 个频道中去重得到 {len(unique_channels)} 个唯一频道")
    
    # 更新文件
    if update_4k_channels_file(unique_channels):
        print("\n🏆 任务完成！")
        print(f"📊 最终统计：")
        print(f"   - 提取到的4K直播源数量：{len(channels)}")
        print(f"   - 去重后的4K直播源数量：{len(unique_channels)}")
        print(f"   - 成功写入文件：4K_uhd_channels.txt")
    
if __name__ == "__main__":
    main()
