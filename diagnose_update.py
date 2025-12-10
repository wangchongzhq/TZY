import sys
import os
import importlib.util
import logging
from collections import defaultdict

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', encoding='utf-8')
logger = logging.getLogger(__name__)

# 加载IP-TV.py模块
spec = importlib.util.spec_from_file_location("IPTV", "IP-TV.py")
IPTV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(IPTV)

# 运行update_iptv_sources函数的关键部分进行诊断
def diagnose_update():
    logger.info("开始诊断update_iptv_sources函数...")
    
    # 合并所有直播源
    all_sources = IPTV.default_sources + IPTV.user_sources
    default_local_sources = IPTV.default_local_sources
    
    logger.info(f"直播源数量: {len(all_sources)}个远程源, {len(default_local_sources)}个本地源")
    
    # 获取所有远程源内容
    logger.info("正在获取远程直播源...")
    results = IPTV.fetch_multiple(all_sources, timeout=30, verify=False)
    
    # 统计成功获取的远程源
    success_count = sum(1 for content in results.values() if content)
    logger.info(f"成功获取 {success_count}/{len(all_sources)} 个远程源")
    
    # 合并所有频道
    logger.info("正在合并直播源...")
    channels_data = IPTV.merge_sources(all_sources, default_local_sources)
    
    # 统计合并后的频道数量
    all_channels_count = sum(len(chans) for group, chans in channels_data['all'].items())
    ipv4_count = sum(len(chans) for group, chans in channels_data['ipv4'].items())
    ipv6_count = sum(len(chans) for group, chans in channels_data['ipv6'].items())
    
    logger.info(f"合并后频道数量: 全部={all_channels_count}, IPv4={ipv4_count}, IPv6={ipv6_count}")
    
    if all_channels_count == 0:
        logger.error("合并后没有频道数据，这可能是问题所在！")
        return False
    
    # 过滤频道
    logger.info("正在过滤频道...")
    filtered_channels_all = IPTV.filter_channels(channels_data['all'])
    filtered_channels_ipv4 = IPTV.filter_channels(channels_data['ipv4'])
    filtered_channels_ipv6 = IPTV.filter_channels(channels_data['ipv6'])
    
    # 统计过滤后的频道数量
    filtered_all_count = sum(len(chans) for group, chans in filtered_channels_all.items())
    filtered_ipv4_count = sum(len(chans) for group, chans in filtered_channels_ipv4.items())
    filtered_ipv6_count = sum(len(chans) for group, chans in filtered_channels_ipv6.items())
    
    logger.info(f"过滤后频道数量: 全部={filtered_all_count}, IPv4={filtered_ipv4_count}, IPv6={filtered_ipv6_count}")
    
    if filtered_all_count == 0:
        logger.error("过滤后没有频道数据，这可能是问题所在！")
        return False
    
    # 尝试生成文件
    logger.info("正在尝试生成TXT文件...")
    output_config = IPTV.get_config('output', {})
    output_file_txt_all = output_config.get('txt_filename', "jieguo.txt")
    
    if IPTV.generate_txt_file(filtered_channels_all, output_file_txt_all):
        logger.info(f"✅ 成功生成TXT文件: {output_file_txt_all}")
    else:
        logger.error(f"❌ 生成TXT文件失败: {output_file_txt_all}")
        return False
    
    return True

if __name__ == "__main__":
    diagnose_update()
