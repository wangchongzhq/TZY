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
        logging.FileHandler('diagnose_update.log', encoding='utf-8')
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
    logger.info("开始诊断update_iptv_sources函数...")
    
    # 加载IP-TV模块
    try:
        ip_tv_module = load_module("C:\\Users\\Administrator\\Documents\\GitHub\\TZY\\IP-TV.py")
        logger.info("成功加载IP-TV模块")
    except Exception as e:
        logger.error(f"加载IP-TV模块失败: {e}")
        sys.exit(1)
    
    # 模拟update_iptv_sources函数的部分逻辑
    try:
        # 获取频道分类配置
        logger.info("\n获取频道分类配置...")
        categories = ip_tv_module.CHANNEL_CATEGORIES
        logger.info(f"频道分类: {categories}")
        logger.info(f"分类数量: {len(categories)}")
        
        # 获取配置
        output_config = ip_tv_module.get_config('output', {})
        logger.info(f"输出配置: {output_config}")
        
        # 创建一些测试频道数据（模拟从merge_sources返回的数据）
        logger.info("\n创建测试频道数据...")
        test_channels = {
            "4K频道": [
                ("湖南卫视4K", "http://example.com/hunan4k.m3u8"),
                ("中央电视台4K", "http://example.com/cctv4k.m3u8")
            ],
            "央视频道": [
                ("CCTV1", "http://example.com/cctv1.m3u8"),
                ("CCTV2", "http://example.com/cctv2.m3u8")
            ],
            "卫视频道": [
                ("湖南卫视", "http://example.com/hunan.m3u8"),
                ("浙江卫视", "http://example.com/zhejiang.m3u8")
            ]
        }
        
        logger.info(f"测试频道数据: {test_channels}")
        logger.info(f"频道分类数量: {len(test_channels)}")
        
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
            
        except Exception as e:
            logger.error(f"频道过滤失败: {e}", exc_info=True)
            filtered_channels = test_channels  # 使用原始数据继续测试
        
        # 测试文件生成
        logger.info("\n测试文件生成...")
        
        # 获取输出文件名
        output_file_m3u_all = output_config.get('m3u_file', output_config.get('m3u_filename', "jieguo.m3u"))
        output_file_txt_all = output_config.get('txt_file', output_config.get('txt_filename', "jieguo.txt"))
        
        logger.info(f"M3U输出路径: {output_file_m3u_all}")
        logger.info(f"TXT输出路径: {output_file_txt_all}")
        
        # 测试generate_m3u_file
        logger.info("测试generate_m3u_file...")
        try:
            m3u_result = ip_tv_module.generate_m3u_file(filtered_channels, "test_m3u_output.m3u")
            logger.info(f"generate_m3u_file返回值: {m3u_result}")
            if os.path.exists("test_m3u_output.m3u"):
                logger.info(f"M3U文件生成成功，大小: {os.path.getsize('test_m3u_output.m3u')} 字节")
            else:
                logger.error("M3U文件生成失败")
        except Exception as e:
            logger.error(f"generate_m3u_file失败: {e}", exc_info=True)
        
        # 测试generate_txt_file
        logger.info("测试generate_txt_file...")
        try:
            txt_result = ip_tv_module.generate_txt_file(filtered_channels, "test_txt_output.txt")
            logger.info(f"generate_txt_file返回值: {txt_result}")
            if os.path.exists("test_txt_output.txt"):
                logger.info(f"TXT文件生成成功，大小: {os.path.getsize('test_txt_output.txt')} 字节")
            else:
                logger.error("TXT文件生成失败")
        except Exception as e:
            logger.error(f"generate_txt_file失败: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"诊断过程中发生错误: {e}", exc_info=True)
        
    logger.info("诊断结束")