#!/usr/bin/env python3
"""
增强版直播源测速工具
功能：
1. 支持从M3U或TXT文件读取频道
2. 异步批量测速，带并发控制
3. 支持重试机制和超时处理
4. 按延迟排序测速结果
5. 生成详细测速报告
6. 生成排序后的M3U或TXT文件
"""

import asyncio
import aiohttp
import time
import logging
import os
import datetime
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

# 配置类
class Config:
    CONCURRENT_LIMIT = 20  # 并发限制
    TIMEOUT = 10  # 超时时间（秒）
    RETRY_TIMES = 3  # 重试次数
    OUTPUT_DIR = "output"  # 输出目录
    LOG_FILE = "speed_test.log"  # 日志文件

config = Config()

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据类
@dataclass
class SpeedTestResult:
    url: str
    latency: Optional[float] = None  # 延迟（毫秒）
    resolution: Optional[str] = None  # 分辨率
    bitrate: Optional[int] = None  # 码率（Kbps）
    content_type: Optional[str] = None  # 内容类型
    success: bool = False  # 是否成功
    error: Optional[str] = None  # 错误信息
    test_time: float = 0  # 测试时间戳

# 速度测试工具类
class SpeedTester:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.TIMEOUT))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def extract_resolution_from_m3u8(self, url: str) -> Optional[str]:
        """从m3u8文件中提取分辨率信息"""
        try:
            async with self.session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status == 200:
                    content = await response.text()
                    # 查找EXT-X-STREAM-INF标签，通常包含分辨率信息
                    stream_inf_pattern = r"#EXT-X-STREAM-INF:.*?RESOLUTION=(\d+x\d+).*?(\S+)"
                    matches = re.findall(stream_inf_pattern, content, re.MULTILINE | re.DOTALL)
                    if matches:
                        # 返回第一个流的分辨率
                        return matches[0][0]
            return None
        except Exception as e:
            logger.warning(f"解析m3u8分辨率失败: {e}")
            return None
    
    async def measure_latency(self, url: str, retry_times: int = 3) -> SpeedTestResult:
        """测量单个URL的延迟、分辨率、码率等指标"""
        result = SpeedTestResult(url=url, test_time=time.time())
        
        for attempt in range(retry_times):
            try:
                start_time = time.time()
                async with self.session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=config.TIMEOUT)) as response:
                    if response.status == 200:
                        # 测量响应时间作为延迟
                        latency = (time.time() - start_time) * 1000  # 转换为毫秒
                        
                        # 提取内容类型
                        content_type = response.headers.get("Content-Type", "")
                        
                        # 提取分辨率
                        resolution = None
                        if "application/vnd.apple.mpegurl" in content_type or url.endswith(".m3u8"):
                            # 对于m3u8文件，解析获取分辨率
                            resolution = await self.extract_resolution_from_m3u8(url)
                        elif "video" in content_type:
                            # 尝试从响应头获取内容长度
                            content_length = response.headers.get("Content-Length")
                            if content_length:
                                # 视频流可能没有分辨率信息，标记为流
                                resolution = "stream"
                        
                        # 提取码率信息（如果可用）
                        bitrate = None
                        if "video" in content_type:
                            # 尝试从响应头获取码率（有些服务器会提供）
                            bitrate_header = response.headers.get("X-Content-Bitrate")
                            if bitrate_header:
                                bitrate = int(bitrate_header) // 1000  # 转换为Kbps
                        
                        result.latency = latency
                        result.resolution = resolution
                        result.bitrate = bitrate
                        result.content_type = content_type
                        result.success = True
                        logger.info(f"URL: {url} 测试成功，延迟: {latency:.2f}ms, 分辨率: {resolution or 'unknown'}")
                        break
                    else:
                        result.error = f"HTTP状态码: {response.status}"
            except Exception as e:
                result.error = str(e)
                logger.warning(f"URL: {url} 尝试 {attempt+1}/{retry_times} 失败: {e}")
                await asyncio.sleep(1)  # 重试前等待1秒
        
        return result
    
    async def batch_speed_test(self, urls: List[str], show_progress: bool = False) -> List[SpeedTestResult]:
        """批量测速（带并发控制和进度显示）"""
        results = []
        semaphore = asyncio.Semaphore(config.CONCURRENT_LIMIT)

        async def worker(url):
            async with semaphore:
                result = await self.measure_latency(url, config.RETRY_TIMES)
                results.append(result)

        tasks = [worker(url) for url in urls]
        
        # 执行任务，根据参数决定是否显示进度
        if show_progress:
            try:
                from tqdm.asyncio import tqdm_asyncio
                await tqdm_asyncio.gather(*tasks, total=len(urls), desc="测速中", unit="url")
            except ImportError:
                await asyncio.gather(*tasks)
        else:
            await asyncio.gather(*tasks)
        
        # 按延迟排序结果（升序）
        return sorted(results, key=lambda x: x.latency if x.latency is not None else float('inf'))

