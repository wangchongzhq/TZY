# 直播源有效性验证工具

这是一个用于验证直播源有效性的工具，支持M3U和TXT格式文件，可以检测视频分辨率并生成带有分辨率信息的有效直播源文件。

## 功能特性

- ✅ 支持M3U和TXT格式直播源文件的解析
- ✅ 并发验证直播源URL的有效性
- ✅ 使用ffprobe检测视频分辨率
- ✅ 在频道名称后添加分辨率信息（如"CCTV5[3840*2160]"）
- ✅ 保留原始频道分类和排序顺序
- ✅ 生成符合要求的输出文件
- ✅ 支持多线程并发处理，提高验证效率
- ✅ 支持自定义超时时间

## 安装依赖

1. 确保已安装Python 3.7或更高版本
2. 安装所需的Python库：
   ```bash
   pip install -r ../requirements.txt
   ```
3. 安装FFmpeg（用于视频分辨率检测）：
   - Windows：从[Gyan.dev](https://www.gyan.dev/ffmpeg/builds/)下载并添加到系统PATH
   - Linux：`sudo apt-get install ffmpeg`
   - macOS：`brew install ffmpeg`

## 使用方法

### 命令行使用

#### 验证单个M3U文件
```bash
python iptv_validator.py -i ../jieguo.m3u -w 50 -t 5
```

#### 验证单个TXT文件
```bash
python iptv_validator.py -i ../jieguo.txt -w 50 -t 5
```

#### 批量验证当前目录下所有支持的文件
```bash
python iptv_validator.py -a -w 50 -t 5
```

#### 参数说明
- `-i, --input`: 输入文件路径（必填）
- `-o, --output`: 输出文件路径（可选，默认生成`原文件名_valid.扩展名`）
- `-w, --workers`: 并发工作线程数（默认：10）
- `-t, --timeout`: 超时时间（秒，默认：10）
- `-a, --all`: 批量验证当前目录下所有支持的文件

### 示例输出

```
开始验证文件: ../jieguo.m3u
文件类型: m3u
共解析到 100 个频道，10 个分类
验证完成，耗时 25.32 秒
有效频道数: 78
有效率: 78.00%
输出文件已生成: ../jieguo_valid.m3u
```

## 输出文件格式

### M3U格式
```
#EXTM3U
#EXTINF:-1 group-title="央视",CCTV1[1920*1080]
https://example.com/cctv1.m3u8
#EXTINF:-1 group-title="央视",CCTV5[3840*2160]
https://example.com/cctv5.m3u8
#EXTINF:-1 group-title="体育",NBA直播[1280*720]
https://example.com/nba.m3u8
```

### TXT格式
```
#央视#,genre#
CCTV1[1920*1080],https://example.com/cctv1.m3u8
CCTV5[3840*2160],https://example.com/cctv5.m3u8
#体育#,genre#
NBA直播[1280*720],https://example.com/nba.m3u8
```

## 在Python代码中使用

```python
from validator.iptv_validator import IPTVValidator

# 创建验证器实例
validator = IPTVValidator('input.m3u', 'output_valid.m3u', max_workers=20, timeout=5)

# 运行验证并生成输出文件
output_file = validator.run()
print(f"输出文件已生成: {output_file}")
```

## 扩展建议

### 本地Web界面

为了更方便地在本地使用，可以添加一个Web界面：

1. **安装Web框架**：
   ```bash
   pip install flask
   ```

2. **创建Web应用**：
   - 支持文件上传
   - 支持手动输入直播源URL
   - 显示验证进度和结果
   - 提供生成的有效直播源文件下载

### GitHub部署方案

为了在GitHub上使用这些功能，可以考虑以下方案：

1. **GitHub Actions自动化**：
   - 使用GitHub Actions定期验证直播源
   - 将生成的有效直播源文件上传到GitHub Releases
   - 提供下载链接

2. **Web应用部署**：
   - 使用Flask或Streamlit创建Web应用
   - 部署到Vercel、Heroku或GitHub Pages
   - 支持用户上传文件和输入URL

3. **API服务**：
   - 创建RESTful API接口
   - 支持远程验证直播源
   - 提供JSON格式的验证结果

## 注意事项

1. 验证速度取决于网络质量和直播源服务器响应速度
2. 分辨率检测需要安装FFmpeg
3. 某些直播源可能需要特殊的验证方法（如需要认证的流）
4. 建议根据实际情况调整工作线程数和超时时间

## 许可证

MIT License
