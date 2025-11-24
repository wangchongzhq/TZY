# 生成符合要求格式的电视直播文件

OUTPUT_FILE = 'tzydauto.txt'

# 示例频道数据
CHANNEL_DATA = [
    {
        "category": "4K央视频道",
        "channels": [
            {"name": "北京卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.51:5140"},
            {"name": "湖南卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.63:5140"},
            {"name": "浙江卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.65:5140"},
            {"name": "江苏卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.64:5140"},
            {"name": "东方卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.67:5140"},
            {"name": "广东卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.103:5140"},
            {"name": "深圳卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.104:5140"},
            {"name": "四川卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.62:5140"},
            {"name": "山东卫视4K", "url": "http://ddns.xryo.cn:8888/udp/239.111.205.66:5140"},
            {"name": "华数爱上4K", "url": "http://ddns.xryo.cn:8888/udp/239.112.205.186:5140"}
        ]
    },
    {
        "category": "央视频道",
        "channels": [
            {"name": "CCTV1", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226346/1.m3u8?"},
            {"name": "CCTV1", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226895/1.m3u8?"},
            {"name": "CCTV1", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226431/1.m3u8?"},
            {"name": "CCTV2", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226230/1.m3u8?"},
            {"name": "CCTV2", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226950/1.m3u8?"},
            {"name": "CCTV2", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226990/1.m3u8?"},
            {"name": "CCTV2", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226371/1.m3u8?"},
            {"name": "CCTV3", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226471/1.m3u8?"},
            {"name": "CCTV4", "url": "http://[2409:8087:8:21::0b]:6610/otttv.bj.chinamobile.com/PLTV/88888888/224/3221226335/1.m3u8?"}
        ]
    },
    {
        "category": "卫视频道",
        "channels": [
            {"name": "湖南卫视", "url": "http://example.com/hunan"},
            {"name": "浙江卫视", "url": "http://example.com/zhejiang"},
            {"name": "江苏卫视", "url": "http://example.com/jiangsu"}
        ]
    }
]

def main():
    """生成电视直播文件"""
    try:
        output_lines = []
        channel_count = 0
        
        # 生成文件内容
        for category_data in CHANNEL_DATA:
            # 添加类别标记
            output_lines.append(f"{category_data['category']},#genre#")
            
            # 添加频道
            for channel in category_data['channels']:
                output_lines.append(f"{channel['name']},{channel['url']}")
                channel_count += 1
            
            # 类别之间添加空行
            output_lines.append("")
        
        # 写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        print(f"成功生成 {OUTPUT_FILE}，共包含 {channel_count} 个频道")
    except Exception as e:
        print(f"生成文件失败: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
