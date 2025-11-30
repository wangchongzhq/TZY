# 4K超高清直播源合并转换工具

## 📋 项目介绍

这是一套用于自动和手动处理4K超高清直播源的解决方案，能够从`4K_uhd_channels.txt`文件中提取以`.m3u`结尾的直播源URL，合并并转换为`4K_uhd_hb.txt`格式，同时保留频道名称与URL的对应关系，并自动去除重复的直播线路。

## ✨ 功能特点

### 核心功能
- 🎯 **智能提取**：自动从`4K_uhd_channels.txt`提取所有`.m3u`直播源URL
- 🔄 **合并转换**：将多个M3U直播源合并并转换为统一的TXT格式
- 📝 **保留信息**：确保每个URL都对应正确的频道名称（如CCTV1、湖南卫视等）
- 🧹 **自动去重**：去除相同的直播线路，避免重复内容
- 🌐 **多源支持**：支持多种M3U格式（标准格式、简化格式、极简格式）
- 🔍 **编码自动检测**：自动识别和处理不同编码的M3U文件
- ⚡ **并行处理**：使用多线程技术，提高处理效率

### 部署功能
- 🤖 **自动运行**：每天自动定时更新直播源
- 🖱️ **手动触发**：支持手动运行工作流进行更新
- 📊 **详细日志**：完整记录处理过程和结果统计
- 📁 **版本控制**：自动提交更新到GitHub，支持查看历史版本

## 📁 文件结构

```
📦 TZY/
├── 📄 4K_uhd_merger.py       # 主程序脚本
├── 📄 4K_uhd_channels.txt    # 直播源URL列表（输入文件）
├── 📄 4K_uhd_hb.txt          # 合并转换结果（输出文件）
├── 📄 README.md              # 项目说明文档
└── 📁 .github/
    └── 📁 workflows/
        └── 📄 4k_uhd_merger.yml  # GitHub Actions工作流配置
```

## 🚀 快速开始

### 环境要求
- Python 3.6 或更高版本
- Git 版本控制工具
- GitHub账号（用于自动部署）

### 安装步骤

#### 1. 克隆代码库
```bash
git clone https://github.com/your-username/TZY.git
cd TZY
```

#### 2. 安装依赖
```bash
# Windows
pip install requests

# Linux/Mac
pip3 install requests
```

#### 3. 准备输入文件
确保`4K_uhd_channels.txt`文件包含有效的`.m3u`直播源URL，格式如下：
```
# 示例内容
https://example.com/4K.m3u
https://ghfast.top/https://raw.githubusercontent.com/user/repo/master/m3u/4K.m3u
```

## 💻 使用方法

### 手动运行

#### 方式1：直接运行Python脚本
```bash
# Windows
python 4K_uhd_merger.py

# Linux/Mac
python3 4K_uhd_merger.py
```

#### 方式2：通过PowerShell运行
```powershell
cd "C:\Users\Administrator\Documents\GitHub\TZY"
python 4K_uhd_merger.py
```

### 自动运行

项目配置了GitHub Actions工作流，每天会自动运行：
- ⏰ **运行时间**：每天凌晨2点（北京时间）
- 📊 **运行结果**：自动更新`4K_uhd_hb.txt`文件
- 📝 **版本记录**：自动提交更改到GitHub

#### 手动触发工作流
1. 访问项目的GitHub页面
2. 点击"Actions"选项卡
3. 选择"4K超高清直播源自动合并转换"工作流
4. 点击"Run workflow"按钮
5. 选择分支并点击"Run workflow"

## 📄 文件格式说明

### 输入文件格式 (4K_uhd_channels.txt)

```
# 4K超高清直播源列表
# 更新时间: 2025-11-29
# 共包含多个4K超高清频道

# GitHub直播源URL示例
https://ghfast.top/https://raw.githubusercontent.com/user/repo/master/m3u/4K.m3u
https://example.com/another_4K.m3u
```

### 输出文件格式 (4K_uhd_hb.txt)

```
# 4K超高清直播源合并结果
# 更新时间: 2025-11-30 15:30:45
# 总频道数: 1256
# 来源: 4K_uhd_channels.txt

CCTV1,http://example.com/cctv1/4k.m3u8
CCTV2,http://example.com/cctv2/4k.m3u8
CCTV4K,http://example.com/cctv4k/4k.m3u8
湖南卫视,http://example.com/hunan/4k.m3u8
北京卫视,http://example.com/beijing/4k.m3u8
```

## 🔧 工作原理

### 处理流程
1. **提取URL**：从`4K_uhd_channels.txt`提取所有以`.m3u`结尾的URL
2. **下载内容**：并行下载每个M3U文件的内容
3. **解析频道**：从M3U内容中提取频道名称和对应的直播URL
4. **合并数据**：将所有频道信息合并到一个列表中
5. **去重处理**：去除相同的直播线路
6. **排序保存**：按频道名排序并保存到`4K_uhd_hb.txt`

