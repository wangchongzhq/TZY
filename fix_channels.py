# 最简单的方法：手动编辑文件内容

# 读取文件
with open('4K_uhd_channels.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 直接修改GitHub URL部分
# 我们只保留前5个 iptv-org/iptv 仓库的URL
new_lines = []
iptv_org_count = 0
liuminghang_count = 0
imDazui_count = 0

for line in lines:
    # 检查是否是 iptv-org/iptv 仓库的URL
    if 'raw.githubusercontent.com/iptv-org/iptv/' in line:
        if iptv_org_count < 5:
            new_lines.append(line)
            iptv_org_count += 1
            print(f"保留 iptv-org/iptv URL ({iptv_org_count}/5): {line.strip()}")
        else:
            print(f"跳过 iptv-org/iptv URL: {line.strip()}")
    # 检查是否是 liuminghang/IPTV 仓库的URL
    elif 'raw.githubusercontent.com/liuminghang/IPTV/' in line:
        if liuminghang_count < 5:
            new_lines.append(line)
            liuminghang_count += 1
            print(f"保留 liuminghang/IPTV URL ({liuminghang_count}/5): {line.strip()}")
        else:
            print(f"跳过 liuminghang/IPTV URL: {line.strip()}")
    # 检查是否是 imDazui/Tvlist-awesome-m3u-m3u8 仓库的URL
    elif 'raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/' in line:
        if imDazui_count < 5:
            new_lines.append(line)
            imDazui_count += 1
            print(f"保留 imDazui URL ({imDazui_count}/5): {line.strip()}")
        else:
            print(f"跳过 imDazui URL: {line.strip()}")
    # 其他行都保留
    else:
        new_lines.append(line)

# 写入文件
with open('4K_uhd_channels.txt', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("\n处理完成！")
print(f"保留的URL数量：")
print(f"- iptv-org/iptv: {iptv_org_count} 个")
print(f"- liuminghang/IPTV: {liuminghang_count} 个")
print(f"- imDazui/Tvlist-awesome-m3u-m3u8: {imDazui_count} 个")
print(f"总文件行数：{len(new_lines)}")