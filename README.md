# IPTV 直播源处理工具集

## 📋 项目介绍

本项目包含两个核心工具：

1. **直播源自动生成工具**：核心脚本为 `IPTV.py`，能够自动生成高质量的 M3U 播放列表和 TXT 格式直播源文件，支持质量筛选、智能分类和定时更新。

2. **直播源验证工具**：位于 `validator/` 目录，支持多协议（HTTP/HTTPS/RTSP/RTMP/MMS/UDP/RTP）验证，提供命令行和 Web 界面两种使用方式，能够批量验证直播源有效性并生成仅包含有效频道的输出文件。

## ✨ 功能特性

### 直播源自动生成工具（IPTV.py）
- **多格式支持**：生成 M3U 播放列表和 TXT 格式直播源
- **智能分类**：自动将频道分类为央视频道、卫视频道、4K 频道等
- **质量控制**：支持筛选高清（HD）和 4K 直播源
- **并发处理**：使用线程池实现高效的网络请求处理
- **本地文件支持**：支持 `file://` 协议读取本地直播源文件
- **重试机制**：网络请求失败时自动重试，提高可靠性
- **定时更新**：通过 GitHub Actions 实现每日自动更新

### 直播源验证工具（validator/）
- **多协议支持**：验证 HTTP/HTTPS、RTSP、RTMP、MMS、UDP、RTP 协议的直播源
- **批量验证**：支持 M3U/M3U8/TXT 格式文件的批量验证
- **并发处理**：使用多线程加速验证过程
- **智能验证**：
  - HTTP/HTTPS 协议：先尝试 HEAD 请求，失败自动回退到 GET 请求
  - 支持所有 2xx（成功）和 3xx（重定向）状态码
  - 其他协议：通过 socket 连接检查
- **调试模式**：详细的调试输出，便于排查问题
- **Web 界面**：用户友好的 Web 界面，支持文件上传和手动 URL 验证
- **智能过滤**：自动去除无效直播源，仅保留可播放的频道 URL
- **分辨率检测**：自动检测视频流分辨率（需要 FFmpeg）

## 📋 环境要求

- Python 3.6 或更高版本
- Git 版本控制工具
- GitHub 账号（用于自动化工作流）

### 依赖安装

```bash
pip install -r requirements.txt
```

**可选依赖**：
- FFmpeg：用于视频分辨率检测

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/TZY.git
cd TZY
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

## 📁 项目结构

```
├── .github/workflows/           # GitHub Actions 工作流配置
├── IPTV.py                      # 核心直播源生成工具（全功能）
├── unified_sources.py           # 统一直播源配置
├── update_sources.py            # 直播源更新脚本
├── convert_m3u_to_txt.py        # M3U 转 TXT 工具
├── check_files.py               # 文件状态检查工具
├── check_all_syntax.py          # 语法检查工具
├── validate_workflows.py        # GitHub Actions 工作流验证工具
├── validator/                   # 直播源验证工具目录
│   ├── iptv_validator.py        # 验证工具核心脚本
│   ├── web_app.py               # Web 界面应用
│   ├── README.md                # 验证工具详细文档
│   └── output/                  # 验证工具输出目录
├── requirements.txt             # 依赖包列表
├── README.md                    # 项目说明文档
├── REPOSITORY_OPTIMIZATION_REPORT.md  # 仓库优化报告
└── 项目文件关联关系.md          # 项目文件依赖关系文档
```

## 🎯 使用指南

### 直播源自动生成工具（IPTV.py）

#### 运行核心脚本

```bash
python IPTV.py --update
```

#### 检查输出文件状态

```bash
python check_files.py
```

#### 自定义直播源

您可以直接在 `unified_sources.py` 中添加自定义直播源：

```python
UNIFIED_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    # 添加本地文件直播源
    "file:///path/to/your/local/live.txt",
    # 或直接添加单个直播源URL
    "http://example.com/custom-channel",
]
```

#### 验证生成结果

运行脚本后，检查输出文件是否成功生成：

```bash
# 查看输出文件状态
python check_files.py

# 检查特定频道是否存在（以CCTV1为例）
# 例如: grep -n "CCTV1" jieguo.txt
```

#### 配置直播源

编辑 `unified_sources.py` 文件，添加或修改直播源：

```python
UNIFIED_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "file://c:/Users/Administrator/Documents/GitHub/TZY/temp_live.txt",
    # 添加更多直播源...
]
```

### 直播源验证工具（validator/）

#### 命令行界面（CLI）

```bash
python validator/iptv_validator.py -i <输入文件> [选项]
```

##### 参数说明

| 参数 | 描述 | 默认值 |
|------|------|--------|
| -i, --input | 输入文件路径（M3U/M3U8/TXT格式） | 必填 |
| -o, --output | 输出文件路径 | output/[输入文件名]_valid.m3u |
| -w, --workers | 线程数量 | 5 |
| -t, --timeout | 超时时间（秒） | 5 |
| -d, --debug | 启用调试模式 | False |
| -a, --all | 验证所有URL，包括非标准协议 | False |

##### 示例

```bash
# 基本用法
python validator/iptv_validator.py -i validator/109 live 1205 直播源.txt

# 启用调试模式，增加超时时间
python validator/iptv_validator.py -i validator/109 live 1205 直播源.txt -t 10 -d

# 自定义输出文件和线程数
python validator/iptv_validator.py -i validator/109 live 1205 直播源.txt -o valid_channels.m3u -w 10
```

