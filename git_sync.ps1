# Git Sync Script
$ErrorActionPreference = "Stop"

Write-Host "[1/4] Cleaning lock file..." -ForegroundColor Cyan
$lockFile = ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "[OK] Lock file cleaned" -ForegroundColor Green
} else {
    Write-Host "[OK] No lock file found" -ForegroundColor Green
}

Write-Host "[2/4] Pulling from remote..." -ForegroundColor Cyan
git pull --rebase origin main

Write-Host "[3/4] Committing changes..." -ForegroundColor Cyan
git add -A
git commit -m "update files"

Write-Host "[4/4] Pushing to remote..." -ForegroundColor Cyan
git push -f origin main

Write-Host "" -ForegroundColor White
Write-Host "[OK] Done!" -ForegroundColor Green
Read-Host "Press Enter to exit"
