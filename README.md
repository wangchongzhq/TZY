# 多平台直播源处理工具集

## 📋 项目介绍

这是一套功能完整的直播源处理解决方案，包含4K超高清直播源处理、IPTV直播源生成、电视直播线路更新等多种功能。该工具集能够自动提取、合并、转换和更新各类直播源，支持多种格式处理，提供完整的自动化工作流程。

## ✨ 功能特点

### 核心功能

#### 4K超高清直播源处理
- 🎯 **智能验证**：验证`4K_uhd_channels.txt`中的直播源URL有效性
- 🔄 **URL处理**：为GitHub原始文件URL添加ghfast.top前缀，提高访问成功率
- 📝 **频道管理**：维护4K央视频道等高质量直播源
- 📊 **状态统计**：统计有效4K频道数量，更新文件头部信息

#### IPTV直播源生成
- 📡 **IPZY直播源**：自动生成`ipzy.m3u`、`ipzy.txt`、`ipzyauto.txt`和`ipzy_channels.txt`等IPTV直播源文件
- 📊 **数据统计**：生成详细的直播源统计数据
- 🔄 **自动更新**：通过`collect_ipzy.py`和GitHub Actions每天定时更新IPTV直播源内容

#### 电视直播线路更新
- 📺 **电视线路**：使用`tvzy.py`生成`tzauto.txt`和`tvdayauto.txt`等电视直播线路
- 🔍 **内容过滤**：智能过滤和筛选直播源内容
- 📋 **格式转换**：支持多种直播源格式的相互转换

#### M3U格式处理
- 🔄 **格式转换**：使用`convert_m3u_to_txt.py`、`convert_to_txt.py`和`convert_to_txtauto.py`进行M3U和TXT格式的相互转换
- 🌐 **多源支持**：支持多种M3U格式处理
- 🧹 **去重处理**：智能去除重复的直播线路

#### 通用功能
- 🌐 **多源支持**：支持多种M3U格式（标准格式、简化格式、极简格式）
- 🔍 **编码处理**：处理不同编码的文本文件
- ⚡ **高效处理**：优化的处理算法，提高处理效率
- 🧹 **去重处理**：智能去除重复的直播线路

### 部署功能
- 🤖 **自动运行**：通过GitHub Actions每天自动定时更新各类直播源
- 🖱️ **手动触发**：支持手动运行工作流进行更新
- 📊 **详细日志**：完整记录处理过程和结果统计
- 📁 **版本控制**：自动提交更新到GitHub，支持查看历史版本

## 📁 文件结构

