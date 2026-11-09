# Colab AI 圖片與影片生成實驗室 (Colab AI Media Lab)

這個儲存庫用來存放跨電腦同步的 **Google Colab 生圖 / 生影片測試筆記本與腳本**，支援在不同電腦與 Google Colab（T4 / L4 / A100 GPU）之間無痛轉移。

## 🚀 快速在 Colab 開啟（一鍵啟動）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/colab_image_video_benchmark.ipynb)

👉 **直接點擊上方「Open in Colab」按鈕**，或點擊此連結：
https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/colab_image_video_benchmark.ipynb

這會直接從你的 GitHub (`Chenponpon/colab-ai-media-lab`) 將測試筆記本載入到 Google Colab，在任何一台電腦都能一鍵開啟並切換 **L4 / A100 GPU**！

---

## 📊 硬體邊界測試清單 (T4 vs L4 vs A100)

| 測試項目 | 模型名稱 | 建議最低 GPU | A100 (40GB/80GB) 表現與邊界 |
| :--- | :--- | :--- | :--- |
| **1. 極速高畫質生圖** | **Flux.1-schnell / dev** | L4 (24GB) | 可開滿 `1024x1024` 甚至 `1536x1536` 不需量化（bfloat16 滿血版），單張約 2~6 秒 |
| **2. 輕量文字轉影片 (T2V)** | **Wan 2.1 (1.3B)** | T4 (15GB) / L4 | `832x480` (480p) 81 影格（約 5 秒影片），A100 生成約 1~2 分鐘 |
| **3. 旗艦文字/圖片轉影片** | **Wan 2.1 (14B)** | **A100 (40GB+)** | `1280x720` (720p)，畫質與物理動態極佳，這正是測試 A100 VRAM 極限的最佳指標 |

---

## 📁 專案結構

- `notebooks/colab_image_video_benchmark.ipynb`：整合硬體檢測、生圖測試（SDXL / Flux）、生影片測試（Wan 2.1）與 VRAM 壓力測試的 Colab 筆記本。
- `scripts/sync_workspace.ps1`：Windows 環境快速同步與備份腳本。
