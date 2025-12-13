import re
import logging
from core.logging_config import setup_logging
import os

# 设置日志
setup_logging()
logger = logging.getLogger("check_cctv4k_fix")

# 检查output/iptv.txt文件中是否有正确的CCTV4K/CCTV8K频道
def check_cctv4k_channels():
    try:
        # 首先检查output目录是否存在
        if not os.path.exists('output'):
            logger.error("output目录不存在，请先运行IPTV.py --update")
            return False
        
        # 检查iptv.txt文件是否存在
        if not os.path.exists('output/iptv.txt'):
            logger.error("output/iptv.txt文件不存在，请先运行IPTV.py --update")
            return False
        
        with open('output/iptv.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 搜索CCTV4K和CCTV8K频道
        cctv4k_pattern = re.compile(r'CCTV4K', re.IGNORECASE)
        cctv8k_pattern = re.compile(r'CCTV8K', re.IGNORECASE)
        
        # 搜索包含cctv4k或cctv8k但频道名称不正确的条目
        wrong_pattern = re.compile(r'(CCTV\d+),.*(cctv4k|cctv8k).*', re.IGNORECASE)
        
        cctv4k_matches = cctv4k_pattern.findall(content)
        cctv8k_matches = cctv8k_pattern.findall(content)
        wrong_matches = wrong_pattern.findall(content)
        
        logger.info(f"\n=== CCTV4K/CCTV8K频道检查结果 ===")
        logger.info(f"找到 {len(cctv4k_matches)} 个正确命名的CCTV4K频道")
        logger.info(f"找到 {len(cctv8k_matches)} 个正确命名的CCTV8K频道")
        logger.info(f"找到 {len(wrong_matches)} 个URL包含cctv4k/cctv8k但频道名称不正确的条目")
        
        if wrong_matches:
            logger.info("\n错误的频道条目示例：")
            for match in wrong_matches[:10]:  # 只显示前10个
                logger.info(f"频道名: {match[0]}, URL包含: {match[1]}")
        
        # 显示所有包含cctv4k或cctv8k的行
        logger.info("\n所有包含cctv4k或cctv8k的行：")
        all_cctv4k8k_lines = [line for line in content.split('\n') if re.search(r'cctv4k|cctv8k', line.lower())]
        for line in all_cctv4k8k_lines[:20]:  # 只显示前20个
            logger.info(line.strip())
        
        logger.info("\n检查完成！")
        
        # 如果没有正确的CCTV4K/CCTV8K频道，返回False
        if not cctv4k_matches and not cctv8k_matches:
            return False
        
        return True
        
except Exception as e:
        logger.error(f"检查CCTV4K/CCTV8K频道时出错: {e}")
        return False

if __name__ == "__main__":
    success = check_cctv4k_channels()
    exit(0 if success else 1)
