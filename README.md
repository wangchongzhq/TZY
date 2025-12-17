# IPTV 直播源自动生成工具

## 📋 项目介绍

一个功能强大的 IPTV 直播源自动化处理工具集，支持多格式输出、质量筛选、智能分类和定时更新。主要包含 `IPTV.py` 和 `tvzy.py` 两个核心脚本，用于满足不同场景的直播源处理需求。

## ✨ 功能特性

### 核心功能
- **多格式支持**：生成 M3U 播放列表和 TXT 格式直播源
- **智能分类**：自动将频道分类为央视频道、卫视频道、4K 频道等
- **质量控制**：支持筛选高清（HD）和 4K 直播源
- **并发处理**：使用线程池实现高效的网络请求处理
- **本地文件支持**：支持 `file://` 协议读取本地直播源文件
- **重试机制**：网络请求失败时自动重试，提高可靠性
- **定时更新**：通过 GitHub Actions 实现每日自动更新

### 两个核心脚本的区别

| 特性 | IPTV.py | tvzy.py |
|------|---------|---------|
| **主要用途** | 全功能直播源生成工具 | 专注于高质量（HD/4K）直播源 |
| **输出格式** | M3U + TXT | TXT 格式 |
| **频道范围** | 所有可用频道 | 仅高质量（HD/4K）频道 |
| **分类方式** | 基于频道名称 | 基于频道名称 |
| **文件名称** | `jieguo.m3u` 和 `jieguo.txt` | `tzydauto.txt` |
| **质量过滤** | 无特定过滤 | 通过正则表达式过滤 HD/4K 流 |
| **分组功能** | 基础分类 | 无 |

## 📋 环境要求

- Python 3.6 或更高版本
- Git 版本控制工具
- GitHub 账号（用于自动化工作流）

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

### 3. 运行核心脚本

#### 运行 tvzy.py（仅生成高质量频道）
```bash
python tvzy.py
```

#### 运行 IPTV.py（全功能直播源生成工具）
```bash
python IPTV.py --update
```

## 📁 项目结构

```
├── .github/workflows/           # GitHub Actions 工作流配置
├── IPTV.py                      # 核心直播源生成工具（全功能）
├── tvzy.py                      # 高质量直播源生成工具（HD/4K）
├── unified_sources.py           # 统一直播源配置
├── update_sources.py            # 直播源更新脚本
├── convert_m3u_to_txt.py        # M3U 转 TXT 工具
├── check_files.py               # 文件状态检查工具
├── check_all_syntax.py          # 语法检查工具
├── validate_workflows.py        # GitHub Actions 工作流验证工具
├── requirements.txt             # 依赖包列表
├── tzydauto.txt                 # tvzy.py 输出的高质量频道列表
├── README.md                    # 项目说明文档
├── REPOSITORY_OPTIMIZATION_REPORT.md  # 仓库优化报告
└── 项目文件关联关系.md          # 项目文件依赖关系文档
```

## 🎯 使用指南

### 1. 检查输出文件状态

```bash
python check_files.py
```

### 2. 自定义直播源

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

### 3. 验证生成结果

运行脚本后，检查输出文件是否成功生成：

```bash
# 查看输出文件状态
python check_files.py

# 检查特定频道是否存在（以CCTV1为例）
# 例如: grep -n "CCTV1" tzydauto.txt 或 grep -n "CCTV1" jieguo.txt
```

### 4. 配置直播源

编辑 `unified_sources.py` 文件，添加或修改直播源：

```python
UNIFIED_SOURCES = [
    "https://iptv-org.github.io/iptv/countries/cn.m3u",
    "file://c:/Users/Administrator/Documents/GitHub/TZY/temp_live.txt",
    # 添加更多直播源...
]
```

## 🤖 自动化工作流

项目配置了多个 GitHub Actions 工作流，支持自动定时更新：

- **update_iptv.yml**: 定时更新 IPTV.py 生成的直播源
- **tvzy_update.yml**: 定时更新 tvzy.py 生成的高质量直播源
- **update_sources.yml**: 定时更新统一直播源配置

### 手动触发工作流

1. 打开 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择对应的工作流
4. 点击 "Run workflow" 按钮

## 🔧 最近修复与改进

### 核心优化
- ✅ 统一调整了网络请求超时时间至120秒，解决了慢响应直播源读取失败问题
- ✅ 标准化了时间戳显示为北京时间（UTC+8）
- ✅ 移除了4个持续获取失败的直播源，提高了脚本稳定性
- ✅ 更新了 `.gitignore` 文件，添加了更全面的忽略规则

### IPTV.py 修复
- ✅ 添加了 `file://` 协议支持，可读取本地直播源文件
- ✅ 实现了动态格式检测，根据内容自动区分 M3U 和 TXT 格式
- ✅ 优化了频道合并逻辑，提高了生成速度
- ✅ 修复了远程源请求失败导致的文件不更新问题
- ✅ 添加了详细的日志记录，便于故障排查
- ✅ 统一使用120秒超时设置，提高慢响应直播源的获取成功率

### tvzy.py 修复
- ✅ 修复了缺少 `import time` 导致的脚本错误
- ✅ 修改了 `should_exclude_url` 函数，允许所有 HTTP/HTTPS URL
- ✅ 优化了高质量频道过滤逻辑
- ✅ 统一使用120秒超时设置，提高慢响应直播源的获取成功率

## ⚠️ 注意事项

1. 部分直播源可能存在版权问题，请合法使用
2. 网络不稳定可能导致部分远程直播源获取失败
3. 建议定期运行脚本更新直播源列表
4. 如遇到播放源失效问题，可在 `unified_sources.py` 中替换或移除

## 📝 输出文件说明

### tvzy.py 输出
- **tzydauto.txt**: 仅包含高质量（HD/4K）频道的 TXT 格式列表

### IPTV.py 输出
- **jieguo.m3u**: M3U 格式播放列表
- **jieguo.txt**: TXT 格式直播源列表

## 🛠️ 故障排查

### 检查文件是否更新
```bash
python check_files.py
```

### 查看脚本运行情况
```bash
# 直接运行脚本查看输出
# 例如: python tvzy.py 或 python IPTV.py

# 或查看文件生成状态
python check_files.py
```

### 常见问题及解决方案

#### 问题：输出文件没有更新
- **原因1**: 远程直播源请求失败（网络问题或403/404错误）
- **解决方案1**: 检查网络连接，或更换直播源
- **原因2**: 本地测试文件缺失
- **解决方案2**: 创建 `temp_live.txt` 并添加测试频道

#### 问题：测试频道未出现在输出中
- **原因**: 文件格式检测错误
- **解决方案**: 确保脚本正确区分 M3U 和 TXT 格式内容

## 📄 免责声明

本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除。

本工具仅用于技术研究和学习目的，请勿用于商业用途。使用本工具获取的播放源时，请确保您已获得合法授权。使用者应对使用内容的合法性负责，作者不对任何法律责任负责。

## 📧 联系方式

如有问题或建议，欢迎提交 Issue 或 Pull Request。

---

**更新时间**: 2025-12-17
**版本**: 1.5.1