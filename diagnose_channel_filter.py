import os
import sys
import logging
import importlib.util
from datetime import datetime

# 设置日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('diagnose_filter.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def load_module(file_path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location("IP-TV", file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["IP-TV"] = module
    spec.loader.exec_module(module)
    return module

if __name__ == "__main__":
    logger.info("开始诊断频道过滤问题...")
    
    # 加载IP-TV模块
    try:
        ip_tv_module = load_module("C:\\Users\\Administrator\\Documents\\GitHub\\TZY\\IP-TV.py")
        logger.info("成功加载IP-TV模块")
    except Exception as e:
        logger.error(f"加载IP-TV模块失败: {e}")
        sys.exit(1)
    
    # 测试should_exclude_url函数
    logger.info("\n测试should_exclude_url函数...")
    
    test_urls = [
        "http://example.com/cctv1.m3u8",
        "http://tv.example.com/cctv2.m3u8",
        "http://streaming.tv/cctv3.m3u8",
        "http://cdn.live.com/channel1.m3u8",
        "http://demo.live.com/test.m3u8",
        "http://live.com/sample.m3u8"
    ]
    
    for url in test_urls:
        result = ip_tv_module.should_exclude_url(url, "测试频道")
        logger.info(f"URL '{url}' -> 是否排除: {result}")
    
    # 测试should_exclude_channel函数
    logger.info("\n测试should_exclude_channel函数...")
    
    test_channels = [
        "湖南卫视",
        "东方购物",
        "CCTV1",
        "好享购",
        "浙江卫视",
        "电视购物频道"
    ]
    
    for channel_name in test_channels:
        result = ip_tv_module.should_exclude_channel(channel_name)
        logger.info(f"频道 '{channel_name}' -> 是否排除: {result}")
    
    # 创建不会被过滤的测试频道数据
    logger.info("\n创建不会被过滤的测试频道数据...")
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
    
    # 测试频道过滤
    logger.info("\n测试频道过滤...")
    try:
        filtered_channels = ip_tv_module.filter_channels(test_channels)
        logger.info(f"过滤后频道分类数量: {len(filtered_channels)}")
        
        # 统计每个分类的频道数量
        total_channels = 0
        for category, channels in filtered_channels.items():
            channel_count = len(channels)
            total_channels += channel_count
            logger.info(f"  {category}: {channel_count}个频道")
        logger.info(f"  总频道数: {total_channels}")
        
        # 如果过滤成功，测试文件生成
        if filtered_channels:
            logger.info("\n测试文件生成...")
            
            # 测试generate_txt_file
            logger.info("测试generate_txt_file...")
            try:
                txt_result = ip_tv_module.generate_txt_file(filtered_channels, "test_txt_final.txt")
                logger.info(f"generate_txt_file返回值: {txt_result}")
                if os.path.exists("test_txt_final.txt"):
                    logger.info(f"TXT文件生成成功，大小: {os.path.getsize('test_txt_final.txt')} 字节")
                    # 查看文件内容
                    with open("test_txt_final.txt", "r", encoding="utf-8") as f:
                        content = f.read()
                        logger.info(f"文件内容: {content[:200]}...")  # 只显示前200个字符
                else:
                    logger.error("TXT文件生成失败")
            except Exception as e:
                logger.error(f"generate_txt_file失败: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"频道过滤失败: {e}", exc_info=True)
        
    logger.info("诊断结束")