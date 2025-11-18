import requests
import re
from datetime import datetime
import time

SOURCES = [
{"name": "fanmingming", "url": "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u"},
{"name": "free-iptv", "url": "https://raw.githubusercontent.com/Free-IPTV/Countries/master/China.m3u"},
]

def download_m3u(url):
    try:
        response = requests.get(url, timeout=10)
        return response.text
    except:
        return None

def main():
    print("Starting IPZY collection...")
    for source in SOURCES:
        print(f"Processing: {source['name']}")
        content = download_m3u(source["url"])
        if content:
            print(f"Got data from {source['name']}")
        else:
            print(f"Failed to get data from {source['name']}")
    print("Done!")

if __name__ == "__main__":
    main()