```
📦 TZY/
├── 📁 .github/
│   └── 📁 workflows/         # GitHub Actions工作流配置
│       ├── 📄 4k_uhd_update.yml              # 4K超高清直播源更新工作流
│       ├── 📄 Convert M3U to TXT Daily.yml   # M3U转TXT格式转换工作流
│       ├── 📄 IPZYTXT.yml                    # IPZY直播源TXT格式转换工作流
│       ├── 📄 generate-ipzyauto.yml          # 生成IPZY自动工作流
│       ├── 📄 mainzy.yml                     # 主要IPZY更新工作流
│       ├── 📄 tvzy_update.yml                # 电视直播线路更新工作流
│       ├── 📄 update-4k-channels.yml         # 更新4K频道工作流
│       ├── 📄 update-tv-channels.yml         # 更新电视频道工作流
│       └── 📄 update_ipzy.yml                # 更新IPZY工作流
├── 📄 4K_uhd_channels.txt                    # 4K超高清直播源列表
├── 📄 README.md                              # 项目说明文档
├── 📄 check_and_push.py                      # 检查并推送更新工具
├── 📄 check_live_sources.py                  # 直播源检查工具
├── 📄 cn.m3u                                 # 中文M3U直播源文件
├── 📄 collect_ipzy.py                        # 收集IPZY频道工具
├── 📄 convert_m3u_to_txt.py                   # M3U转TXT格式转换工具
├── 📄 convert_to_txt.py                      # 转换为TXT格式工具
├── 📄 convert_to_txtauto.py                  # 自动转换为TXT格式工具
├── 📄 direct_fix.py                          # 直接修复工具
├── 📄 filter_demo_urls.py                    # 演示URL过滤工具
├── 📄 ipzy.m3u                               # IPZY直播源M3U文件
├── 📄 ipzy.txt                               # IPZY直播源TXT文件
├── 📄 ipzy_channels.txt                      # IPZY频道列表
├── 📄 ipzyauto.py                            # IPZY自动生成工具
├── 📄 ipzyauto.txt                           # IPZY自动生成TXT文件

├── 📄 local_test_4K.m3u                      # 本地测试4K直播源
├── 📄 process_4k_channels.py                 # 处理4K频道工具
├── 📄 requirements.txt                       # Python依赖配置
├── 📄 test_4K_output.txt                     # 4K测试输出文件
├── 📄 test_4K_simple.txt                     # 4K简单测试文件
├── 📄 test_4K_simple_output.txt              # 4K简单测试输出
├── 📄 test_4k_channels.txt                   # 4K频道测试文件
├── 📄 test_output.txt                        # 测试输出文件
├── 📄 tvzy.log                               # 电视直播线路更新日志
├── 📄 tvzy.py                                # 电视直播线路更新工具
├── 📄 tzydauto.txt                           # 电视直播线路自动更新文件
├── 📄 tzydayauto.txt                         # 电视直播线路每日更新文件
├── 📄 update_4k_channels_from_tzydayauto.py   # 从tzydayauto.txt提取4K直播源工具
└── 📄 validate_workflows.py                  # 验证工作流配置工具
```

## 🚀 快速开始

### 环境要求
- Python 3.6 或更高版本
- Git 版本控制工具
- GitHub账号（用于自动部署工作流）

### 安装步骤

#### 1. 克隆代码库
```bash
git clone https://github.com/your-username/TZY.git
cd TZY
```

#### 2. 安装依赖
```bash
# Windows
pip install -r requirements.txt

# Linux/Mac
pip3 install -r requirements.txt
```

如果`requirements.txt`不存在或不完整，可以手动安装主要依赖：
```bash
# Windows
pip install requests

# Linux/Mac
pip3 install requests
```

#### 3. 准备输入文件

根据需要处理的直播源类型，准备相应的输入文件：

**4K超高清直播源**：
```
# 4K_uhd_channels.txt 示例内容
https://example.com/4K.m3u
https://ghfast.top/https://raw.githubusercontent.com/user/repo/master/m3u/4K.m3u
```

**IPZY直播源**：
系统会自动生成和更新IPZY直播源文件。

**电视直播线路**：
系统会自动更新电视直播线路文件。

## 💻 使用方法

### 手动运行

根据需要处理的直播源类型，选择相应的脚本运行：

#### 4K超高清直播源处理
```bash
# Windows
python process_4k_channels.py

# Linux/Mac
python3 process_4k_channels.py
```

#### IPZY直播源生成
```bash
# Windows
python ipzyauto.py
python collect_ipzy.py

# Linux/Mac
python3 ipzyauto.py
python3 collect_ipzy.py
```

#### 电视直播线路更新
```bash
# Windows
python tvzy.py

# Linux/Mac
python3 tvzy.py
```

#### 格式转换
```bash
# M3U转TXT格式
python convert_m3u_to_txt.py

# 其他格式转换
python convert_to_txt.py
python convert_to_txtauto.py
```

#### 通过PowerShell运行示例
```powershell
cd "C:\Users\Administrator\Documents\GitHub\TZY"
python process_4k_channels.py
```

### 自动运行

项目配置了多个GitHub Actions工作流，每天会自动运行不同类型的直播源更新：

