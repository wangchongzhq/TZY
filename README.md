# 多平台直播源处理工具集

## 📋 项目介绍

一个功能完整的直播源处理解决方案，能够自动提取、合并、转换和更新各类直播源，支持多种格式处理，提供完整的自动化工作流程。

## ✨ 功能特性

- **统一管理**：通过`sources.json`集中管理所有播放源
- **自动更新**：一键更新所有相关脚本的播放源配置
- **多格式支持**：支持M3U、TXT等多种直播源格式
- **自动分类**：智能分类央视频道、卫视频道、4K频道等
- **质量筛选**：自动筛选可用的高质量直播源，支持清晰度过滤
- **自动化工作流**：GitHub Actions实现定时和手动触发更新（7个工作流文件）
- **IP直播源处理**：专门的IP直播源收集和处理功能
- **格式转换**：支持M3U到TXT格式的转换
- **语法检查**：提供脚本语法检查和字符修复功能
- **频道标准化**：自动处理频道名称的错误别名和格式问题
- **EPG和台标支持**：自动添加电子节目指南和频道台标信息
- **频道过滤优化**：智能过滤购物频道和无效URL
- **模块化设计**：核心功能模块化，便于维护和扩展

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

### 4. 运行主要脚本

```bash
# 运行IP-TV直播源处理脚本（生成包含EPG和台标的M3U文件）
python IP-TV.py --update

# 运行IP直播源收集脚本
python collect_ipzy.py

# 运行直播源格式转换脚本
python convert_m3u_to_txt.py
```

## 📁 项目结构

```
├── .github/workflows/     # GitHub Actions工作流配置
│   ├── Convert M3U to TXT Daily.yml
│   ├── IPZYTXT.yml
│   ├── mainzy.yml

│   ├── update_ip-tv.yml
│   ├── update_ipzy.yml
│   └── update_sources.yml
├── config/                # 配置文件目录
│   ├── config.json        # 主配置文件
│   └── config_example.yaml # 配置示例文件
├── core/                  # 核心功能模块
│   ├── channel_utils.py   # 频道处理工具
│   ├── chinese_conversion.py # 中文转换工具
│   ├── config.py          # 配置管理
│   ├── file_utils.py      # 文件处理工具
│   ├── logging_config.py  # 日志配置
│   ├── network.py         # 网络请求工具
│   ├── parser.py          # 直播源解析器
│   └── epg_handler.py     # EPG和台标处理工具

├── logs/                  # 日志文件目录
├── tests/                 # 测试文件目录
│   ├── test_channel_utils.py
│   ├── test_config_manager.py
│   ├── test_file_utils.py
│   ├── test_logging_config.py
│   ├── test_network.py
│   └── test_parser.py
├── sources.json           # 统一播放源配置文件
├── update_sources.py      # 播放源自动更新脚本
├── unified_sources.py     # 生成的统一播放源文件（请勿手动修改）

├── IP-TV.py               # IP-TV直播源处理脚本（带EPG和台标支持）
├── collect_ipzy.py        # IP直播源收集脚本
├── convert_m3u_to_txt.py  # M3U转TXT格式转换脚本
├── check_all_syntax.py    # 语法检查脚本
├── validate_workflows.py  # 工作流验证脚本
├── check_missing_files.py # 文件引用检查脚本
├── epg_data.json          # EPG和台标数据源文件
├── filter_hd_channels.py  # HD频道过滤脚本
├── final_verification.py  # 最终验证脚本
├── ipzyauto.txt           # IP直播源频道列表
├── ipzyauto.m3u           # 自动生成的IP直播源M3U文件
├── ipzyauto.txt           # 自动生成的IP直播源TXT文件
├── tzydauto.txt           # 自动生成的直播源TXT文件
├── channel_aliases_to_add.txt # 待添加的频道别名
├── .gitignore             # Git忽略文件配置
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



**功能**：提取、合并、分类直播源，支持质量筛选和格式转换

**使用方法**：

```bash

