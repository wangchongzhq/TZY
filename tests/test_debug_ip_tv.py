#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

# 设置日志级别为DEBUG，查看详细信息
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从IP-TV.py导入需要的函数
import importlib.util

spec = importlib.util.spec_from_file_location("IP_TV", "IP-TV.py")
IP_TV = importlib.util.module_from_spec(spec)
sys.modules["IP_TV"] = IP_TV
spec.loader.exec_module(IP_TV)

# 运行测试
def test_merge_sources():
    logger.info("=== 测试merge_sources函数 ===")
    
    # 获取默认的直播源
    default_sources = IP_TV.default_sources
    default_local_sources = IP_TV.default_local_sources
    
    logger.info(f"默认远程直播源数量: {len(default_sources)}")
    logger.info(f"默认本地直播源文件数量: {len(default_local_sources)}")
    
    # 调用merge_sources函数
    try:
        channels_data = IP_TV.merge_sources(default_sources, default_local_sources)
        
        # 检查返回的数据
        logger.info(f"merge_sources返回的数据类型: {type(channels_data)}")
        if isinstance(channels_data, dict):
            logger.info(f"merge_sources返回的键: {list(channels_data.keys())}")
            
            # 检查各个版本的频道数据
            for key, value in channels_data.items():
                if isinstance(value, dict):
                    num_groups = len(value)
                    num_channels = sum(len(chans) for group, chans in value.items())
                    logger.info(f"{key} - 频道组数: {num_groups}, 频道总数: {num_channels}")
                    
                    # 显示前几个频道组
                    if num_groups > 0:
                        logger.info(f"前几个频道组: {list(value.keys())[:5]}")
                        
                        # 显示前几个频道组的频道数量
                        for group in list(value.keys())[:3]:
                            logger.info(f"  {group}: {len(value[group])} 个频道")
                            if len(value[group]) > 0:
                                logger.info(f"    前几个频道: {[name for name, url in value[group][:3]]}")
        
        return channels_data
    except Exception as e:
        logger.error(f"调用merge_sources函数时出错: {e}", exc_info=True)
        return None

def test_filter_channels(channels_data):
    if channels_data is None:
        logger.error("没有可用的频道数据进行过滤测试")
        return None
    
    logger.info("\n=== 测试filter_channels函数 ===")
    
    try:
        # 测试过滤合并频道
        filtered_channels_all = IP_TV.filter_channels(channels_data['all'])
        
        # 检查过滤后的数据
        num_groups = len(filtered_channels_all)
        num_channels = sum(len(chans) for group, chans in filtered_channels_all.items())
        logger.info(f"过滤后 - 频道组数: {num_groups}, 频道总数: {num_channels}")
        
        # 显示前几个频道组
        if num_groups > 0:
            logger.info(f"前几个频道组: {list(filtered_channels_all.keys())[:5]}")
            
            # 显示前几个频道组的频道数量
            for group in list(filtered_channels_all.keys())[:3]:
                logger.info(f"  {group}: {len(filtered_channels_all[group])} 个频道")
                if len(filtered_channels_all[group]) > 0:
                    logger.info(f"    前几个频道: {[name for name, url in filtered_channels_all[group][:3]]}")
        
        return filtered_channels_all
    except Exception as e:
        logger.error(f"调用filter_channels函数时出错: {e}", exc_info=True)
        return None

def test_file_generation(filtered_channels_all):
    if filtered_channels_all is None:
        logger.error("没有可用的频道数据进行文件生成测试")
        return False
    
    logger.info("\n=== 测试文件生成功能 ===")
    
    try:
        # 获取输出配置
        from core.config import get_config
        output_config = get_config('output', {})
        logger.info(f"输出配置: {output_config}")
        
        # 生成测试M3U文件
        m3u_path = 'test_output.m3u'
        success = IP_TV.generate_m3u_file(filtered_channels_all, m3u_path)
        
        if success:
            logger.info(f"✅ 成功生成测试M3U文件: {m3u_path}")
            logger.info(f"   文件大小: {os.path.getsize(m3u_path)} 字节")
        else:
            logger.error(f"❌ 生成测试M3U文件失败: {m3u_path}")
        
        return success
    except Exception as e:
        logger.error(f"测试文件生成功能时出错: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("开始测试IP-TV.py程序")
    
    # 测试merge_sources函数
    channels_data = test_merge_sources()
    
    # 测试filter_channels函数
    filtered_channels_all = test_filter_channels(channels_data)
    
    # 测试文件生成功能
    test_file_generation(filtered_channels_all)
    
    logger.info("\n测试结束")