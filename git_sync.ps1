# Git Sync Script - Keep window open on error
$Host.UI.RawUI.WindowTitle = "Git Sync"

Write-Host "================================" -ForegroundColor White
Write-Host "        Git Sync Script          " -ForegroundColor White
Write-Host "================================" -ForegroundColor White
Write-Host ""

try {
    Write-Host "[1/4] Cleaning lock file..." -ForegroundColor Cyan
    $lockFile = ".git\index.lock"
    if (Test-Path $lockFile) {
        Remove-Item $lockFile -Force -ErrorAction Stop
        Write-Host "    [OK] Lock file cleaned" -ForegroundColor Green
    } else {
        Write-Host "    [OK] No lock file found" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "[2/4] Pulling from remote..." -ForegroundColor Cyan
    $pullResult = git pull --rebase origin main 2>&1
    Write-Host "    $pullResult" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "[3/4] Committing changes..." -ForegroundColor Cyan
    git add -A
    $commitResult = git commit -m "update files" 2>&1
    if ($commitResult -match "nothing to commit") {
        Write-Host "    [OK] No changes to commit" -ForegroundColor Yellow
    } else {
        Write-Host "    [OK] Committed" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "[4/4] Pushing to remote..." -ForegroundColor Cyan
    $pushResult = git push -f origin main 2>&1
    Write-Host "    $pushResult" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "================================" -ForegroundColor White
    Write-Host "           [OK] Done!           " -ForegroundColor Green
    Write-Host "================================" -ForegroundColor White
}
catch {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host "           [ERROR]              " -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host | Out-Null