# 文件处理类
class FileProcessor:
    @staticmethod
    def parse_file(file_path: str) -> List[Tuple[str, str]]:
        """解析M3U或TXT文件，返回[(名称, URL), ...]"""
        try:
            # 根据文件扩展名决定解析方式
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.m3u':
                return FileProcessor.parse_m3u(file_path)
            elif ext in ('.txt', '.list'):
                return FileProcessor.parse_txt(file_path)
            else:
                logger.error(f"不支持的文件格式: {ext}")
                return []
        except Exception as e:
            logger.error(f"解析文件失败: {e}")
            return []
    
    @staticmethod
    def parse_m3u(file_path: str) -> List[Tuple[str, str]]:
        """解析M3U文件，返回[(名称, URL), ...]"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            live_sources = []
            current_name = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    # 提取名称
                    name_start = line.find(',') + 1
                    current_name = line[name_start:] if name_start > 0 else "未知频道"
                elif line.startswith('http') and current_name:
                    # 添加到源列表
                    live_sources.append((current_name, line))
                    current_name = None
            
            return live_sources
        except Exception as e:
            logger.error(f"解析M3U文件失败: {e}")
            return []
    
    @staticmethod
    def parse_txt(file_path: str) -> List[Tuple[str, str]]:
        """解析TXT文件，返回[(名称, URL), ...]"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            live_sources = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 尝试解析不同格式的行
                # 格式1: 频道名称,http://url
                if ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2 and parts[1].startswith('http'):
                        live_sources.append((parts[0].strip(), parts[1].strip()))
                # 格式2: http://url (没有名称)
                elif line.startswith('http'):
                    # 从URL中提取简单名称
                    name = os.path.splitext(os.path.basename(line.split('?')[0]))[0]
                    live_sources.append((name, line))
            
            return live_sources
        except Exception as e:
            logger.error(f"解析TXT文件失败: {e}")
            return []
    
    @staticmethod
    def generate_file(live_sources: List[Tuple[str, str]], output_path: str) -> None:
        """生成M3U或TXT文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            ext = os.path.splitext(output_path)[1].lower()
            
            if ext == '.m3u':
                FileProcessor.generate_m3u(live_sources, output_path)
            elif ext in ('.txt', '.list'):
                FileProcessor.generate_txt(live_sources, output_path)
            else:
                logger.error(f"不支持的输出格式: {ext}")
        except Exception as e:
            logger.error(f"生成文件失败: {e}")
    
    @staticmethod
    def generate_m3u(live_sources: List[Tuple[str, str]], output_path: str) -> None:
        """生成M3U文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for name, url in live_sources:
                    f.write(f'#EXTINF:-1,{name}\n')
                    f.write(f'{url}\n')
            
            logger.info(f"已生成M3U文件: {output_path}")
        except Exception as e:
            logger.error(f"生成M3U文件失败: {e}")
    
    @staticmethod
    def generate_txt(live_sources: List[Tuple[str, str]], output_path: str) -> None:
        """生成TXT文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('# 直播源列表 (名称,URL)\n')
                f.write(f'# 生成时间: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'# 共 {len(live_sources)} 个直播源\n')
                f.write('\n')
                for name, url in live_sources:
                    f.write(f'{name},{url}\n')
            
            logger.info(f"已生成TXT文件: {output_path}")
        except Exception as e:
            logger.error(f"生成TXT文件失败: {e}")

# 报告生成类
class ReportGenerator:
    @staticmethod
    def generate_report(results: List[SpeedTestResult], live_sources: List[Tuple[str, str]], output_path: str) -> None:
        """生成详细的测速报告"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 创建URL到名称的映射
            url_to_name = {url: name for name, url in live_sources}
            
            # 统计信息
            total = len(results)
            success = sum(1 for r in results if r.success)
            failed = total - success
            avg_latency = sum(r.latency for r in results if r.success) / success if success > 0 else 0
            
            # 按延迟排序结果
            sorted_results = sorted(results, key=lambda x: x.latency if x.latency is not None else float('inf'))
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== IPTV直播源测速报告 ===\n")
                f.write(f"测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"测试直播源总数: {total}\n")
                f.write(f"成功测试数: {success}\n")
                f.write(f"失败测试数: {failed}\n")
                f.write(f"成功率: {success/total*100:.2f}%\n")
                f.write(f"平均延迟: {avg_latency:.2f}ms\n")
                f.write("\n")
                f.write("=== 测试结果详情（按延迟升序排列） ===\n")
                f.write("\n")
                
                for i, result in enumerate(sorted_results):
                    name = url_to_name.get(result.url, "未知频道")
                    status = "成功" if result.success else "失败"
                    latency_str = f"{result.latency:.2f}ms" if result.success else "-"
                    resolution_str = result.resolution if result.resolution else "-"
                    bitrate_str = f"{result.bitrate}Kbps" if result.bitrate else "-"
                    content_type_str = result.content_type.split('/')[-1] if result.content_type else "-"
                    error_str = f"错误: {result.error}" if not result.success else ""
                    
                    f.write(f"{i+1}. {name}\n")
                    f.write(f"   URL: {result.url}\n")
                    f.write(f"   状态: {status}\n")
                    f.write(f"   延迟: {latency_str}\n")
                    f.write(f"   分辨率: {resolution_str}\n")
                    f.write(f"   码率: {bitrate_str}\n")
                    f.write(f"   类型: {content_type_str}\n")
                    if error_str:
                        f.write(f"   {error_str}\n")
                    f.write("\n")
            
            logger.info(f"已生成测速报告: {output_path}")
        except Exception as e:
            logger.error(f"生成测速报告失败: {e}")

# 主程序
async def main():
    """主程序入口"""
    import sys
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='增强版IPTV直播源测速工具')
    parser.add_argument('input_file', help='输入的M3U或TXT文件路径')
    parser.add_argument('output_dir', nargs='?', default=config.OUTPUT_DIR, help='输出目录（默认: output）')
    parser.add_argument('--concurrent', type=int, default=config.CONCURRENT_LIMIT, help='并发数（默认: 20）')
    parser.add_argument('--timeout', type=int, default=config.TIMEOUT, help='超时时间（秒，默认: 10）')
    parser.add_argument('--retry', type=int, default=config.RETRY_TIMES, help='重试次数（默认: 3）')
    parser.add_argument('--no-progress', action='store_true', help='不显示进度条')
    
    args = parser.parse_args()
    
    # 更新配置
    config.CONCURRENT_LIMIT = args.concurrent
    config.TIMEOUT = args.timeout
    config.RETRY_TIMES = args.retry
    show_progress = not args.no_progress
    
    # 获取输入输出参数
    input_file = args.input_file
    output_dir = args.output_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 解析输入文件
    logger.info(f"开始解析文件: {input_file}")
    live_sources = FileProcessor.parse_file(input_file)
    
    if not live_sources:
        logger.error("未找到有效的直播源")
        return
    
    logger.info(f"找到 {len(live_sources)} 个直播源")
    
    # 执行速度测试
    logger.info("开始速度测试...")
    start_time = time.time()
    
    async with SpeedTester() as tester:
        urls = [source[1] for source in live_sources]
        results = await tester.batch_speed_test(urls, show_progress=show_progress)
    
    elapsed_time = time.time() - start_time
    logger.info(f"测速完成，耗时: {elapsed_time:.2f}秒")
    
    # 统计结果
    success_count = sum(1 for r in results if r.success)
    total_count = len(results)
    
    logger.info(f"速度测试结果: 成功 {success_count}/{total_count} ({success_count/total_count*100:.2f}%)")
    
    # 创建URL到结果的映射
    url_to_result = {result.url: result for result in results}
    
    # 根据测试结果排序直播源
    sorted_live_sources = sorted(
        live_sources,
        key=lambda x: url_to_result[x[1]].latency if url_to_result[x[1]].latency is not None else float('inf')
    )
    
    # 显示前5个最快的直播源
    logger.info("\n前5个最快的直播源:")
    for i, (name, url) in enumerate(sorted_live_sources[:5], 1):
        result = url_to_result[url]
        if result.success:
            logger.info(f"{i}. {name} - 延迟: {result.latency:.2f}ms, 分辨率: {result.resolution or 'unknown'}")
    
    # 生成排序后的输出文件
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    ext = os.path.splitext(input_file)[1]
    output_file = os.path.join(output_dir, f"{base_name}_sorted{ext}")
    FileProcessor.generate_file(sorted_live_sources, output_file)
    
    # 生成速度测试报告
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"speed_test_report_{timestamp}.txt")
    ReportGenerator.generate_report(results, live_sources, report_file)
    
    logger.info("\n所有操作已完成！")

if __name__ == "__main__":
    asyncio.run(main())