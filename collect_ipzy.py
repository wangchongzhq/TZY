name: Update IPZY Channels Daily

on:
  schedule:
    # 北京时间每天凌晨2点运行 (UTC 18:00)
    - cron: '0 18 * * *'
  workflow_dispatch: # 允许手动触发
  push:
    paths:
      - 'collect_ipzy.py'

jobs:
  update-ipzy:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # 增加超时时间，因为质量检测需要时间
    
    steps:
    - name: Checkout代码
      uses: actions/checkout@v3
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: 设置Python环境
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
        
    - name: 安装依赖
      run: |
        python -m pip install --upgrade pip
        pip install requests
        
    - name: 运行收集脚本
      run: |
        python collect_ipzy.py
        
    - name: 检查文件变更
      id: check_changes
      run: |
        git add ipzy_channels.txt
        git diff --staged --quiet || echo "changes=true" >> $GITHUB_OUTPUT
        
    - name: 提交更新
      if: steps.check_changes.outputs.changes == 'true'
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git commit -m "自动更新IPZY高清直播线路 [$(date +'%Y-%m-%d')]"
        git push
