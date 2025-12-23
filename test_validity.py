import re
import sys
from urllib.parse import urlparse

# 模拟check_url_validity方法的逻辑
def mock_check_url_validity(url):
    try:
        # 处理包含特殊字符的URL，如$符号
        if '$' in url:
            url = url.split('$')[0]

        # 检测是否包含动态参数
        has_dynamic_params = re.search(r'(\{[A-Z_]+\}|%7B[A-Z_]+%7D)', url)

        parsed_url = urlparse(url)
        
        print(f"检查URL: {url}")
        print(f"解析结果 - scheme: {parsed_url.scheme}, netloc: {parsed_url.netloc}")
        
        # 检查URL是否包含常见的视频流协议
        if re.search(r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)', url):
            print(f"URL包含有效协议，视为有效: {url}")
            return True
        
        # 检查是否为IP地址+端口的格式
        if re.search(r'^\d+\.\d+\.\d+\.\d+:\d+', url):
            print(f"URL为IP+端口格式，视为有效: {url}")
            return True
        
        # 对于任何看起来像URL的字符串，都视为有效
        if parsed_url.scheme or parsed_url.netloc or '.' in url:
            print(f"URL格式合理，视为有效: {url}")
            return True
        
        # 最后的检查：如果URL不为空，就视为有效
        if url.strip():
            print(f"URL不为空，视为有效: {url}")
            return True
        
        # 只有空URL才视为无效
        print(f"URL为空，视为无效: {url}")
        return False
    except Exception as e:
        print(f"检查URL有效性时出错: {type(e).__name__}: {e}")
        # 如果发生任何异常，使用与主要逻辑一致的宽松验证策略
        try:
            parsed_url = urlparse(url)
            
            # 检查URL是否包含常见的视频流协议
            if re.search(r'(http[s]?://|rtsp://|rtmp://|mms://|udp://|rtp://)', url):
                print(f"URL包含有效协议，视为有效: {url}")
                return True
            
            # 检查是否为IP地址+端口的格式
            if re.search(r'^\d+\.\d+\.\d+\.\d+:\d+', url):
                print(f"URL为IP+端口格式，视为有效: {url}")
                return True
            
            # 对于任何看起来像URL的字符串，都视为有效
            if parsed_url.scheme or parsed_url.netloc or '.' in url:
                print(f"URL格式合理，视为有效: {url}")
                return True
            
            # 最后的检查：如果URL不为空，就视为有效
            if url.strip():
                print(f"URL不为空，视为有效: {url}")
                return True
            
            # 只有空URL才视为无效
            print(f"URL为空，视为无效: {url}")
            return False
        except Exception as e2:
            # 如果再次发生异常，只要URL不为空就视为有效
            if url.strip():
                print(f"异常处理中再次出错，但URL不为空，视为有效: {url}")
                return True
            return False

# 测试几个URL
if __name__ == "__main__":
    test_urls = [
        "http://example.com/live.m3u8",
        "rtsp://192.168.1.100:554/stream",
        "udp://@239.255.1.1:1234",
        "http://192.168.1.1:8080/live",
        "http://example.com/stream.m3u8$DVB-C",
        "http://example.com/stream?psid={PSID}",
        "",
        "invalid_url",
        "example.com/live.m3u8",
        "192.168.1.1:8080"
    ]
    
    for url in test_urls:
        print(f"\n--- 测试URL: {url} ---")
        result = mock_check_url_validity(url)
        print(f"结果: {'有效' if result else '无效'}")