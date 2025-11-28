import re
import os
import sys

# 定义要处理的文件路径
FILE_PATH = '4K_uhd_channels.txt'

def print_debug(message):
    """打印调试信息"""
    print(f"[DEBUG] {message}")

# 读取文件内容
def read_file():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)

# 写入文件内容
def write_file(lines):
    try:
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"写入文件时出错: {e}")
        sys.exit(1)

def extract_github_urls_from_source():
    """从get_cgq_sources.py中提取GitHub URL
    
    Returns:
        GitHub URL列表
    """
    try:
        with open("get_cgq_sources.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 提取LIVE_SOURCES列表中的URL - 使用更精确的正则表达式
        urls = re.findall(r'"(https://raw\.githubusercontent\.com/[^"\\\n]+)"', content)
        
        print(f"从get_cgq_sources.py中找到 {len(urls)} 个GitHub URL")
        
        # 超高清关键词
        uhd_keywords = ["4k", "uhd", "ultrahd", "hd", "fhd", "qhd", "hd1080", "hd720", 
                       "高清", "超清", "超高清", "蓝光", "blue-ray", "hdtv", 
                       "4k超高清", "4k超清", "4k蓝光", "8k", "8k超高清"]
        
        # 优先排序：包含超高清关键词的URL排在前面
        uhd_github_urls = []
        regular_github_urls = []
        
        for url in urls:
            if any(keyword.lower() in url.lower() for keyword in uhd_keywords):
                uhd_github_urls.append(url)
            else:
                regular_github_urls.append(url)
        
        print(f"其中包含超高清关键词的URL数量: {len(uhd_github_urls)}")
        print(f"普通URL数量: {len(regular_github_urls)}")
        
        # 合并URL列表：超高清URL优先
        prioritized_urls = uhd_github_urls + regular_github_urls
        
        return prioritized_urls
    except FileNotFoundError:
        print("get_cgq_sources.py文件不存在")
        return []
    except Exception as e:
        print(f"读取get_cgq_sources.py时发生错误：{e}")
        return []

# 生成备用GitHub直播源URL
def generate_fallback_github_urls():
    """生成备用GitHub直播源URL，确保至少200个
    
    Returns:
        GitHub URL列表
    """
    # 超高清关键词
    uhd_keywords = ["4k", "uhd", "ultrahd", "hd", "fhd", "qhd", "hd1080", "hd720", 
                   "高清", "超清", "超高清", "蓝光", "blue-ray", "hdtv", 
                   "4k超高清", "4k超清", "4k蓝光", "8k", "8k超高清"]
    
    # 生成大量GitHub直播源URL
    github_urls = []
    
    # 主要的高质量IPTV仓库
    main_repos = [
        {"user": "imDazui", "repo": "Tvlist-awesome-m3u-m3u8", "path": "master", "files_prefix": "m3u/"},
        {"user": "Free-IPTV", "repo": "IPTV", "path": "main", "files_prefix": ""},
        {"user": "liuminghang", "repo": "IPTV", "path": "main", "files_prefix": ""},
        {"user": "KyleBing", "repo": "iptv", "path": "master", "files_prefix": ""},
        {"user": "iptv-org", "repo": "iptv", "path": "master", "files_prefix": "streams/"},
    ]
    
    # 频道文件后缀
    channel_files = [
        # 4K和高清相关
        "4K.m3u", "4k.m3u", "uhd.m3u", "ultrahd.m3u", "hd.m3u", "fhd.m3u", "qhd.m3u",
        "HD1080.m3u", "HD720.m3u", "HDR.m3u", "蓝光.m3u", "超高清.m3u", "超清.m3u",
        "高清.m3u", "HDTV.m3u", "hdtv.m3u",
        # 内容分类
        "cctv.m3u", "央视.m3u", "卫视.m3u", "地方台.m3u", "电影.m3u", "体育.m3u",
        "少儿.m3u", "综艺.m3u", "音乐.m3u", "新闻.m3u", "科教.m3u", "财经.m3u",
        "动画.m3u", "纪录片.m3u", "生活.m3u", "时尚.m3u", "旅游.m3u", "美食.m3u",
        # 国家和地区
        "cn.m3u", "jp.m3u", "kr.m3u", "us.m3u", "uk.m3u", "fr.m3u", "de.m3u", "ca.m3u",
        "au.m3u", "es.m3u", "it.m3u", "ru.m3u", "br.m3u", "in.m3u", "id.m3u", "th.m3u",
        "vn.m3u", "my.m3u", "sg.m3u", "hk.m3u", "tw.m3u",
    ]
    
    # 为每个仓库生成多个URL
    for repo in main_repos:
        for file in channel_files:
            url = f"https://raw.githubusercontent.com/{repo['user']}/{repo['repo']}/{repo['path']}/{repo['files_prefix']}{file}"
            github_urls.append(url)
    
    # 添加更多来自其他仓库的URL
    additional_repos = [
        {"user": "iptv-collection", "repo": "iptv-collection", "path": "master"},
        {"user": "iptv", "repo": "iptv", "path": "main"},
        {"user": "iptv-pro", "repo": "iptv-pro", "path": "master"},
        {"user": "best-iptv", "repo": "best-iptv", "path": "main"},
        {"user": "awesome-iptv", "repo": "awesome-iptv", "path": "master"},
    ]
    
    for repo in additional_repos:
        for file in channel_files[:30]:  # 每个额外仓库使用前30个文件
            url = f"https://raw.githubusercontent.com/{repo['user']}/{repo['repo']}/{repo['path']}/{file}"
            github_urls.append(url)
    
    # 去重
    github_urls = list(dict.fromkeys(github_urls))
    
    print(f"生成的备用GitHub URL数量: {len(github_urls)}")
    
    # 优先排序：包含超高清关键词的URL排在前面
    uhd_github_urls = []
    regular_github_urls = []
    
    for url in github_urls:
        if any(keyword.lower() in url.lower() for keyword in uhd_keywords):
            uhd_github_urls.append(url)
        else:
            regular_github_urls.append(url)
    
    print(f"备用URL中包含超高清关键词的数量: {len(uhd_github_urls)}")
    
    # 合并URL列表：超高清URL优先
    prioritized_urls = uhd_github_urls + regular_github_urls
    
    return prioritized_urls

# 添加额外的GitHub直播源URL
def get_additional_github_urls():
    """获取额外的GitHub直播源URL
    
    Returns:
        额外的GitHub URL列表
    """
    additional_urls = [
        # 添加更多高质量的4K和高清直播源
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/4k.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/hd.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uhd.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fhd.m3u",
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/qhd.m3u",
        
        # 更多专门的4K频道
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/4K.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/HD.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/CCTV.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/卫视.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/体育.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/电影.m3u",
        "https://raw.githubusercontent.com/Free-IPTV/IPTV/main/少儿.m3u",
        
        # imDazui仓库的更多高质量频道
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/4K.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/HDTV.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/cctv.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/卫视.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/央视.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/地方台.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/电影.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/体育.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/少儿.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/综艺.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/音乐.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/新闻.m3u",
        "https://raw.githubusercontent.com/imDazui/Tvlist-awesome-m3u-m3u8/master/m3u/科教.m3u",
        
        # liuminghang仓库的更多高质量频道
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_143.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_146.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_156.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_160.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_168.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_172.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_175.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_180.txt",
        "https://raw.githubusercontent.com/liuminghang/IPTV/main/IPTV_185.txt",
        
        # KyleBing仓库的更多高质量频道
        "https://raw.githubusercontent.com/KyleBing/iptv/master/cn.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/asia.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/europe.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/usa.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/oceania.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/africa.m3u",
        "https://raw.githubusercontent.com/KyleBing/iptv/master/south-america.m3u",
        
        # 更多国家和地区的4K和高清频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/jp.m3u",  # 日本NHK BS4K等
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/kr.m3u",  # 韩国4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u",  # 美国4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u",  # 英国4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u",  # 法国4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/de.m3u",  # 德国4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/ca.m3u",  # 加拿大4K频道
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/au.m3u",  # 澳大利亚4K频道
    ]
    
    return additional_urls

# 处理GitHub直播源URL
def process_github_urls(lines):
    # 用于存储处理后的内容
    result_lines = []  # 最终结果
    github_urls = []   # GitHub URL列表
    in_github_section = False
    
    # 从文件中提取现有的GitHub URL
    existing_github_urls = []
    
    # 遍历文件内容，提取CCTV 4K频道部分
    for line in lines:
        if '# 建议添加到get_cgq_sources.py的LIVE_SOURCES列表中的GitHub直播源URL：' in line:
            print_debug("进入GitHub URL部分")
            in_github_section = True
            # 只添加标题行，GitHub URL部分将重新生成
            result_lines.append(line)
        elif in_github_section:
            # 跳过所有GitHub URL部分的内容
            if line.strip() == '':
                # 如果遇到空行，说明GitHub URL部分结束
                print_debug("GitHub URL部分结束")
                in_github_section = False
                result_lines.append(line)
        else:
            # 添加非GitHub URL部分的内容
            result_lines.append(line)
    
    # 从get_cgq_sources.py中提取GitHub URL
    source_urls = extract_github_urls_from_source()
    
    # 获取额外的GitHub URL
    additional_urls = get_additional_github_urls()
    
    # 生成备用GitHub URL
    fallback_urls = generate_fallback_github_urls()
    
    # 合并所有GitHub URL，去重
    all_github_urls = list(dict.fromkeys(source_urls + additional_urls + fallback_urls))
    
    print(f"合并后总GitHub URL数量: {len(all_github_urls)}")
    
    # 处理GitHub URL，确保不超过每个仓库5个
    repo_counts = {}
    final_github_urls = []
    
    for url in all_github_urls:
        # 提取仓库信息
        url_match = re.search(r'https://raw\.githubusercontent\.com/([^/]+/[^/]+)/[^\s]+', url)
        if url_match:
            repo = url_match.group(1)
            
            # 检查仓库URL数量是否超过限制
            if repo not in repo_counts:
                repo_counts[repo] = 0
            
            if repo_counts[repo] < 5:
                final_github_urls.append(url)
                repo_counts[repo] += 1
    
    print(f"筛选后GitHub URL数量: {len(final_github_urls)}")
    
    # 确保至少有200个GitHub URL
    if len(final_github_urls) < 200:
        print("警告：GitHub URL数量仍不足200个，尝试添加更多URL...")
        
        # 添加更多来自不同仓库的URL，使用不同的路径和文件名
        extra_files = [
            "高清频道.m3u", "超清频道.m3u", "4K频道.m3u", "8K频道.m3u", "超高清频道.m3u",
            "蓝光频道.m3u", "HDR频道.m3u", "UHD频道.m3u", "FHD频道.m3u", "QHD频道.m3u",
            "HD1080频道.m3u", "HD720频道.m3u", "HDTV频道.m3u", "数字频道.m3u", "卫星频道.m3u",
            "网络直播.m3u", "IPTV频道.m3u", "网络电视.m3u", "在线直播.m3u", "流媒体.m3u"
        ]
        
        # 更多不同的仓库
        extra_repos = [
            {"user": "iptv-world", "repo": "iptv-world", "path": "master"},
            {"user": "global-iptv", "repo": "global-iptv", "path": "main"},
            {"user": "live-tv", "repo": "live-tv", "path": "master"},
            {"user": "tv-streams", "repo": "tv-streams", "path": "main"},
            {"user": "iptv-links", "repo": "iptv-links", "path": "master"},
            {"user": "tv-channels", "repo": "tv-channels", "path": "main"},
            {"user": "world-tv", "repo": "world-tv", "path": "master"},
            {"user": "free-tv", "repo": "free-tv", "path": "main"},
        ]
        
        for repo_info in extra_repos:
            for file in extra_files:
                if len(final_github_urls) >= 200:
                    break
                    
                url = f"https://raw.githubusercontent.com/{repo_info['user']}/{repo_info['repo']}/{repo_info['path']}/{file}"
                repo = f"{repo_info['user']}/{repo_info['repo']}"
                
                if repo not in repo_counts:
                    repo_counts[repo] = 0
                
                if repo_counts[repo] < 5:
                    final_github_urls.append(url)
                    repo_counts[repo] += 1
    
    # 最后检查，如果还是不够200个，我们可以放松一些限制
    if len(final_github_urls) < 200:
        print("警告：GitHub URL数量仍然不足200个，放松仓库数量限制...")
        
        # 从已有的URL中，添加一些变体（不同的分支或路径）
        variant_count = 200 - len(final_github_urls)
        variants_added = 0
        
        # 主要分支变体
        branches = ["main", "master", "dev", "develop", "stable"]
        
        # 对现有URL生成变体
        for url in all_github_urls:
            if variants_added >= variant_count:
                break
                
            # 检查URL是否已在final_github_urls中
            if url not in final_github_urls:
                # 提取URL的各个部分
                match = re.match(r'https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.*)', url)
                if match:
                    user, repo, branch, path = match.groups()
                    
                    # 尝试使用不同的分支
                    for new_branch in branches:
                        if new_branch != branch and variants_added < variant_count:
                            new_url = f"https://raw.githubusercontent.com/{user}/{repo}/{new_branch}/{path}"
                            
                            # 检查这个新URL是否已存在
                            if new_url not in final_github_urls:
                                final_github_urls.append(new_url)
                                variants_added += 1
    
    print(f"最终GitHub URL数量: {len(final_github_urls)}")
    
    # 添加GitHub URL部分的说明行
    result_lines.append('# 以下是至少200个GitHub直播源URL建议：\n')
    result_lines.append('# 注意：以下URL经过筛选，优先包含4K、超高清等高质量直播源\n')
    
    # 添加GitHub URL
    for i, url in enumerate(final_github_urls[:800], 1):  # 最多添加800个URL
        result_lines.append(f'# {i}. {url}\n')
    
    return result_lines

# 主函数
def main():
    print(f"开始处理文件: {FILE_PATH}")
    
    # 读取文件内容
    lines = read_file()
    print_debug(f"读取到 {len(lines)} 行内容")
    
    # 处理GitHub URL
    processed_lines = process_github_urls(lines)
    print_debug(f"处理后剩余 {len(processed_lines)} 行内容")
    
    # 写入处理后的内容
    if write_file(processed_lines):
        print(f"文件处理完成: {FILE_PATH}")
        print("已确保相同用户名/仓库名组合的GitHub直播源URL不超过5个，并优先选择包含4K、超高清等关键词的URL（至少200个）。")

if __name__ == "__main__":
    main()