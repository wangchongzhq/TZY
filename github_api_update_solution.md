# GitHub API文件更新方案设计

## 问题分析

尽管项目中已经实现了基于GitHub API的文件更新方案，但用户仍然遇到了git push冲突错误。经过全面分析，可能存在以下原因：

1. 可能有未被发现的旧配置或脚本仍在执行git push操作
2. 错误日志可能来自之前的执行记录
3. 可能是本地测试环境中的遗留问题

## 彻底避免Git Push的替代方案设计

### 1. 核心方案：基于GitHub API的原子更新

**工作原理**：直接使用GitHub API的Contents API进行文件创建和更新，完全绕过git操作。

**关键特性**：
- 使用文件SHA进行乐观并发控制
- 支持创建新文件和更新现有文件
- 原子操作确保数据一致性
- 无需本地git环境和克隆操作

### 2. 详细实现步骤

#### 2.1 获取文件当前SHA（用于更新现有文件）

```bash
function get_current_sha() {
  local file_path=$1
  local max_retries=3
  local retry_count=0
  local sha
  local base_url="https://api.github.com"
  local endpoint="/repos/$REPO_OWNER/$REPO_NAME/contents/$file_path?ref=$BRANCH"
  
  while [ $retry_count -lt $max_retries ]; do
    retry_count=$((retry_count + 1))
    
    # 使用curl调用GitHub API获取文件信息
    local response=$(curl -s -w "\n%{http_code}" \
      --max-time 15 \
      --connect-timeout 5 \
      --retry 1 \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: $GITHUB_API_VERSION" \
      -H "User-Agent: $USER_AGENT" \
      "$base_url$endpoint")
    
    local http_code=$(echo "$response" | tail -n 1)
    local response_body=$(echo "$response" | head -n -1)
    
    # 处理HTTP 200（文件存在）
    if [ "$http_code" -eq 200 ]; then
      if echo "$response_body" | grep -q '"sha":"'; then
        sha=$(echo "$response_body" | grep -o '"sha":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        echo "$sha"
        return 0
      fi
    # 处理HTTP 404（文件不存在）
    elif [ "$http_code" -eq 404 ]; then
      echo ""
      return 0
    fi
    
    # 重试逻辑
    if [ $retry_count -lt $max_retries ]; then
      local wait_time=$((retry_count * 3))
      sleep $wait_time
    fi
  done
  
  echo ""
  return 0
}
```

#### 2.2 使用指数退避策略上传文件

```bash
function upload_with_retry() {
  local file_path=$1
  local max_retries=5
  local retry_count=0
  local base_delay=2
  local base_url="https://api.github.com"
  local endpoint="/repos/$REPO_OWNER/$REPO_NAME/contents/$file_path"
  local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
  
  # 验证文件存在
  if [ ! -f "$file_path" ]; then
    echo "错误: 文件 $file_path 不存在"
    return 1
  fi
  
  # 编码文件内容
  local content_base64=$(base64 -w 0 "$file_path")
  
  # 重试循环
  while [ $retry_count -lt $max_retries ]; do
    retry_count=$((retry_count + 1))
    
    # 获取最新SHA
    local current_sha=$(get_current_sha "$file_path")
    
    # 构建提交消息
    local commit_message="自动更新: $file_path ($timestamp)"
    
    # 构建JSON数据
    local json_data
    if [ -n "$current_sha" ]; then
      json_data=$(cat <<EOF
{"message":"$commit_message","content":"$content_base64","sha":"$current_sha","branch":"$BRANCH"}
EOF
)
    else
      json_data=$(cat <<EOF
{"message":"$commit_message","content":"$content_base64","branch":"$BRANCH"}
EOF
)
    fi
    
    # 调用GitHub API
    local response=$(curl -s -w "\n%{http_code}" \
      -X PUT \
      --max-time 60 \
      --retry 2 \
      --retry-delay 3 \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      -H "Content-Type: application/json" \
      -H "X-GitHub-Api-Version: $GITHUB_API_VERSION" \
      -H "User-Agent: $USER_AGENT" \
      "$base_url$endpoint" \
      --data "$json_data")
    
    local http_code=$(echo "$response" | tail -n 1)
    
    # 成功检查
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
      echo "成功使用GitHub API更新文件！"
      return 0
    fi
    
    # 冲突处理
    if [ "$http_code" -eq 409 ] || echo "$response" | grep -q -E 'sha|conflict'; then
      echo "检测到版本冲突，将重新获取最新SHA..."
      current_sha=""  # 强制下次获取新SHA
      continue
    fi
    
    # 指数退避
    if [ $retry_count -lt $max_retries ]; then
      local delay=$((base_delay * (2 ** (retry_count - 1))))
      # 添加随机抖动
      local jitter=$((RANDOM % (delay / 5) + 1))
      if [ $((RANDOM % 2)) -eq 0 ]; then
        delay=$((delay + jitter))
      else
        delay=$((delay - jitter))
      fi
      
      sleep $delay
    fi
  done
  
  echo "所有上传尝试均失败"
  return 1
}
```

### 3. 工作流集成方案

在GitHub Actions工作流中，完全移除git push操作，替换为上述API更新函数：

```yaml
jobs:
  update-tv-channels:
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v3
        with:
          fetch-depth: 1  # 只获取最新提交
          ref: ${{ github.ref }}
          token: ${{ secrets.GITHUB_TOKEN }}
      
      # 中间步骤：运行脚本生成文件
      - name: 运行电视直播线路收集脚本
        run: python tvzydaily.py
      
      # 使用API更新文件（替代git push）
      - name: 使用GitHub API进行文件更新
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          REPO_OWNER: ${{ github.repository_owner }}
          REPO_NAME: ${{ github.event.repository.name }}
          BRANCH: main
          GITHUB_API_VERSION: "2022-11-28"
        run: |
          # 包含上述get_current_sha和upload_with_retry函数
          # 然后调用upload_with_retry "tzydauto.txt"
          # 这里将实际函数定义包含进来
          upload_with_retry "tzydauto.txt"
```

### 4. 额外安全措施

1. **环境变量验证**：在工作流开始时验证所有必要的环境变量
2. **文件存在性检查**：在上传前确保文件存在且非空
3. **错误处理增强**：对所有API响应进行详细分析和处理
4. **日志记录**：记录详细的操作日志，便于调试
5. **监控机制**：添加基本的健康检查和监控逻辑

## 优势总结

1. **完全避免Git Push冲突**：基于API的更新不依赖Git操作，彻底消除推送冲突
2. **原子性操作**：每个文件更新都是一个原子操作，确保数据一致性
3. **更好的并发控制**：使用SHA进行乐观并发控制，支持多源更新
4. **增强的错误处理**：完善的重试机制和错误诊断
5. **更轻量级**：减少了对Git环境的依赖，降低了工作流执行的复杂度

## 实施建议

1. 确保GitHub Actions工作流配置完全移除了git push操作
2. 验证所有测试脚本也使用API方案而不是git操作
3. 在生产环境部署前进行充分的测试
4. 考虑添加监控和告警机制来跟踪更新成功率