#### 4K超高清直播源更新
- ⏰ **运行时间**：每天北京时间3点
- 📊 **运行结果**：自动更新`4K_uhd_channels.txt`文件
- 📝 **版本记录**：自动提交更改到GitHub

#### IPZY直播源更新
- ⏰ **运行时间**：每天北京时间凌晨2点
- 📊 **运行结果**：自动更新`ipzy.txt`、`ipzyauto.txt`等文件
- 📝 **版本记录**：自动提交更改到GitHub

#### 电视直播线路更新
- ⏰ **运行时间**：每天北京时间早上3点
- 📊 **运行结果**：自动更新`tzydayauto.txt`文件
- 📝 **版本记录**：自动提交更改到GitHub

#### M3U转TXT格式转换
- ⏰ **运行时间**：每天北京时间4:00
- 📊 **运行结果**：自动将M3U文件转换为TXT格式
- 📝 **版本记录**：自动提交更改到GitHub

#### 手动触发工作流
1. 访问项目的GitHub页面
2. 点击"Actions"选项卡
3. 选择需要运行的工作流（如"4K超高清直播源更新"）
4. 点击"Run workflow"按钮
5. 选择分支并点击"Run workflow"

## 📄 文件格式说明

### 4K超高清直播源文件

**文件格式 (4K_uhd_channels.txt)**
```
# 4K超高清直播源列表
# 更新时间: 2025-11-30
# 共包含 374 个4K超高清频道

# 4K央视频道

#4K频道,#genre#

##翡翠台4K
翡翠台4K,https://cdn6.163189.xyz/163189/fct4k
翡翠台4K,http://tbb.91mo.co:54318/udp/224.1.1.4:1234
...

##CCTV4K
CCTV4K,https://httop.top/ysp-cctv4k
CCTV4K,http://aiony.top:35455/nptv/cctv4k.m3u8
...
```

### IPZY直播源文件

**M3U格式 (ipzy.m3u)**
```
#EXTM3U
#EXTINF:-1 tvg-id="CCTV1" tvg-name="CCTV1" tvg-logo="http://example.com/logos/cctv1.png" group-title="央视",CCTV1
http://example.com/cctv1.m3u8
#EXTINF:-1 tvg-id="CCTV2" tvg-name="CCTV2" tvg-logo="http://example.com/logos/cctv2.png" group-title="央视",CCTV2
http://example.com/cctv2.m3u8
```

**TXT格式 (ipzy.txt)**
```
# IPZY直播源
# 更新时间: 2025-11-30 16:14:00

CCTV1,http://example.com/cctv1.m3u8
CCTV2,http://example.com/cctv2.m3u8
湖南卫视,http://example.com/hunan.m3u8
```

### 电视直播线路文件

**tzydayauto.txt 格式**
```
# 电视直播线路每日更新
# 更新时间: 2025-11-30 08:36:00

CCTV1,http://example.com/cctv1.m3u8
CCTV2,http://example.com/cctv2.m3u8
CCTV3,http://example.com/cctv3.m3u8
```



## 🔧 工作原理

### 4K超高清直播源处理流程
1. **读取文件**：读取`4K_uhd_channels.txt`文件内容
2. **处理URL**：为GitHub原始文件URL添加ghfast.top前缀
3. **验证有效性**：验证直播源URL的可访问性
4. **更新信息**：更新文件头部的频道数量和时间戳
5. **保存结果**：将处理后的内容写回原文件

### IPZY直播源生成流程
1. **获取源数据**：从多个来源获取IPTV直播源数据
2. **解析处理**：解析原始数据，提取频道信息和直播URL
3. **格式转换**：将数据转换为M3U和TXT格式
4. **去重过滤**：去除重复和无效的直播源
5. **统计生成**：生成直播源统计数据
6. **保存文件**：将处理后的数据保存到相应文件

### 电视直播线路更新流程
1. **获取线路**：从指定来源获取电视直播线路数据
2. **处理数据**：处理和筛选直播线路信息
3. **格式转换**：将数据转换为标准格式
4. **更新文件**：更新`tzydayauto.txt`等目标文件



