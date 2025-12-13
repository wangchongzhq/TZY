# 多平台直播源处理工具集

## 📋 项目介绍

一个功能完整的直播源处理解决方案，能够自动提取、合并、转换和更新各类直播源，支持多种格式处理，提供完整的自动化工作流程。

## ✨ 功能特性

- **统一管理**：通过`sources.json`集中管理所有播放源
- **自动更新**：一键更新所有相关脚本的播放源配置
- **多格式支持**：支持M3U、TXT等多种直播源格式
- **自动分类**：智能分类央视频道、卫视频道、4K频道等
- **质量筛选**：自动筛选可用的高质量直播源，支持清晰度过滤
- **自动化工作流**：GitHub Actions实现定时和手动触发更新
- **IP直播源处理**：专门的IP直播源收集和处理功能
- **格式转换**：支持M3U到TXT格式的转换
- **语法检查**：提供脚本语法检查和字符修复功能
- **频道标准化**：自动处理频道名称的错误别名和格式问题
- **模块化设计**：核心功能模块化，便于维护和扩展
- **性能优化**：实现了网络请求缓存和并发请求控制
- **错误处理**：增强了异常处理机制，提高了系统稳定性
- **代码质量**：统一了网络请求和配置管理，移除了重复代码
- **测试覆盖**：完善了单元测试，提高了代码可靠性

## 📅 最近更新

- **频道名称标准化修复**：解决了"凤凰"、"凤凰卫视"、"凤凰中文台"、"凤凰中文卫视"等频道名称的标准化问题，确保它们都能正确映射
- **标识保留优化**：改进了频道名称处理逻辑，保留了"卫视"等重要标识
- **代码结构优化**：移除了未使用的重复函数，提高了代码效率
- **调试信息清理**：清理了开发调试信息，提高了代码可读性
- **测试完善**：添加了针对频道名称标准化的单元测试，确保功能稳定性
- **4K频道统计功能**：在channel_utils.py中添加了4K和高清频道统计功能
- **性能优化**：实现了网络请求缓存和并发请求控制
- **Core模块扩展**：完善了core模块的功能，统一了接口设计
- **项目结构优化**：将测试文件统一到tests目录，辅助脚本移动到scripts目录
- **文档更新**：完善了README.md文档，确保与代码同步

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
# 运行IPTV直播源处理脚本
python IPTV.py

# 运行IP直播源收集脚本
python ipzyauto.py
```

## 📁 项目结构

```
├── .github/workflows/     # GitHub Actions工作流配置
│   ├── Convert M3U to TXT Daily.yml
│   ├── mainzy.yml
│   ├── update_ip-tv.yml
│   └── update_sources.yml
├── config/                # 配置文件目录
│   ├── config.json        # 主配置文件
│   └── config_example.yaml # 配置示例文件
├── core/                  # 核心功能模块
│   ├── __init__.py        # 模块初始化文件
│   ├── channel_utils.py   # 频道处理工具
│   ├── chinese_conversion.py # 中文转换工具
│   ├── config.py          # 配置管理
│   ├── file_utils.py      # 文件处理工具
│   ├── logging_config.py  # 日志配置
│   ├── network.py         # 网络请求工具（带缓存功能）
│   └── parser.py          # 直播源解析器

├── tests/                 # 测试文件目录
│   ├── analyze_ipv6_4k.py
│   ├── check_4k_channels.py
│   ├── check_all_syntax.py
│   ├── check_config.py
│   ├── check_ipv6.py
│   ├── check_m3u_syntax.py
│   ├── check_network.py
│   ├── convert_m3u_to_txt.py
│   ├── debug_normalize.py
│   ├── generate_statistics.py
│   ├── resolve_conflicts.py
│   ├── test_channel_utils.py
│   ├── test_config.py
│   ├── test_file_utils.py
│   ├── test_logging_config.py
│   ├── test_network.py
│   ├── test_parser.py
│   ├── update_hd_aliases.py
│   ├── update_sources.py
│   ├── update_traditional_aliases.py
│   └── validate_workflows.py
├── sources.json           # 统一播放源配置文件
├── update_sources.py      # 播放源自动更新脚本
├── unified_sources.py     # 生成的统一播放源文件（请勿手动修改）

├── IPTV.py               # IPTV直播源处理脚本
├── ipzyauto.py            # IP直播源自动生成脚本
├── scripts/               # 辅助脚本目录
│   ├── convert_m3u_to_txt.py  # M3U转TXT格式转换脚本
│   ├── check_all_syntax.py    # 语法检查脚本
│   ├── validate_workflows.py  # 工作流验证脚本
│   ├── resolve_conflicts.py   # 冲突解决脚本
│   ├── update_hd_aliases.py   # HD频道别名更新脚本
│   └── update_traditional_aliases.py # 传统频道别名更新脚本
├── epg_data.json          # EPG数据文件
├── .gitignore             # Git忽略文件配置
├── README.md              # 项目说明文档
└── 仓库优化建议.md        # 项目优化建议文档
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

