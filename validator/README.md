# 直播源有效性验证工具ZHQ

一个功能强大的IPTV直播源验证工具，支持多协议（HTTP/HTTPS/RTSP/RTMP/MMS/UDP/RTP）验证，提供命令行和Web界面两种使用方式。

## 功能特性

- **多协议支持**：验证HTTP/HTTPS、RTSP、RTMP、MMS、UDP、RTP协议的直播源
- **批量验证**：支持M3U/M3U8/TXT格式文件的批量验证
- **互联网直播源支持**：直接从HTTP/HTTPS URL下载并验证直播源文件
- **频道比较功能**：对比原始频道列表和验证后的有效频道列表，找出无效频道并进行分析
- **智能并发处理**：
  - 动态线程池：根据CPU核心数自动调整线程数（默认：CPU核心数×4，最大20）
  - 批处理：每100个频道为一批进行验证，避免资源过载
  - HTTP连接池：重用连接，减少连接建立开销（50个连接）
  - ffprobe进程池：重用ffprobe进程，提高分辨率检测效率
- **智能验证**：
  - HTTP/HTTPS协议：先尝试HEAD请求，失败自动回退到GET请求
  - 支持所有2xx（成功）和3xx（重定向）状态码
  - 其他协议：通过socket连接检查
  - 增强URL验证：支持包含动态参数（如{PSID}或%7BPSID%7D）的URL
  - 特殊字符处理：自动处理URL中的$符号和后续内容
  - IPv6支持：支持IPv6地址（带或不带方括号）
  - 宽松验证逻辑：URL格式有效（包含scheme和netloc）即标记为有效（用户确认的电视可播放链接）
- **BlackBird-Player风格试播验证**：
  - IPv6 URL试播：通过FFprobe探测，检查是否能在IPv6环境下正常连接并获取真实分辨率
  - UDP/RTSP/RTMP/RTP协议：使用FFmpeg尝试解码一小段数据，确认流可播放并获取真实分辨率
  - 真实分辨率检测：通过实际播放测试获取流的真实分辨率，而非从URL模式推断
  - 编码信息获取：成功播放后获取视频编码、音频编码等详细信息
- **调试模式**：详细的调试输出，便于排查问题
- **Web界面**：用户友好的Web界面，支持文件上传和手动URL验证
- **增强的结果展示**：Web界面以表格形式展示验证结果，包括频道名称、播放地址、线程号、有效性和视频分辨率
- **分辨率检测**：自动检测视频流分辨率（需要FFmpeg，支持MediaInfo作为备选方案）
- **音频参数检测**：自动检测音频流参数（编码格式、采样率、声道数、比特率）
- **失效源过滤**：可自动过滤不含音频或视频流的失效源
- **增强分辨率检测**：支持ffprobe和MediaInfo双重检测，提高分辨率识别成功率
- **自动目录管理**：验证完成后自动创建output目录（若不存在），确保输出文件能正常生成

## 安装依赖

```bash
pip install requests flask
```

**可选依赖**：
- FFmpeg：用于视频分辨率检测（必需）
- MediaInfo：用于增强分辨率检测，作为ffprobe的备选方案

### MediaInfo 安装

**Windows**（使用 winget）：
```powershell
winget install MediaArea.MediaInfo -e
```

**Windows**（使用 Chocolatey）：
```powershell
choco install mediainfo
```

**macOS**（使用 Homebrew）：
```bash
brew install mediainfo
```

**Linux**（Ubuntu/Debian）：
```bash
sudo apt install mediainfo
```

**Linux**（Fedora）：
```bash
sudo dnf install mediainfo
```

安装后需要重启终端或刷新环境变量使PATH生效。

## 使用方法

### 命令行界面（CLI）

#### 1. 直播源验证工具

```bash
python iptv_validator.py -i <输入文件> [选项]
```

#### 参数说明

| 参数 | 描述 | 默认值 |
|------|------|--------|
| -i, --input | 输入文件路径（M3U/M3U8/TXT格式）或互联网直播源文件URL（HTTP/HTTPS协议） | 必填（与-a互斥） |
| -o, --output | 输出文件路径 | output/[输入文件名]_valid.m3u |
| -w, --workers | 线程数量 | CPU核心数×4（最大20） |
| -t, --timeout | 超时时间（秒） | 5 |
| -d, --debug | 启用调试模式 | False |
| -a, --all | 验证当前目录下所有支持的文件 | False（与-i互斥） |
| --no-audio-filter | 过滤不含音频流的频道 | False |
| --skip-resolution | 跳过分辨率检测 | False |
| --use-mediainfo-only | 仅使用MediaInfo进行分辨率检测 | False |

#### 示例

```bash
# 基本用法
python iptv_validator.py -i channels.m3u

# 启用调试模式，增加超时时间
python iptv_validator.py -i channels.m3u -t 10 -d

# 自定义输出文件和线程数
python iptv_validator.py -i channels.m3u -o valid_channels.m3u -w 10

# 过滤不含音频流的频道
python iptv_validator.py -i channels.m3u --no-audio-filter

# 跳过分辨率检测（快速模式）
python iptv_validator.py -i channels.m3u --skip-resolution

# 仅使用MediaInfo进行分辨率检测
python iptv_validator.py -i channels.m3u --use-mediainfo-only

# 验证当前目录下所有支持的文件
python iptv_validator.py -a

# 验证当前目录下所有支持的文件并启用调试模式
python iptv_validator.py -a -d -w 5
```

#### 2. 频道比较工具

用于对比原始频道列表和验证后的有效频道列表，找出无效频道并进行分析。

```bash
python compare_channels.py <原始文件> <有效文件>
```

#### 示例

```bash
# 比较原始文件和有效文件，找出无效频道
python compare_channels.py original_channels.txt valid_channels.m3u
```