### 技术实现
- **多线程下载**：使用ThreadPoolExecutor实现并行下载
- **正则表达式**：支持多种M3U格式的解析
- **编码处理**：自动检测和处理不同编码的文本
- **错误处理**：完善的异常捕获和重试机制
- **日志记录**：详细记录处理过程和结果
- **GitHub Actions**：自动化工作流配置和管理

## 🛠️ 配置选项

### 核心脚本配置

#### 4K超高清直播源处理 (process_4k_channels.py)
```python
# 文件路径配置
FILE_PATH = "4K_uhd_channels.txt"    # 输入输出文件

# 请求头配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
```

#### IPZY直播源生成 (ipzyauto.py)
```python
# 输出文件配置
m3u_output_file = "ipzy.m3u"    # M3U格式输出文件
txt_output_file = "ipzy.txt"    # TXT格式输出文件
auto_output_file = "ipzyauto.txt"    # 自动生成TXT文件

# 下载配置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
}  # 用户代理
```

#### 电视直播线路更新 (tvzy.py)
```python
# 输出文件配置
auto_output_file = "tzydauto.txt"    # 自动更新输出文件
day_output_file = "tzydayauto.txt"    # 每日更新输出文件

# 下载配置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
}  # 用户代理
```

#### IPZY频道收集 (collect_ipzy.py)
```python
# 输出文件配置
output_file = "ipzy_channels.txt"    # IPZY频道列表输出文件

# 下载配置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
}  # 用户代理
```

### 工作流配置

#### 4K超高清直播源更新工作流 (4k_uhd_update.yml)
```yaml
# 定时运行配置
on:
  schedule:
    - cron: '0 19 * * *'  # UTC时间，对应北京时间凌晨3点
  workflow_dispatch:  # 允许手动触发
```

#### IPZY直播源更新工作流 (update_ipzy.yml)
```yaml
# 定时运行配置
on:
  schedule:
    - cron: '0 18 * * *'  # UTC时间，对应北京时间凌晨2点
  workflow_dispatch:  # 允许手动触发
  push:
    paths:
      - 'collect_ipzy.py'  # 当collect_ipzy.py文件变更时触发
```

#### 电视直播线路更新工作流 (tvzy_update.yml)
```yaml
# 定时运行配置
on:
  schedule:
    - cron: '0 19 * * *'  # UTC时间，对应北京时间早上3点
  workflow_dispatch:  # 允许手动触发，可添加更新原因
```

## 📊 使用示例

### 示例1：处理4K超高清直播源

```bash
# 运行4K频道处理脚本
python process_4k_channels.py

# 输出示例
(TraeAI-4) C:\Users\Administrator\Documents\GitHub\TZY > python process_4k_channels.py

# 脚本运行成功，无错误输出
# 4K_uhd_channels.txt文件已更新
```

### 示例2：生成IPZY直播源

```bash
# 运行IPZY自动生成脚本
python ipzyauto.py

# 输出示例
🎬 IPZY直播源生成工具启动
============================================================
🔍 正在获取IPZY直播源数据...
📥 正在处理IPZY直播源...
📊 解析到多个IPTV频道
💾 正在保存到 ipzy.m3u...
✅ ipzy.m3u 保存成功!
💾 正在生成统计数据...
✅ 统计数据保存成功!
============================================================
🏆 操作完成!
⏱️ 总耗时: 45.23 秒
```

### 示例3：更新电视直播线路

```bash
# 运行电视直播线路更新脚本
python tvzy.py

# 输出示例
🎬 电视直播线路更新工具启动
============================================================
🔍 正在获取电视直播线路数据...
📥 正在处理电视直播线路...
📊 解析到多个电视直播频道
💾 正在保存到 tzydayauto.txt...
✅ tzydayauto.txt 保存成功!
============================================================
🏆 操作完成!
⏱️ 总耗时: 15.89 秒
```

