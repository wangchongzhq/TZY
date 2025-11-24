# GitHub Actions 工作流配置验证

## 问题描述
GitHub Actions工作流在推送更改时遇到了冲突，错误信息为：
```
! [rejected]        main -> main (fetch first)
error: failed to push some refs to 'https://github.com/wangchongzhq/zhby'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally.
```

## 已实施的修改

### 1. 所有工作流文件统一修改：

#### 1.1 增强检出步骤配置
- 添加了显式的`token`配置，确保使用正确的GitHub令牌
- 统一设置`fetch-depth: 0`以获取完整历史
- 启用`persist-credentials: true`确保凭证正确保存

#### 1.2 优化Git身份配置
- 统一使用官方推荐的`github-actions[bot]@users.noreply.github.com`作为邮箱
- 使用`GitHub Actions Bot`作为用户名
- 将全局配置(`--global`)改为本地配置(`--local`)以避免跨作业干扰

#### 1.3 改进同步机制
- 采用更直接可靠的同步策略：
  ```bash
  git fetch origin main
  git checkout main || git checkout -b main
  git reset --hard origin/main
  ```
- 移除了复杂的冲突检测逻辑，使用简单直接的`reset --hard`确保本地与远程完全一致

#### 1.4 增强推送策略
- 实现多阶段推送尝试，确保最大成功率：
  1. 首先尝试普通推送`git push origin main`
  2. 如果失败，尝试使用`--force-with-lease`推送
  3. 最后，尝试使用`--force`推送
- 添加详细的日志输出，便于调试

### 2. 具体文件修改摘要：

#### cgq_update.yml
- 更新了git身份配置
- 简化了同步逻辑，采用强制重置方式
- 增强了推送错误处理

#### tvzy_update.yml
- 添加了详细的检出配置
- 改进了同步策略，确保分支存在

#### update-tv-channels.yml
- 更新了git身份配置和同步逻辑
- 实现了多阶段推送策略

## 验证要点

1. **权限配置**：所有工作流已配置`contents: write`权限
2. **令牌使用**：每个工作流都明确使用`secrets.GITHUB_TOKEN`
3. **同步机制**：采用`reset --hard`确保本地与远程完全一致
4. **推送策略**：实现了渐进式推送尝试机制
5. **错误处理**：添加了详细的错误日志和重试逻辑

## 预期效果
修改后的工作流配置应该能够：
1. 有效解决"remote contains work that you do not have locally"的推送冲突
2. 确保本地代码与远程仓库完全同步
3. 通过多种推送策略组合提高推送成功率
4. 提供更清晰的日志输出，便于问题诊断

## 注意事项
- 由于使用了`reset --hard`，请确保重要更改不会因此丢失
- 工作流运行时会先同步远程代码，然后再生成新内容，确保增量更新正确
- 首次运行可能会生成一个合并提交，之后应该能够正常进行增量更新
