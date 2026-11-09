# 快速將專案同步至 GitHub 的 PowerShell 腳本
param(
    [string]$CommitMessage = "Update Colab notebooks and scripts ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"
)

Set-Location $PSScriptRoot\..
git add .
git commit -m $CommitMessage
git push
Write-Host "✅ 已成功將最新程式碼與筆記本同步至 GitHub！" -ForegroundColor Green
