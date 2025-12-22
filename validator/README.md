# IPTV直播源验证工具

一个功能强大的IPTV直播源验证工具，支持多协议（HTTP/HTTPS/RTSP/RTMP/MMS/UDP/RTP）验证，提供命令行和Web界面两种使用方式。

## 功能特性

- **多协议支持**：验证HTTP/HTTPS、RTSP、RTMP、MMS、UDP、RTP协议的直播源
- **批量验证**：支持M3U/M3U8/TXT格式文件的批量验证
- **互联网直播源支持**：直接从HTTP/HTTPS URL下载并验证直播源文件
- **并发处理**：使用多线程加速验证过程
- **智能验证**：
  - HTTP/HTTPS协议：先尝试HEAD请求，失败自动回退到GET请求
  - 支持所有2xx（成功）和3xx（重定向）状态码
  - 其他协议：通过socket连接检查
- **调试模式**：详细的调试输出，便于排查问题
- **Web界面**：用户友好的Web界面，支持文件上传和手动URL验证
- **分辨率检测**：自动检测视频流分辨率（需要FFmpeg）

## 安装依赖

```bash
pip install requests flask
```

**可选依赖**：
- FFmpeg：用于视频分辨率检测

## 使用方法

### 命令行界面（CLI）

```bash
python iptv_validator.py -i <输入文件> [选项]
```

#### 参数说明

| 参数 | 描述 | 默认值 |
|------|------|--------|
| -i, --input | 输入文件路径（M3U/M3U8/TXT格式）或互联网直播源文件URL（HTTP/HTTPS协议） | 必填 |
| -o, --output | 输出文件路径 | output/[输入文件名]_valid.m3u |
| -w, --workers | 线程数量 | 5 |
| -t, --timeout | 超时时间（秒） | 5 |
| -d, --debug | 启用调试模式 | False |
| -a, --all | 验证所有URL，包括非标准协议 | False |

#### 示例

```bash
# 基本用法
python iptv_validator.py -i channels.m3u

# 启用调试模式，增加超时时间
python iptv_validator.py -i channels.m3u -t 10 -d

# 自定义输出文件和线程数
python iptv_validator.py -i channels.m3u -o valid_channels.m3u -w 10
```

### Web界面

```bash
python web_app.py
```

然后在浏览器中访问：`http://localhost:5000`

#### Web界面功能

- **文件上传**：支持M3U/M3U8/TXT格式文件上传
- **手动URL输入**：支持单个URL输入并配置分类
- **互联网直播源文件**：支持直接输入M3U/M3U8/TXT格式的互联网直播源文件URL
- **参数配置**：可设置线程数和超时时间
- **结果展示**：显示有效频道数和详细信息
- **文件下载**：可下载验证后的有效直播源文件

## 文件格式支持

### M3U/M3U8格式

```
#EXTM3U
#EXTINF:-1 group-title="新闻",CCTV-13新闻
https://example.com/cctv13.m3u8
#EXTINF:-1 group-title="综艺",湖南卫视
http://example.com/hunan.m3u8
```

### TXT格式

```
#新闻#,genre#
CCTV-13新闻,https://example.com/cctv13.m3u8

#综艺#,genre#
湖南卫视,http://example.com/hunan.m3u8
```

## 故障排除

### 常见问题

1. **没有找到有效的直播源**
   - 检查网络连接是否正常
   - 尝试增加超时时间：`-t 10`
   - 启用调试模式查看详细错误信息：`-d`
   - 验证URL是否可以在浏览器或播放器中正常访问
   - **内部网络限制**：如果直播源是内部IP地址（如10.0.0.0/8、192.168.0.0/16），确保验证工具与直播源在同一网络段

2. **连接被拒绝**
   - 确保防火墙没有阻止程序访问网络
   - 检查代理设置
   - 对于RTSP/RTMP协议，确保目标服务器端口（默认554/1935）未被防火墙阻止

3. **DNS解析失败**
   - 检查网络连接
   - 尝试使用IP地址代替域名

4. **RTSP/RTMP流验证失败**
   - 检查网络是否允许TCP连接到目标端口
   - 确认服务器是否正常运行
   - 内部网络的RTSP流需要在同一网络环境下验证

### 调试模式输出说明

调试模式下，程序会输出详细的验证过程：

```
[调试] 正在检查URL: http://example.com/stream.m3u8
[调试] URL http://example.com/stream.m3u8 HEAD请求状态码: 200
[调试] URL http://example.com/stream.m3u8 连接成功
```

## 开发说明

### 核心功能

- **URL验证**：`check_url_validity`方法负责验证URL有效性
- **文件解析**：支持M3U/M3U8/TXT格式文件解析
- **并发处理**：使用`concurrent.futures.ThreadPoolExecutor`实现多线程验证
- **Web应用**：基于Flask的Web界面，支持文件上传和手动验证

### 项目结构

```
validator/
├── iptv_validator.py    # 核心验证逻辑
├── web_app.py           # Web界面
├── README.md            # 文档
└── output/              # 输出文件目录
```

## 更新日志

### v1.1
- 增加调试模式
- 支持所有2xx和3xx状态码
- 改进错误处理
- 更新Web界面

### v1.0
- 初始版本
- 支持多协议验证
- 命令行和Web界面
- 批量验证功能

## 注意事项

1. 某些直播源可能需要特定的User-Agent或Referer才能访问
2. 频繁验证可能会导致IP被封禁，建议合理设置验证频率
3. 分辨率检测需要安装FFmpeg
4. 非HTTP/HTTPS协议的验证仅检查连接是否成功，不验证流的有效性

## 许可证

MIT License