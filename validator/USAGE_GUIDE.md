# 直播源有效性验证工具使用指南

本文档详细介绍如何在本地和GitHub上使用直播源有效性验证工具，包括检测输入直播源网址、上传本地直播源文件，以及生成和下载有效直播源文件。

## 一、本地使用方法

### 1. 命令行方式

#### 环境准备

1. 确保已安装Python 3.7或更高版本
2. 安装依赖：
   ```bash
   pip install -r ../requirements.txt
   ```
3. 安装FFmpeg（用于视频分辨率检测）：
   - Windows：从[Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)下载并添加到系统PATH
   - Linux：`sudo apt-get install ffmpeg`
   - macOS：`brew install ffmpeg`

#### 基本使用

```bash
# 进入validator目录
cd validator

# 验证M3U文件，使用50个并发线程，5秒超时
python iptv_validator.py -i ../jieguo.m3u -w 50 -t 5

# 验证TXT文件
python iptv_validator.py -i ../jieguo.txt -w 50 -t 5

# 批量验证当前目录下所有支持的文件
python iptv_validator.py -a -w 50 -t 5
```

#### 参数说明

- `-i, --input`: 输入文件路径（必填）
- `-o, --output`: 输出文件路径（可选，默认生成`原文件名_valid.扩展名`）
- `-w, --workers`: 并发工作线程数（默认：10）
- `-t, --timeout`: 超时时间（秒，默认：10）
- `-a, --all`: 批量验证当前目录下所有支持的文件

### 2. Web界面方式

提供图形化界面，更适合本地使用。

#### 启动Web服务

```bash
# 进入validator目录
cd validator

# 启动Flask Web服务
python web_app.py
```

服务将在`http://localhost:5001`启动。

#### 使用Web界面

Web界面提供两个功能标签页：

##### 2.1 文件上传

1. 点击"文件上传"标签
2. 选择本地的M3U、M3U8或TXT格式直播源文件
3. 设置并发工作线程数和超时时间（建议使用默认值：20线程，5秒超时）
4. 点击"开始验证"
5. 验证完成后，点击"下载有效直播源文件"获取结果

##### 2.2 URL输入

1. 点击"URL输入"标签
2. 在文本框中输入直播源URL，格式为：`频道名称,http://example.com/stream.m3u8`（每行一个）
3. 设置分类名称
4. 设置并发工作线程数和超时时间
5. 点击"开始验证"
6. 验证完成后，点击"下载有效直播源文件"获取结果

## 二、GitHub使用方法

### 1. 当前GitHub Actions自动化

项目已配置GitHub Actions工作流，自动定期更新直播源：

- **触发方式**：每天北京时间4点自动运行，也支持手动触发
- **运行环境**：Ubuntu 最新版
- **主要功能**：运行IPTV.py脚本更新直播源，提交更改到仓库

### 2. 扩展GitHub使用功能

#### 2.1 添加验证步骤到GitHub Actions

可以扩展现有工作流，添加直播源验证步骤：

```yaml
# 在现有工作流中添加验证步骤

- name: 安装FFmpeg
  run: sudo apt-get update && sudo apt-get install -y ffmpeg

- name: 验证生成的直播源
  run: |
    cd validator
    python iptv_validator.py -i ../jieguo.m3u -w 50 -t 5
    python iptv_validator.py -i ../jieguo.txt -w 50 -t 5

- name: 提交验证后的有效直播源
  run: |
    git add jieguo_valid.m3u jieguo_valid.txt
    git commit -m "添加验证后的有效直播源 [$(date +'%Y-%m-%d %H:%M:%S')]"
    git push origin ${{ github.ref_name }}
```

#### 2.2 部署Web应用到云平台

将Web应用部署到云平台，让用户可以在GitHub上直接使用：

1. **部署选项**：
   - Vercel：适合部署Flask应用
   - Heroku：支持Python应用部署
   - Render：提供免费的Web服务

2. **部署步骤**（以Vercel为例）：
   - Fork项目到自己的GitHub账户
   - 登录Vercel，选择导入项目
   - 选择Fork的项目
   - 配置构建命令和输出目录
   - 部署完成后，获取访问URL

3. **使用方式**：
   - 通过Vercel提供的URL访问Web应用
   - 上传本地直播源文件或输入URL进行验证
   - 下载生成的有效直播源文件

