# 直播源自动生成工具

## 📋 项目介绍

 **直播源自动生成工具**：核心脚本为 `IPTV.py`，能够自动生成高质量的 M3U 播放列表和 TXT 格式直播源文件，支持质量筛选、智能分类和定时更新。


## ✨ 功能特性

### 直播源自动生成工具（IPTV.py）
- **多格式支持**：生成 M3U 播放列表和 TXT 格式直播源
- **智能分类**：自动将频道分类为央视频道、卫视频道、4K 频道等
- **质量控制**：支持筛选高清（HD）和 4K 直播源
- **并发处理**：使用线程池实现高效的网络请求处理
- **本地文件支持**：支持 `file://` 协议读取本地直播源文件
- **重试机制**：网络请求失败时自动重试，提高可靠性
- **定时更新**：通过 GitHub Actions 实现每日自动更新

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
    # 添加本地文件直播源（示例）
    "file:///path/to/your/local/live.txt",
    # 添加更多直播源...
]
```

## 📄 免责声明

本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除。

本工具仅用于技术研究和学习目的，请勿用于商业用途。使用本工具获取的播放源时，请确保您已获得合法授权。使用者应对使用内容的合法性负责，作者不对任何法律责任负责。

## 📧 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**更新时间**: 2025-12-24