#### 1. IPTV.py - IPTV直播源处理脚本

**功能**：处理IP-TV格式的直播源，支持多种格式转换和源合并，智能分类4K频道

**使用方法**：

```bash
# 基本使用
python IPTV.py

# 查看帮助信息
python IPTV.py --help
```

**参数说明**：
- `--update`: 更新播放源配置
- `--check-syntax`: 检查脚本语法
- `--fix-encoding`: 修复字符编码问题

**输出**：自动生成IP-TV格式的直播源文件（iptv.m3u、channels.txt等）

#### 2. ipzyauto.py - IP直播源收集脚本

**功能**：从多个源收集IP直播源，自动筛选高清线路，智能分类

**使用方法**：

```bash
python ipzyauto.py
```

**输出**：自动生成分类的IP直播源文件（默认：ipzyauto.txt、ipzyauto.m3u等）

#### 3. convert_m3u_to_txt.py - M3U转TXT格式转换

**功能**：将M3U格式的直播源转换为TXT格式

**使用方法**：

```bash
python convert_m3u_to_txt.py input.m3u output.txt
```

**输出**：生成指定名称的TXT格式直播源文件

#### 4. check_all_syntax.py - 语法检查脚本

**功能**：检查所有Python脚本的语法正确性

**使用方法**：

```bash
python check_all_syntax.py
```

**输出**：显示所有脚本的语法检查结果

#### 5. validate_workflows.py - 工作流验证脚本

**功能**：验证GitHub Actions工作流配置的正确性

**使用方法**：

```bash
python validate_workflows.py
```

**输出**：显示工作流配置的验证结果





## 🤖 自动化工作流

### GitHub Actions工作流配置

项目配置了4个自动化工作流，支持定时和手动触发：

#### 1. Convert M3U to TXT Daily.yml
- **功能**：每日自动将M3U格式转换为TXT格式
- **触发方式**：定时执行

#### 2. mainzy.yml
- **功能**：主要直播源处理工作流
- **触发方式**：定时执行和手动触发

#### 3. update_ip-tv.yml
- **功能**：IP-TV直播源定时更新
- **触发方式**：定时执行

#### 4. update_sources.yml
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

### 工作流优化

- **分离功能**：不同功能的工作流已经分离，便于管理
- **错误处理**：增强了错误处理机制，添加了详细的错误日志
- **执行时间优化**：实现了增量构建和测试，避免不必要的重复执行

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
- **4K频道统计功能**：在channel_utils.py中添加了4K和高清频道统计功能
- **性能优化**：实现了网络请求缓存和并发请求控制，提高了网络请求效率
- **Core模块扩展**：完善了core模块的功能，统一了接口设计，添加了类型注解
- **项目结构优化**：将测试文件统一到tests目录，辅助脚本移动到scripts目录
- **测试完善**：添加了针对get_channel_statistics函数的单元测试
- **文档更新**：完善了README.md文档，确保与代码同步
- 修复了CCTV频道名称中的错误别名问题（如CCTV4a、CCTV4A、CCTV4o、CCTV4m等），将其转换为标准格式
- 改进了CCTV 4K/8K频道名称规范化逻辑，支持"CCTV 4K超高清"等变体格式转换为标准"CCTV4K"
- 统一了M3U和TXT解析函数的4K频道判断逻辑，确保一致性
- 修复了分组标题错误分类为4K频道的问题，仅根据频道名称判断4K属性
- 改进了4K频道判断逻辑，排除含否定词的频道（如"不包含4K"等）
- 删除了M3U和TXT文件中的EPG相关功能（tvg-id、tvg-name、tvg-logo、tvg-url等属性）
- 实现了频道分类内按名称升序排序功能，提高了频道列表的可读性
- 修复了M3U文件中group-title属性后面多余空格的问题

### 主要功能更新
- 实现统一播放源管理系统(`sources.json`)
- 开发自动更新脚本(`update_sources.py`)
- 配置GitHub Actions自动化工作流
- 支持M3U、TXT等多种直播源格式处理
- 实现智能分类和质量筛选功能
- 提供IP直播源收集和处理功能
- 开发M3U转TXT格式转换工具
- 实现频道名称标准化功能
- 统一了网络请求和配置管理，移除了重复代码
- 增强了异常处理机制，提高了系统稳定性
- 完善了单元测试，提高了代码可靠性

## 📄 免责声明

本项目仅供学习交流用途，接口数据均来源于网络，如有侵权，请联系删除

本工具仅用于技术研究和学习目的，请勿用于商业用途。 使用本工具获取的播放源时，请确保您已获得合法授权。 使用者应对使用内容的合法性负责，作者不对任何法律责任负责。 继续使用即表示您同意自行承担所有风险和责任。

使用规范

🔒 合法使用：请在法律允许范围内使用

📺 版权尊重：仅使用拥有合法授权的播放源

⚖️ 责任自负：使用者需自行承担相关法律责任

🚫 非商用：禁止将本工具用于商业盈利目的