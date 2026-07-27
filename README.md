# IPTV直播源自动生成工具

## 项目介绍

这是一个自动化的 IPTV 直播源生成工具，能够从多个来源获取直播源并生成 M3U 和 TXT 格式的文件，方便在各种播放器中使用。

## 功能特性

- **多源获取**：从多个可靠来源获取直播源
- **自动更新**：支持手动更新和通过 GitHub Actions 定时更新
- **质量过滤**：自动过滤低质量和无效的直播源
- **分类整理**：将直播源按频道类型分类
- **4K 支持**：支持筛选 4K 高清频道
- **URL 测试**：自动测试直播源的可用性
- **缓存机制**：缓存直播源内容，提高更新速度

## 文件结构

```
├── IPTV.py            # 主脚本，生成 jieguo.m3u 和 jieguo.txt
├── IPTVTXT.py         # 辅助脚本，生成 jieguo_txt.m3u 和 jieguo_txt.txt
├── update_sources.py  # 播放源更新脚本
├── sources.json       # 直播源配置文件
├── unified_sources.py # 自动生成的统一播放源文件
├── iptv_config.json   # 配置文件
├── source_cache.json  # 缓存文件
└── .github/workflows/ # GitHub Actions 工作流
```

## 使用方法

### 手动更新

1. **更新播放源**：
   ```bash
   python update_sources.py
   ```

2. **生成直播源文件**：
   ```bash
   python IPTV.py --update
   ```

3. **只获取 4K 频道**：
   ```bash
   python IPTV.py --filter-4k
   ```

4. **检查脚本语法**：
   ```bash
   python IPTV.py --check-syntax
   ```

### 自动更新

项目配置了 GitHub Actions 工作流，会定期自动更新直播源并推送到仓库。

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
- requests
- schedule

## 许可证

本项目仅供个人学习和研究使用，请勿用于商业用途。

## 更新日志

- **2026-03-28**：添加 Node.js 24 支持，更新 GitHub Actions 配置
- **2026-03-27**：添加新的直播源，优化过滤算法
- **2026-03-26**：修复 URL 测试逻辑，提高检测速度
- **2026-03-07**：初始版本发布

---

**提示**：使用 VLC、PotPlayer、Kodi 等播放器打开生成的 M3U 文件即可观看直播。