输出示例：
```
原始频道数: 100
有效频道数: 85
无效频道数: 15

无效频道列表:
CCTV-1,http://example.com/cctv1.m3u8
  格式检查: scheme=http, netloc=example.com
湖南卫视频道,http://example.com/hunan.m3u8
  格式检查: scheme=http, netloc=example.com
```

### Web界面

```bash
python web_app.py
```

然后在浏览器中访问：`http://localhost:5001`

#### Web界面功能

- **文件上传**：支持M3U/M3U8/TXT格式文件上传
- **手动URLweb输入**：支持单个URL输入并配置分类
- **互联网直播源文件**：支持直接输入M3U/M3U8/TXT格式的互联网直播源文件URL
- **参数配置**：可设置线程数和超时时间
- **增强的结果展示**：以表格形式展示验证结果，包含以下信息：
  - 频道名称：直播频道的名称
  - 播放地址：直播流的URL
  - 线程号：处理该频道的线程ID
  - 有效性：频道是否有效（绿色表示有效，红色表示无效）
  - 分辨率：视频流的宽度和高度（如1920x1080）
  - 音频参数：音频编码、采样率、声道数（如AAC/48000/6）
- **过滤选项**：可选择过滤不含音频流的失效源
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
#新闻#,#genre#
CCTV-13新闻,https://example.com/cctv13.m3u8

#综艺#,#genre#
湖南卫视,http://example.com/hunan.m3u8
```

**注意**：TXT格式支持两种分类行格式：
- 标准格式：`#分类名#,#genre#`
- 兼容格式：`#分类名#,genre#`（自动转换为标准格式）

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
├── iptv_validator.py            # 核心验证逻辑
├── web_app.py                   # Web界面
├── compare_channels.py          # 频道比较工具
├── README.md                    # 文档
├── OPTIMIZATION_SUGGESTIONS.md  # 性能优化建议
├── USAGE_GUIDE.md               # 使用指南
├── __init__.py                  # 包初始化文件
├── test_resolution_detection.py # 分辨率检测测试
├── test_url_validity.py         # URL有效性测试
├── test_validation_flow.py      # 验证流程测试
├── test_validity.py             # 有效性测试
├── test_web_app.py              # Web应用测试
└── output/                      # 输出文件目录
```

## 更新日志

### v1.7
- **修复频道分类问题**：解决TXT格式文件验证后所有频道显示为"未分类"的问题
- **增强分类行处理**：支持两种分类行格式（`#分类#,#genre#` 和 `#分类#,genre#`），自动兼容错误格式
- **修复M3U解析逻辑**：重写M3U解析逻辑，确保分类行正确识别和分组
- **修复TXT输出分辨率显示**：解决TXT输出中"(None, None)"分辨率显示问题
- **保持向后兼容性**：确保新版本与旧格式的兼容性，同时标准化输出格式
- **完善验证测试**：添加全面的分类处理测试，确保修复的稳定性

### v1.6
- 新增BlackBird-Player风格试播验证功能
- IPv6 URL试播：通过FFprobe探测，检查是否能在IPv6环境下正常连接并获取真实分辨率
- UDP/RTSP/RTMP/RTP协议：使用FFmpeg尝试解码一小段数据，确认流可播放并获取真实分辨率
- 真实分辨率检测：通过实际播放测试获取流的真实分辨率，而非从URL模式推断
- 编码信息获取：成功播放后获取视频编码、音频编码等详细信息
- Web界面更名为"直播源有效性验证工具ZHQ"
- 优化Web界面布局，减少行间距，提升用户体验
- 修复输出目录问题：验证完成后自动创建output目录（若不存在），解决删除output目录后无法生成输出文件的问题
- 新增文件编码智能检测：支持UTF-8、GBK、GB2312等中文编码自动识别，解决大文件乱码问题
- 增强WebSocket传输：增大缓冲区至100MB，支持大文件实时通信
- 优化验证结果滚动：实现双模式滚动逻辑，自动定位最新验证结果
- 新增快速停止机制：点击停止后0.5秒内立即响应，解决大型文件停止延迟问题
- 改进外部URL处理：添加实时进度反馈，消除用户等待焦虑

### v1.4
- 改进参数解析：将-i/--input和-a/--all选项设置为互斥，解决--all选项使用问题
- 优化验证流程：每次验证开始时清除已处理的外部URL缓存，确保验证结果准确
- 增强WebSocket事件处理：使用validation_id隔离验证会话，解决UI状态保留问题
- 修复GitHub Actions工作流：移除对已删除文件的引用
- 修正客户端统计逻辑：确保无效频道计数准确

### v1.3
- 增强的验证结果信息：验证结果包含频道名称、播放地址、线程号、有效性和视频分辨率
- 优化的Web界面显示：以表格形式展示验证结果，支持直观查看每个频道的详细信息
- 有效性状态可视化：绿色表示有效频道，红色表示无效频道
- 分辨率展示：显示视频流的宽度和高度信息

### v1.2
- 新增频道比较工具（compare_channels.py）：对比原始频道列表和验证后的有效频道列表
- 增强URL解析逻辑：支持包含动态参数（如{PSID}或%7BPSID%7D）的URL
- 改进特殊字符处理：自动处理URL中的$符号和后续内容
- 实现动态线程池：根据CPU核心数自动调整线程数（默认：CPU核心数×4，最大20）
- 优化HTTP连接池：配置50个连接的连接池，减少连接开销
- 新增批处理机制：每100个频道为一批进行验证，避免资源过载
- 实现ffprobe进程池：重用ffprobe进程，提高分辨率检测效率
- 改进宽松验证逻辑：URL格式有效（包含scheme和netloc）即标记为有效

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