#### Web界面

```bash
python validator/web_app.py
```

然后在浏览器中访问：`http://localhost:5000`

##### Web界面功能

- **文件上传**：支持M3U/M3U8/TXT格式文件上传
- **手动URL输入**：支持单个URL输入并配置分类
- **参数配置**：可设置线程数和超时时间
- **结果展示**：显示有效频道数和详细信息
- **文件下载**：可下载验证后的有效直播源文件

#### 文件格式支持

##### M3U/M3U8格式

```
#EXTM3U
#EXTINF:-1 group-title="新闻",CCTV-13新闻
https://example.com/cctv13.m3u8
#EXTINF:-1 group-title="综艺",湖南卫视
http://example.com/hunan.m3u8
```

##### TXT格式

```
#新闻#,genre#
CCTV-13新闻,https://example.com/cctv13.m3u8

#综艺#,genre#
湖南卫视,http://example.com/hunan.m3u8
```

## 🤖 自动化工作流

项目配置了多个 GitHub Actions 工作流，支持自动定时更新：

- **update_iptv.yml**: 定时更新 IPTV.py 生成的直播源
- **update_sources.yml**: 定时更新统一直播源配置

### 手动触发工作流

1. 打开 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择对应的工作流
4. 点击 "Run workflow" 按钮

## 🔧 最近修复与改进

### IPTV.py 修复
- ✅ 添加了 `file://` 协议支持，可读取本地直播源文件
- ✅ 实现了动态格式检测，根据内容自动区分 M3U 和 TXT 格式
- ✅ 优化了频道合并逻辑，提高了生成速度
- ✅ 修复了远程源请求失败导致的文件不更新问题
- ✅ 添加了详细的日志记录，便于故障排查

### 直播源验证工具（validator/）改进
- ✅ 支持多协议（HTTP/HTTPS/RTSP/RTMP/MMS/UDP/RTP）验证
- ✅ 实现智能过滤，自动去除无效直播源
- ✅ 提供命令行和Web界面两种使用方式
- ✅ 优化了TXT文件解析，支持emoji前缀分类行
- ✅ 添加了详细的调试模式，便于排查验证失败原因
- ✅ 支持文件格式自动识别（M3U/M3U8/TXT）

## ⚠️ 注意事项

1. 部分直播源可能存在版权问题，请合法使用
2. 网络不稳定可能导致部分远程直播源获取失败
3. 建议定期运行脚本更新直播源列表
4. 如遇到播放源失效问题，可使用直播源验证工具进行检测
5. 频繁验证可能会导致IP被封禁，建议合理设置验证频率
6. 分辨率检测需要安装FFmpeg
7. 某些直播源可能需要特定的User-Agent或Referer才能访问
8. 非HTTP/HTTPS协议的验证仅检查连接是否成功，不验证流的有效性

## 📝 输出文件说明

### 直播源自动生成工具（IPTV.py）输出
- **jieguo.m3u**: M3U 格式播放列表
- **jieguo.txt**: TXT 格式直播源列表

### 直播源验证工具（validator/）输出
- **[输入文件名]_valid.m3u**: 验证后的有效M3U播放列表
- **[输入文件名]_valid.txt**: 验证后的有效TXT格式直播源

## 🛠️ 故障排查

### 直播源自动生成工具故障排查

#### 检查文件是否更新
```bash
python check_files.py
```

#### 查看脚本运行情况
```bash
# 直接运行脚本查看输出
# 例如: python IPTV.py

# 或查看文件生成状态
python check_files.py
```

#### 常见问题及解决方案

##### 问题：输出文件没有更新
- **原因1**: 远程直播源请求失败（网络问题或403/404错误）
- **解决方案1**: 检查网络连接，或更换直播源
- **原因2**: 本地测试文件缺失
- **解决方案2**: 创建 `temp_live.txt` 并添加测试频道

##### 问题：测试频道未出现在输出中
- **原因**: 文件格式检测错误
- **解决方案**: 确保脚本正确区分 M3U 和 TXT 格式内容

### 直播源验证工具故障排查

#### 常见问题

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

4. **RTSP/RTMP/MMS/UDP/RTP流验证失败**
   - 检查网络是否允许TCP连接到目标端口
   - 确认服务器是否正常运行
   - 内部网络的流需要在同一网络环境下验证
   - UDP/RTP协议通常使用特定端口范围，确保防火墙未阻止

#### 调试模式输出说明

调试模式下，程序会输出详细的验证过程：

```
[调试] 正在检查URL: http://example.com/stream.m3u8
[调试] URL http://example.com/stream.m3u8 HEAD请求状态码: 200
[调试] URL http://example.com/stream.m3u8 连接成功
```

## 🔧 开发说明

### 直播源验证工具开发说明

#### 核心功能

- **URL验证**：`check_url_validity`方法负责验证URL有效性
- **文件解析**：支持M3U/M3U8/TXT格式文件解析
- **并发处理**：使用`concurrent.futures.ThreadPoolExecutor`实现多线程验证
- **Web应用**：基于Flask的Web界面，支持文件上传和手动验证

## 📄 免责声明

本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除。

本工具仅用于技术研究和学习目的，请勿用于商业用途。使用本工具获取的播放源时，请确保您已获得合法授权。使用者应对使用内容的合法性负责，作者不对任何法律责任负责。

## 📧 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**更新时间**: 2025-12-21
**版本**: 1.6.0