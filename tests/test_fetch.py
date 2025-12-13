import requests
import time

url = "http://tv.html-5.me/i/9390107.txt"
print(f"开始获取: {url}")

try:
    start_time = time.time()
    response = requests.get(url, timeout=30)
    elapsed_time = time.time() - start_time
    print(f"请求耗时: {elapsed_time:.2f}秒")
    
    if response.status_code == 200:
        print(f"成功获取，内容长度: {len(response.text)}字符")
        print("前100字符:", response.text[:100])
    else:
        print(f"请求失败，状态码: {response.status_code}")
except Exception as e:
    print(f"请求异常: {e}")
