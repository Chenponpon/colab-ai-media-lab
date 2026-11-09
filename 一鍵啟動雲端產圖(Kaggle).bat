@echo off
chcp 65001 >nul
title AI 寫實人像生成實驗室 — 一鍵自動化雲端跑圖
echo ========================================================
echo 🚀 正在啟動雲端 GPU (Kaggle) 寫實人像生成管線...
echo 💎 模型：RealVisXL V5.0 + Asian Slider LoRA (微觀皮膚毛孔 + 端正五官)
echo 📂 成果儲存目錄：%~dp0outputs
echo ========================================================
cd /d "%~dp0"
python scripts\kaggle_auto_runner.py
echo.
echo ========================================================
echo ✨ 全部生成完畢！成果已自動下載存入 outputs 資料夾。
echo 🎨 正在為您打開相簿總覽...
echo ========================================================
start "" "%~dp0outputs\gallery_index.html"
pause
