# Unlock Git Lock File
$lockFile = ".git\index.lock"
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force
    Write-Host "[OK] Lock file cleaned" -ForegroundColor Green
} else {
    Write-Host "[OK] No lock file found" -ForegroundColor Green
}
