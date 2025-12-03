# 多平台直播源处理工具集

## 📋 项目介绍

一个功能完整的直播源处理解决方案，能够自动提取、合并、转换和更新各类直播源，支持多种格式处理，提供完整的自动化工作流程。

## ✨ 功能特性

- **统一管理**：通过`sources.json`集中管理所有播放源
- **自动更新**：一键更新所有相关脚本的播放源配置
- **多格式支持**：支持M3U、TXT等多种直播源格式
- **自动分类**：智能分类央视频道、卫视频道、4K频道等
- **质量筛选**：自动筛选可用的高质量直播源
- **自动化工作流**：GitHub Actions实现定时和手动触发更新
- **简化版本**：提供功能简化的脚本版本，便于快速使用

## 📋 环境要求

- Python 3.6 或更高版本
- Git 版本控制工具
- GitHub账号（用于使用自动化工作流）

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

### 3. 更新播放源

```bash
python update_sources.py
```

## 📁 项目结构

```
├── .github/workflows/     # GitHub Actions工作流配置
├── sources.json           # 统一播放源配置文件
├── update_sources.py      # 播放源自动更新脚本
├── unified_sources.py     # 生成的统一播放源文件（请勿手动修改）
├── tvzy.py                # 主要直播源处理脚本
├── tvzy_simplified.py     # 简化版直播源处理脚本
├── ipzyauto.py            # IP直播源自动处理脚本
├── ipzyauto_simplified.py # 简化版IP直播源自动处理脚本
├── collect_ipzy.py        # IP直播源收集脚本
├── convert_m3u_to_txt.py  # M3U转TXT格式转换脚本
└── README.md              # 项目说明文档
```

## 🎯 使用指南

### 播放源管理

1. **修改播放源配置**：编辑`sources.json`文件

```json
{
  "version": "1.0",
  "description": "统一播放源列表",
  "sources": [
    {
      "name": "播放源名称",
      "url": "https://example.com/source.txt",
      "enabled": true  // true: 启用，false: 禁用
    },
    // 更多播放源...
  ]
}
```

2. **更新所有脚本**：运行更新脚本

```bash
python update_sources.py
```

该命令会：
- 读取`sources.json`中的启用播放源
- 生成`unified_sources.py`统一播放源文件
- 更新所有相关脚本中的播放源配置

### 主要脚本功能

#### 1. tvzy_simplified.py - 简化版直播源处理

**功能**：提取、合并、分类直播源

**使用方法**：

```bash
python tvzy_simplified.py -o output.txt
```

**参数**：
- `-o, --output`: 输出文件名（可选，默认：tzydauto.txt）

#### 2. ipzyauto_simplified.py - 简化版IP直播源处理

**功能**：自动收集和处理IP直播源

**使用方法**：

```bash
python ipzyauto_simplified.py
```

**输出**：自动生成ipzy.txt文件

#### 3. collect_ipzy.py - IP直播源收集器

**功能**：从多个源收集IP直播源并分类

**使用方法**：

```bash
python collect_ipzy.py
```

**输出**：自动生成分类的IP直播源文件

#### 4. convert_m3u_to_txt.py - M3U转TXT格式转换

**功能**：将M3U格式的直播源转换为TXT格式

**使用方法**：

```bash
python convert_m3u_to_txt.py input.m3u output.txt
```

## 🤖 自动化工作流

### GitHub Actions自动更新

项目配置了GitHub Actions工作流，支持两种触发方式：

1. **定时更新**：每天UTC时间19点自动运行
2. **手动触发**：在GitHub Actions页面手动触发

### 工作流流程

1. 检出代码仓库
2. 设置Python环境
3. 运行`update_sources.py`更新播放源
4. 执行相关脚本处理直播源
5. 提交并推送更新

## ⚠️ 注意事项

1. **请勿手动修改** `unified_sources.py`文件，该文件由`update_sources.py`自动生成
2. 建议定期更新播放源以确保可用性
3. 部分直播源可能存在版权问题，请合法使用
4. 如遇到播放源失效，请在`sources.json`中禁用或替换
5. 使用GitHub Actions时，请确保仓库有正确的权限设置

## 📝 更新日志

- 实现统一播放源管理系统
- 开发自动更新脚本
- 配置GitHub Actions自动化工作流
- 提供简化版本脚本
- 支持多种直播源格式处理

## 📄 免责声明
本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除

## 📄 许可证
许可证
MIT License © 2024-PRESENT Govin
