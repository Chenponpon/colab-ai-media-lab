# Colab AI 圖片與影片生成實驗室 (Colab AI Media Lab)

這個儲存庫用來存放跨電腦同步的 **Google Colab 生圖 / 生影片工作站與測試筆記本**，支援在不同電腦與 Google Colab（T4 / L4 / A100 GPU）之間無痛轉移。

---

## 🎯 主力工作站：寫實人像生圖 & 照片轉動態影片 (`portrait_and_i2v_studio.ipynb`)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/portrait_and_i2v_studio.ipynb)

👉 **一鍵在 Colab 開啟專屬工作站**：
https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/portrait_and_i2v_studio.ipynb

### 功能亮點：
1. **免手動上傳參考圖**：自動從 GitHub 載入 `assets/ref_1.jpg` 與 `assets/ref_2.jpg`。
2. **同風格寫實人像生圖 (`RealVisXL V5.0`)**：內建「**白床晨光底片風格（對齊參考圖）**」與「**日式和室榻榻米全身鏡風格**」雙版本優化 Prompt，支援 Image-to-Image 延伸生圖與 Text-to-Image 全新構圖。
3. **讓照片動起來 (`Wan 2.1 I2V 14B`)**：直接將兩張參考圖（以及新生成的照片）透過 140 億參數旗艦圖生影模型轉為 **5 秒（81 影格、`544x832` 直式）自然動態影片**。

---

## 📊 通用硬體邊界壓測筆記本 (`colab_image_video_benchmark.ipynb`)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/colab_image_video_benchmark.ipynb)

👉 https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/colab_image_video_benchmark.ipynb

---

## 📁 專案結構

- `assets/ref_1.jpg`, `assets/ref_2.jpg`：寫實人像與圖生影參考照片。
- `notebooks/portrait_and_i2v_studio.ipynb`：寫實人像生圖（RealVisXL V5.0）+ 照片轉動態影片（Wan 2.1 I2V 14B）工作站。
- `notebooks/colab_image_video_benchmark.ipynb`：通用解析度與 VRAM 極限壓測筆記本。
- `scripts/sync_workspace.ps1`：Windows 環境快速同步與備份腳本。
