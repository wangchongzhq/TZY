name: Daily TV Source Update

on:
  schedule:
    - cron: '0 19 * * *'  # 每天UTC 19:00 (北京时间次日3:00)
  workflow_dispatch:  # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests
        
    - name: Run update script
      run: python tvzy_autocollect.py
      
    - name: Commit and push if changed
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add tzyauto.txt
        git diff --staged --quiet || (git commit -m "Auto-update TV sources" && git push)