### 技术实现
- **多线程下载**：使用ThreadPoolExecutor实现并行下载
- **正则表达式**：支持多种M3U格式的解析
- **编码处理**：自动检测和处理不同编码的文本
- **错误处理**：完善的异常捕获和重试机制
- **日志记录**：详细记录处理过程和结果

## 🛠️ 配置选项

### 主脚本配置 (4K_uhd_merger.py)

在脚本中可以修改以下配置：

```python
# 输入输出文件配置
self.input_file = "4K_uhd_channels.txt"    # 输入文件
self.output_file = "4K_uhd_hb.txt"        # 输出文件

# 下载配置
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
})  # 用户代理

# 线程配置
max_workers = min(8, len(m3u_urls))  # 最大线程数
```

### 工作流配置 (.github/workflows/4k_uhd_merger.yml)

```yaml
# 定时运行配置
on:
  schedule:
    - cron: '0 18 * * *'  # UTC时间，对应北京时间凌晨2点
```

## 📊 使用示例

### 示例1：基本使用

```bash
# 运行主脚本
python 4K_uhd_merger.py

# 输出示例
🎬 4K超高清直播源合并转换工具启动
============================================================
🔍 正在从4K_uhd_channels.txt提取.m3u直播源URL...
✅ 成功提取到 15 个.m3u直播源URL
   1. https://ghfast.top/https://raw.githubusercontent.com/user/repo/master/m3u/4K.m3u
   ...
📥 正在下载: https://ghfast.top/https://raw.githubusercontent.com/user/repo/master/m3u/4K.m3u
📝 下载成功，编码: utf-8, 大小: 128KB
📊 从...解析到 256 个频道
    📡 频道: CCTV1 -> URL: http://example.com/cctv1/4k.m3u8
    📡 频道: CCTV2 -> URL: http://example.com/cctv2/4k.m3u8
    ...
💾 正在保存到 4K_uhd_hb.txt...
✅ 保存成功!
📁 文件名: 4K_uhd_hb.txt
📊 频道数: 1256
📏 文件大小: 352.45 KB
============================================================
🏆 操作完成!
⏱️ 总耗时: 45.23 秒
```

### 示例2：查看转换结果

```bash
# 查看生成的文件
Get-Content 4K_uhd_hb.txt -TotalCount 10

# 输出示例
# 4K超高清直播源合并结果
# 更新时间: 2025-11-30 15:30:45
# 总频道数: 1256
# 来源: 4K_uhd_channels.txt

CCTV1,http://example.com/cctv1/4k.m3u8
CCTV2,http://example.com/cctv2/4k.m3u8
CCTV3,http://example.com/cctv3/4k.m3u8
CCTV4K,http://example.com/cctv4k/4k.m3u8
```

## ⚠️ 注意事项

### 使用须知
1. **网络连接**：运行时需要稳定的网络连接以下载M3U文件
2. **文件格式**：确保`4K_uhd_channels.txt`中的URL格式正确且可访问
3. **存储空间**：处理大量直播源时可能需要足够的临时存储空间
4. **权限设置**：GitHub Actions需要正确的权限设置才能提交更改

### 常见问题

#### Q: 为什么某些直播源下载失败？
A: 可能的原因包括：网络连接问题、URL不存在或已失效、服务器限制访问。程序会自动重试3次。

#### Q: 为什么频道名称显示乱码？
A: 程序支持自动检测和处理不同编码，但某些特殊编码可能仍有问题。建议使用UTF-8编码保存文件。

#### Q: 如何添加新的直播源？
A: 只需在`4K_uhd_channels.txt`文件中添加新的`.m3u`直播源URL，程序会自动处理。

#### Q: 工作流为什么没有自动运行？
A: 请检查：
- GitHub Actions是否已启用
- 定时任务配置是否正确
- 仓库权限设置是否合适

## 🔄 更新日志

### v1.0.0 (2025-11-30)
- ✅ 初始版本发布
- ✅ 实现核心合并转换功能
- ✅ 支持多格式M3U解析
- ✅ 添加自动去重功能
- ✅ 配置GitHub Actions自动工作流
- ✅ 完善错误处理和日志记录

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进这个项目！

### 贡献步骤
1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📞 联系信息

如有问题或建议，请通过以下方式联系：

- 创建Issue：在GitHub仓库创建新的Issue
- 发送邮件：[your-email@example.com]()

---

**享受4K超高清直播体验！** 🎉

=== 测试标记 (请勿删除) ===
此文件已通过脚本自动更新
测试版本: 2.0
测试日期: 2025-11-30
测试ID: test_push_verification_20251130

