# PowerShell脚本：循环检查GitHub Actions工作流状态
for($i=0; $i -lt 30; $i++) {
    Write-Output "\n第 $($i+1) 次检查工作流状态..."
    python check_workflow_status.py
    if($LASTEXITCODE -eq 0) {
        Write-Output "\n工作流执行成功！"
        exit 0
    }
    Write-Output "等待5秒后再次检查..."
    Start-Sleep -Seconds 5
}

Write-Output "\n超过最大检查次数，工作流可能执行失败。"
exit 1