### 3. 使用GitHub Releases发布有效直播源

可以配置工作流将验证后的有效直播源文件发布到GitHub Releases：

```yaml
# 在现有工作流中添加发布步骤

- name: 发布有效直播源到GitHub Releases
  uses: softprops/action-gh-release@v1
  if: steps.check_changes.outputs.changes == 'true'
  with:
    files: |
      jieguo_valid.m3u
      jieguo_valid.txt
    tag_name: iptv-valid-$(date +'%Y%m%d')
    name: 有效直播源 - $(date +'%Y-%m-%d')
    body: 自动生成的有效直播源文件
```

## 三、功能说明

### 1. 直播源检测

#### 1.1 URL有效性检测

- 支持的协议：HTTP、HTTPS、RTSP、RTMP、MMS、UDP、RTP
- 检测方法：
  - HTTP/HTTPS：发送HEAD请求，检查响应状态码（200、301、302）
  - 其他协议：尝试建立TCP连接

#### 1.2 视频分辨率检测

- 使用FFmpeg的ffprobe工具检测视频流信息
- 在频道名称后添加分辨率信息，如：`CCTV5[3840*2160]`

### 2. 文件格式支持

#### 2.1 M3U格式

- 解析EXTINF行提取频道名称和分类信息
- 保留原始分类和排序顺序
- 生成符合M3U标准的输出文件

#### 2.2 TXT格式

- 支持`#分类名#,genre#`格式的分类标记
- 解析`频道名称,URL`格式的频道信息
- 保留原始分类和排序顺序

### 3. 并发处理

- 使用多线程并发验证多个频道
- 可自定义并发工作线程数，提高验证效率
- 默认使用20个线程，5秒超时（Web界面）

## 四、输出结果

### 1. 命令行输出

```
开始验证文件: ../jieguo.m3u
文件类型: m3u
共解析到 100 个频道，10 个分类
验证完成，耗时 25.32 秒
有效频道数: 78
有效率: 78.00%
输出文件已生成: ../jieguo_valid.m3u
```

### 2. Web界面输出

- 显示验证结果统计信息
- 提供有效直播源文件的下载链接
- 支持多种文件格式的下载

### 3. 输出文件格式

#### M3U格式

```
#EXTM3U
#EXTINF:-1 group-title="央视",CCTV1[1920*1080]
https://example.com/cctv1.m3u8
#EXTINF:-1 group-title="央视",CCTV5[3840*2160]
https://example.com/cctv5.m3u8
#EXTINF:-1 group-title="体育",NBA直播[1280*720]
https://example.com/nba.m3u8
```

#### TXT格式

```
#央视#,genre#
CCTV1[1920*1080],https://example.com/cctv1.m3u8
CCTV5[3840*2160],https://example.com/cctv5.m3u8
#体育#,genre#
NBA直播[1280*720],https://example.com/nba.m3u8
```

## 五、常见问题

### 1. 验证速度慢

**解决方法**：
- 增加并发工作线程数（-w参数）
- 减少超时时间（-t参数）
- 示例：`python iptv_validator.py -i input.m3u -w 50 -t 5`

### 2. 分辨率检测失败

**解决方法**：
- 确保已安装FFmpeg并添加到系统PATH
- 检查网络连接是否正常
- 某些直播源可能不支持分辨率检测

### 3. Web界面无法启动

**解决方法**：
- 确保已安装Flask：`pip install flask`
- 检查端口是否被占用
- 尝试使用其他端口：`python web_app.py --port 8080`

### 4. GitHub Actions执行失败

**解决方法**：
- 检查工作流配置文件
- 查看GitHub Actions日志
- 确保FFmpeg已正确安装

## 六、扩展建议

### 1. 本地扩展

- 添加更多视频信息检测（比特率、编码格式等）
- 支持更多直播源格式
- 添加直播源质量评分功能

### 2. GitHub扩展

- 添加用户提交直播源的Issue模板
- 创建Discord或Telegram频道用于用户反馈
- 添加直播源统计分析功能

---

以上就是直播源有效性验证工具的详细使用指南，涵盖了本地和GitHub上的各种使用方式。如果有任何问题或建议，请提交Issue反馈。