### 示例4：查看生成的文件

```bash
# 查看4K超高清直播源文件
Get-Content 4K_uhd_channels.txt -TotalCount 10

# 输出示例
# 4K超高清直播源
# 更新时间: 2025-11-30 19:12:00
# 总频道数: 32,300

CCTV1,http://example.com/cctv1/4k.m3u8
CCTV2,http://example.com/cctv2/4k.m3u8
CCTV3,http://example.com/cctv3/4k.m3u8
CCTV4K,http://example.com/cctv4k/4k.m3u8
```

## ⚠️ 注意事项

### 使用须知
1. **网络连接**：运行时需要稳定的网络连接以验证直播源数据
2. **文件格式**：确保输入文件中的URL格式正确且可访问
3. **权限设置**：GitHub Actions需要正确的权限设置才能提交更改
4. **依赖安装**：确保已安装所有必要的Python依赖（主要是requests）

### 常见问题

#### Q: 为什么某些直播源验证失败？
A: 可能的原因包括：网络连接问题、URL不存在或已失效、服务器限制访问、GitHub原始文件需要代理访问。

#### Q: 为什么频道名称显示乱码？
A: 程序使用UTF-8编码处理文件，建议使用UTF-8编码保存所有输入文件。

#### Q: 如何添加新的4K直播源？
A: 在`4K_uhd_channels.txt`文件中添加新的直播源URL，格式为：频道名称,URL

#### Q: 工作流为什么没有自动运行？
A: 请检查：
- GitHub Actions是否已启用
- 定时任务配置是否正确（注意时区转换）
- 仓库权限设置是否合适
- 工作流文件是否存在且格式正确

#### Q: 如何验证生成的直播源是否有效？
A: 可以使用VLC等播放器打开生成的M3U文件，或直接测试TXT文件中的URL。

#### Q: 如何修改工作流的运行时间？
A: 编辑相应的工作流文件（.github/workflows/*.yml），修改cron表达式即可调整运行时间。

#### Q: 为什么GitHub直播源需要添加ghfast.top前缀？
A: 添加ghfast.top前缀可以提高GitHub原始文件的访问成功率，特别是在某些地区可能无法直接访问GitHub原始文件的情况下。

## 🔄 更新日志

### v2.0.1 (2025-11-30)
- ✅ 清理项目文件，移除临时报告和文档文件
- ✅ 更新README.md，保持与当前项目状态一致
- ✅ 优化项目结构，提高代码可维护性

### v2.0.0 (2025-11-30)
- ✅ 扩展为多平台直播源处理工具集
- ✅ 新增IPZY直播源生成功能（collect_ipzy.py）
- ✅ 新增电视直播线路更新功能（tvzy.py）
- ✅ 完善4K超高清直播源处理功能（process_4k_channels.py）
- ✅ 配置多个自动化工作流（9个工作流文件）
- ✅ 优化URL处理，为GitHub原始文件添加ghfast.top前缀
- ✅ 增强日志记录和统计功能
- ✅ 修复Git推送相关问题，确保自动更新正常工作
- ✅ 添加多种格式转换工具（convert_m3u_to_txt.py等）
- ✅ 优化4K频道验证和管理功能

### v1.0.0 (2025-11-29)
- ✅ 初始版本发布（4K超高清直播源合并转换工具）
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

### 开发规范
- 遵循Python PEP 8代码风格指南
- 添加适当的注释和文档字符串
- 确保新功能有适当的错误处理
- 测试新功能以确保兼容性

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📞 联系信息

如有问题或建议，请通过以下方式联系：

- 创建Issue：在GitHub仓库创建新的Issue
- 发送邮件：[your-email@example.com]()

---

**享受多平台直播源处理的便利！** 🎉

=== 测试标记 (请勿删除) ===
此文件已通过脚本自动更新
测试版本: 2.0.1
测试日期: 2025-11-30
测试ID: test_push_verification_20251130

