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
        logging.FileHandler('diagnose_file_generation.log', encoding='utf-8')
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
    logger.info("开始诊断文件生成问题...")
    
    # 加载IP-TV模块
    try:
        ip_tv_module = load_module("C:\\Users\\Administrator\\Documents\\GitHub\\TZY\\IP-TV.py")
        logger.info("成功加载IP-TV模块")
    except Exception as e:
        logger.error(f"加载IP-TV模块失败: {e}")
        sys.exit(1)
    
    # 获取配置
    try:
        output_config = ip_tv_module.get_config('output', {})
        logger.info(f"输出配置: {output_config}")
        
        # 测试配置获取
        output_file_m3u_all = output_config.get('m3u_file', output_config.get('m3u_filename', "jieguo.m3u"))
        output_file_txt_all = output_config.get('txt_file', output_config.get('txt_filename', "jieguo.txt"))
        
        logger.info(f"M3U输出路径: {output_file_m3u_all}")
        logger.info(f"TXT输出路径: {output_file_txt_all}")
        
        # 创建测试频道数据
        test_channels = {
            "4K频道": [
                ("湖南卫视4K", "http://example.com/hunan4k.m3u8"),
                ("中央电视台4K", "http://example.com/cctv4k.m3u8")
            ],
            "央视频道": [
                ("CCTV1", "http://example.com/cctv1.m3u8"),
                ("CCTV2", "http://example.com/cctv2.m3u8")
            ]
        }
        
        # 测试generate_txt_file函数
        logger.info("\n开始测试generate_txt_file函数...")
        try:
            result = ip_tv_module.generate_txt_file(test_channels, "test_diagnose.txt")
            logger.info(f"generate_txt_file返回值: {result}")
            
            if os.path.exists("test_diagnose.txt"):
                logger.info(f"测试文件创建成功，大小: {os.path.getsize('test_diagnose.txt')} 字节")
                with open("test_diagnose.txt", "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.info(f"测试文件内容: {content[:200]}...")
            else:
                logger.error("测试文件创建失败")
        except Exception as e:
            logger.error(f"调用generate_txt_file失败: {e}", exc_info=True)
            
        # 测试generate_files函数
        logger.info("\n开始测试generate_files函数...")
        try:
            # 先获取generate_files函数
            generate_files_func = ip_tv_module.generate_files
            result = generate_files_func(test_channels, "test_m3u.m3u", "test_txt.txt", "测试版")
            logger.info(f"generate_files返回值: {result}")
            
            if os.path.exists("test_m3u.m3u"):
                logger.info(f"测试M3U文件创建成功，大小: {os.path.getsize('test_m3u.m3u')} 字节")
            else:
                logger.error("测试M3U文件创建失败")
                
            if os.path.exists("test_txt.txt"):
                logger.info(f"测试TXT文件创建成功，大小: {os.path.getsize('test_txt.txt')} 字节")
            else:
                logger.error("测试TXT文件创建失败")
        except Exception as e:
            logger.error(f"调用generate_files失败: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"诊断过程中发生错误: {e}", exc_info=True)
        
    logger.info("诊断结束")