# IPTV直播源自动生成工具

## 项目介绍

这是一个自动化的 IPTV 直播源生成工具，能够从多个来源获取直播源并生成 M3U 和 TXT 格式的文件，方便在各种播放器中使用。

## 功能特性

- **多源获取**：从多个可靠来源获取直播源
- **自动更新**：支持手动更新和通过 GitHub Actions 定时更新
- **质量过滤**：自动过滤低质量和无效的直播源
- **流可播放性验证**：直接 GET 读取流首字节，识别 m3u8 / MPEG-TS / HTTP-FLV / fMP4 等封装，并排除 HTML/XML/JSON 错误页与空响应
- **分类整理**：将直播源按频道类型分类
- **4K 支持**：支持筛选 4K 高清频道，4K 频道同样经过流可播放性验证
- **URL 测试**：多线程并发测试直播源可用性，支持 DNS 预筛、批量墙钟总预算（防止慢流拖尾导致 CI 超时）
- **缓存机制**：缓存直播源内容，提高更新速度

## 文件结构

```
├── IPTV.py               # 主脚本，生成 jieguo.m3u 和 jieguo.txt
├── IPTVTXT.py            # 辅助脚本，生成 jieguo_txt.m3u 和 jieguo_txt.txt
├── stream_validator.py   # 统一增强流验证模块（流内容识别、错误页判定、可选 ffprobe）
├── quick_url_checker.py  # 轻量级多线程 URL 批量检测器（含墙钟总预算）
├── update_sources.py     # 播放源更新脚本
├── unified_sources.py    # 自动生成的统一播放源文件
├── pre_commit_check.py   # 提交前代码质量检查（Git hook 调用）
├── convert_m3u_to_txt.py # M3U 转 TXT 工具
├── sources.json          # 直播源配置文件
├── iptv_config.json      # 配置文件（本地配置，可不入库）
├── source_cache.json     # 缓存文件
└── .github/workflows/    # GitHub Actions 工作流
```

## 使用方法

### 手动更新

1. **更新播放源**：
   ```bash
   python update_sources.py
   ```

2. **生成直播源文件**：
   ```bash
   python IPTV.py --update       # 生成 jieguo.m3u / jieguo.txt
   python IPTVTXT.py --update    # 生成 jieguo_txt.m3u / jieguo_txt.txt
   ```

3. **只获取 4K 频道**：
   ```bash
   python IPTV.py --filter-4k
   ```

4. **检查 / 修复脚本**：
   ```bash
   python IPTV.py --check-syntax  # 检查语法错误
   python IPTV.py --fix-chars     # 修复不可打印字符
   ```

### 自动更新

项目配置了 3 个 GitHub Actions 工作流，均设置了 30 分钟作业超时：

- `update_iptv.yml`：定时运行 `IPTV.py` 并提交 `jieguo.*`
- `update_iptv_txt.yml`：定时运行 `IPTVTXT.py` 并提交 `jieguo_txt.*`
- `update_sources.yml`：定时更新播放源列表

工作流会尝试安装 ffmpeg（失败不阻断主流程），仅当 `use_ffprobe` 开启时才用于深度验证。

## 直播源配置

在 `sources.json` 文件中添加或修改直播源：

```json
{
  "sources": [
    {
      "name": "源名称",
      "url": "直播源URL",
      "enabled": true
    }
  ]
}
```

## URL 验证配置

`iptv_config.json` 的 `url_testing` 段控制线路可用性检测（缺省时使用脚本内置默认值）：

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `enable` | `true` | 是否启用 URL 测试 |
| `timeout` | `2` | 单 URL 连接超时（秒） |
| `retries` | `1` | 失败重试次数 |
| `workers` | `32` | 并发线程数 |
| `use_ffprobe` | `false` | 是否调用 ffprobe 做深度验证（需已安装 ffmpeg） |
| `ffprobe_timeout` | `10` | ffprobe 超时（秒） |
| `batch_timeout` | `720` | 普通频道批量检测墙钟总预算（秒） |
| `fourk_batch_timeout` | `180` | 4K 频道批量检测墙钟总预算（秒） |

验证策略：对每个 URL 直接发起 `GET`（带 `Range` 请求、流式读取），通过响应首字节判断封装类型（m3u8 / MPEG-TS / FLV / fMP4 等），仅当明确返回 HTML/XML/JSON 错误页、404/Forbidden 文本或空响应时才判为无效，无法识别但非错误页的内容予以放行，避免误杀有效直播流。`blacklist` 段可配置需排除的协议、关键字与词边界黑名单。

## 输出文件

- **jieguo.m3u**：生成的 M3U 格式直播源文件
- **jieguo.txt**：生成的 TXT 格式直播源文件
- **jieguo_txt.m3u**：备选 M3U 格式直播源文件
- **jieguo_txt.txt**：备选 TXT 格式直播源文件

## 注意事项

- 请确保网络连接正常，以便获取直播源
- 部分直播源可能会随时间失效，工具会自动过滤无效源
- 生成过程可能需要几分钟时间，取决于网络速度和直播源数量

## 依赖项

- Python 3.x
- requests >= 2.25.0
- urllib3 >= 1.26.0
- ffmpeg（可选，仅在开启 `use_ffprobe` 深度验证时需要）

## 许可证

本项目仅供个人学习和研究使用，请勿用于商业用途。

## 更新日志

- **2026-09-30**：
  - 新增 `stream_validator.py` 统一增强流验证模块，并强化 `quick_url_checker.py`
  - 改为直接 GET 读取流首字节，识别 m3u8 / MPEG-TS / HTTP-FLV / fMP4，修复 FLV 流及"HEAD 被 CDN 拒绝"导致的有效线路误杀（实测有效频道约由 1500 提升至 2900+）
  - 4K 频道纳入与普通频道一致的流可播放性验证
  - URL 批量检测增加墙钟总预算（默认普通 720s / 4K 180s），防止慢流拖尾导致 GitHub Actions 30 分钟超时
  - 黑名单配置化并采用词边界匹配，工作流支持可选安装 ffmpeg
- **2026-03-28**：添加 Node.js 24 支持，更新 GitHub Actions 配置
- **2026-03-27**：添加新的直播源，优化过滤算法
- **2026-03-26**：修复 URL 测试逻辑，提高检测速度
- **2026-03-07**：初始版本发布

---

**提示**：使用 VLC、PotPlayer、Kodi 等播放器打开生成的 M3U 文件即可观看直播。