```

**输出**：自动生成分类的直播源文件（默认：tzydauto.txt）

#### 2. IP-TV.py - IP-TV直播源处理脚本

**功能**：处理IP-TV格式的直播源，支持多种格式转换和源合并

**使用方法**：

```bash
python IP-TV.py
```

**输出**：自动生成IP-TV格式的直播源文件

#### 3. collect_ipzy.py - IP直播源收集脚本

**功能**：从多个源收集IP直播源，自动筛选高清线路，智能分类

**使用方法**：

```bash
python collect_ipzy.py
```

**输出**：自动生成分类的IP直播源文件（默认：ipzyauto.txt、ipzyauto.m3u等）

#### 4. convert_m3u_to_txt.py - M3U转TXT格式转换

**功能**：将M3U格式的直播源转换为TXT格式

**使用方法**：

```bash
python convert_m3u_to_txt.py input.m3u output.txt
```

**输出**：生成指定名称的TXT格式直播源文件

#### 5. check_all_syntax.py - 语法检查脚本

**功能**：检查所有Python脚本的语法正确性

**使用方法**：

```bash
python check_all_syntax.py
```

**输出**：显示所有脚本的语法检查结果

#### 6. validate_workflows.py - 工作流验证脚本

**功能**：验证GitHub Actions工作流配置的正确性

**使用方法**：

```bash
python validate_workflows.py
```

**输出**：显示工作流配置的验证结果

#### 7. filter_hd_channels.py - HD频道过滤脚本

**功能**：从直播源中过滤出高清频道

**使用方法**：

```bash
python filter_hd_channels.py
```

**输出**：生成高清频道列表

#### 8. final_verification.py - 最终验证脚本

**功能**：验证生成的直播源文件的完整性和可用性

**使用方法**：

```bash
python final_verification.py
```

**输出**：显示验证结果

## 🤖 自动化工作流

### GitHub Actions工作流配置

项目配置了7个自动化工作流，支持定时和手动触发：

#### 1. Convert M3U to TXT Daily.yml
- **功能**：每日自动将M3U格式转换为TXT格式
- **触发方式**：定时执行

#### 2. IPZYTXT.yml
- **功能**：IPZY直播源TXT文件更新
- **触发方式**：定时执行和手动触发

#### 3. mainzy.yml
- **功能**：主要直播源处理工作流
- **触发方式**：定时执行和手动触发



- **触发方式**：定时执行

#### 5. update_ip-tv.yml
- **功能**：IP-TV直播源定时更新
- **触发方式**：定时执行

#### 6. update_ipzy.yml
- **功能**：IPZY直播源定时更新
- **触发方式**：定时执行

#### 7. update_sources.yml
- **功能**：统一播放源配置更新
- **触发方式**：定时执行和手动触发

### 工作流执行流程

1. 检出代码仓库
2. 设置Python环境
3. 安装依赖包
4. 运行`update_sources.py`更新播放源
5. 执行相关脚本处理直播源
6. 生成输出文件
7. 提交并推送更新

### 触发方式

- **定时更新**：根据配置的时间自动运行
- **手动触发**：在GitHub Actions页面点击"Run workflow"按钮
- **代码推送**：当推送到主分支时自动触发（部分工作流）

## ⚠️ 注意事项

1. **请勿手动修改** `unified_sources.py`文件，该文件由`update_sources.py`自动生成
2. 建议定期更新播放源以确保可用性
3. 部分直播源可能存在版权问题，请合法使用
4. 如遇到播放源失效，请在`sources.json`中禁用或替换
5. 使用GitHub Actions时，请确保仓库有正确的权限设置
6. 执行脚本前，请确保已安装所有依赖包（`pip install -r requirements.txt`）
7. 部分脚本可能需要网络访问权限，请确保网络连接正常
8. 频道名称标准化功能会自动处理错误别名（如CCTV4a、CCTV4o等）

## 📝 更新日志

### 最新更新
- 修复了CCTV频道名称中的错误别名问题（如CCTV4a、CCTV4A、CCTV4o、CCTV4m等），将其转换为标准格式
- 更新了项目结构，完善了核心模块的文档说明
- 删除了M3U和TXT文件中的EPG相关功能（tvg-id、tvg-name、tvg-logo、tvg-url等属性）
- 实现了频道分类内按名称升序排序功能，提高了频道列表的可读性
- 修复了M3U文件中group-title属性后面多余空格的问题
- 清理了项目结构，优化了模块化设计

### 主要功能更新
- 实现统一播放源管理系统(`sources.json`)
- 开发自动更新脚本(`update_sources.py`)
- 配置GitHub Actions自动化工作流(7个工作流文件)
- 支持M3U、TXT等多种直播源格式处理
- 实现智能分类和质量筛选功能
- 提供IP直播源收集和处理功能
- 开发M3U转TXT格式转换工具
- 实现频道名称标准化功能

## 📄 免责声明

本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除

本工具仅用于技术研究和学习目的，请勿用于商业用途。 使用本工具获取的播放源时，请确保您已获得合法授权。 使用者应对使用内容的合法性负责，作者不对任何法律责任负责。 继续使用即表示您同意自行承担所有风险和责任。

使用规范

🔒 合法使用：请在法律允许范围内使用

📺 版权尊重：仅使用拥有合法授权的播放源

⚖️ 责任自负：使用者需自行承担相关法律责任

🚫 非商用：禁止将本工具用于商业盈利目的