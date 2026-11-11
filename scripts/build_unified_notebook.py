import json
import os

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SWITCH_CONFIG_PATH = os.path.join(REPO_DIR, "configs", "benchmark_switch.json")

with open(SWITCH_CONFIG_PATH, "r", encoding="utf-8") as f:
    cfg = json.load(f)

gold = cfg["golden_standard"]
prompts = gold["prompts"]

nb = {
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 🎛️ AI 寫實換裝動態 — 全域統一對照實驗室 (Unified Benchmark Studio)\n",
        "\n",
        "### 🎯 科學化橫向對比的核心原則\n",
        "1. **【統一首幀母圖 (Golden Mother Image)】**：固定使用 98 分評級的法越混血仙女母圖 (`portrait_2.jpg`)。\n",
        "2. **【統一標準提示詞 (Identical Golden Prompts)】**：所有模型使用完全相同的換裝動態描述與負向約束詞，杜絕因詞句差異引起的結果偏差！\n",
        "3. **【統一 7:9 原圖比例 (560x720 雙側零裁切)】**：精確吻合原圖 7:9 比例，徹底杜絕畫面被截切導致兩側女孩肢體破損！\n",
        "4. **【單一開關面板 (Interactive Switch)】**：透過下方 Colab 表單隨選模型與硬體，一鍵執行並自動打包回傳。"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# @title 🎛️ 1. 統一對照實驗控制面板 (Unified Benchmark Controller)\n",
        "# @markdown 請在此切換您想橫向對比的模型與執行硬體：\n",
        "\n",
        "model_choice = \"Wan2.1-14B (阿里萬相旗艦 14B)\" # @param [\"Wan2.1-14B (阿里萬相旗艦 14B)\", \"SVD-XT (1.5B 輕量對照組)\", \"LTX-Video (2B DiT 對照組)\"]\n",
        "resolution_mode = \"560x720 (7:9 原圖等比零裁切 - 推薦)\" # @param [\"560x720 (7:9 原圖等比零裁切 - 推薦)\", \"480x832 (9:16 豎屏邊緣填補)\"]\n",
        "inference_steps = 25 # @param {type:\"slider\", min:15, max:40, step:5}\n",
        "\n",
        "# @markdown ---\n",
        "# @markdown 🌟 **全模型絕對一致的標準提示詞 (Golden Prompts - 嚴格控制變因)**：\n",
        f"motion_prompt = {json.dumps(prompts['golden_motion_prompt'], ensure_ascii=False)} # @param {{type:\"string\"}}\n",
        f"negative_prompt = {json.dumps(prompts['golden_negative_prompt'], ensure_ascii=False)} # @param {{type:\"string\"}}\n",
        "\n",
        "print('✅ 實驗參數配置完成：')\n",
        "print(f'   - 測試模型: {model_choice}')\n",
        "print(f'   - 輸出比例: {resolution_mode}')\n",
        "print(f'   - 推理步數: {inference_steps} 步')\n",
        "print(f'   - 提示詞長度: {len(motion_prompt)} 字元 (全模型嚴格一致)')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# =========================================================================\n",
        "# 2. 硬體檢測與依賴套件安裝\n",
        "# =========================================================================\n",
        "import torch, psutil, os, sys, time, json, cv2\n",
        "\n",
        "if not torch.cuda.is_available():\n",
        "    raise RuntimeError('❌ 未檢測到 GPU！請在 Colab 頂部「執行階段」->「變更執行階段類型」選擇 A100 或 L4 GPU。')\n",
        "\n",
        "gpu_name = torch.cuda.get_device_name(0)\n",
        "vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)\n",
        "ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)\n",
        "print(f'✅ 硬體檢測通過 | GPU: {gpu_name} ({vram_gb} GB VRAM) | 系統 RAM: {ram_gb} GB')\n",
        "\n",
        "print('⏳ 正在檢查並安裝生成庫...')\n",
        "!pip install -q \"diffusers>=0.34.0\" \"transformers>=4.48.0\" \"accelerate\" \"imageio[ffmpeg]\" \"ftfy\" opencv-python Pillow"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# =========================================================================\n",
        "# 3. 載入 98 分母圖並依據 7:9 比例無損縮放 (杜絕人物裁截)\n",
        "# =========================================================================\n",
        "import urllib.request\n",
        "from PIL import Image, ImageOps\n",
        "\n",
        "mother_url = 'https://raw.githubusercontent.com/Chenponpon/colab-ai-media-lab/main/assets/mother_images/portrait_2.jpg'\n",
        "local_mother = 'input_mother.jpg'\n",
        "print(f'📥 下載 98 分鎖定母圖: {mother_url} ...')\n",
        "urllib.request.urlretrieve(mother_url, local_mother)\n",
        "orig_img = Image.open(local_mother).convert('RGB')\n",
        "ow, oh = orig_img.size\n",
        "print(f'✅ 母圖載入成功，原始尺寸: {ow}x{oh} (長寬比: {round(ow/oh, 4)})')\n",
        "\n",
        "if '560x720' in resolution_mode:\n",
        "    target_w, target_h = 560, 720 # 560/720 = 0.7778 (100% 吻合 7:9 原圖比例，雙側完全不裁切！)\n",
        "    input_img = orig_img.resize((target_w, target_h), Image.Resampling.LANCZOS)\n",
        "else:\n",
        "    target_w, target_h = 480, 832\n",
        "    # 使用鏡像反射填補邊緣，避免兩側女孩被生硬切除\n",
        "    scale = min(target_w / ow, target_h / oh)\n",
        "    nw, nh = int(ow * scale), int(oh * scale)\n",
        "    resized = orig_img.resize((nw, nh), Image.Resampling.LANCZOS)\n",
        "    input_img = Image.new('RGB', (target_w, target_h), (25, 20, 20))\n",
        "    input_img.paste(resized, ((target_w - nw) // 2, (target_h - nh) // 2))\n",
        "\n",
        "input_img.save('input_prepared.jpg', quality=98)\n",
        "print(f'✅ 母圖已準備就緒: {target_w}x{target_h} (保證三位混血女孩全部完整入鏡，零截肢！)')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# =========================================================================\n",
        "# 4. 統一模型推理引擎 (依據開關動態執行指定架構)\n",
        "# =========================================================================\n",
        "from diffusers.utils import export_to_video\n",
        "\n",
        "out_vid_name = 'benchmark_comparison.mp4'\n",
        "t0 = time.time()\n",
        "fps = 16\n",
        "total_frames = 81\n",
        "\n",
        "if 'Wan2.1' in model_choice:\n",
        "    from diffusers import WanImageToVideoPipeline\n",
        "    model_id = 'Wan-AI/Wan2.1-I2V-14B-480P-Diffusers'\n",
        "    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16\n",
        "    print(f'🚀 載入阿里萬相 Wan2.1-14B 旗艦管線 ({dtype})...')\n",
        "    pipe = WanImageToVideoPipeline.from_pretrained(model_id, torch_dtype=dtype)\n",
        "    if vram_gb >= 38.0:\n",
        "        print('🔥 [A100 滿血純顯存模式] 啟用零 PCIe 延遲 GPU 常駐！')\n",
        "        pipe.to('cuda')\n",
        "    else:\n",
        "        print(f'⚡ [省顯存模式] 顯存 {vram_gb} GB，啟用 Model CPU Offload...')\n",
        "        pipe.enable_model_cpu_offload()\n",
        "    pipe.vae.enable_tiling()\n",
        "    pipe.vae.enable_slicing()\n",
        "    generator = torch.Generator(device='cuda').manual_seed(42)\n",
        "    print(f'🎬 開始生成 Wan 2.1 換裝動態 ({total_frames} 幀 / {fps} FPS = 5.06 秒)...')\n",
        "    video_frames = pipe(\n",
        "        image=input_img,\n",
        "        prompt=motion_prompt,\n",
        "        negative_prompt=negative_prompt,\n",
        "        width=target_w,\n",
        "        height=target_h,\n",
        "        num_frames=total_frames,\n",
        "        num_inference_steps=inference_steps,\n",
        "        guidance_scale=5.0,\n",
        "        generator=generator\n",
        "    ).frames[0]\n",
        "    export_to_video(video_frames, out_vid_name, fps=fps)\n",
        "\n",
        "elif 'SVD-XT' in model_choice:\n",
        "    from diffusers import StableVideoDiffusionPipeline\n",
        "    model_id = 'stabilityai/stable-video-diffusion-img2vid-xt'\n",
        "    fps = 20\n",
        "    total_frames = 25\n",
        "    print(f'🚀 載入 SVD-XT 管線 ({model_id})...')\n",
        "    pipe = StableVideoDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16, variant='fp16')\n",
        "    pipe.to('cuda')\n",
        "    pipe.enable_model_cpu_offload()\n",
        "    generator = torch.Generator(device='cuda').manual_seed(42)\n",
        "    svd_in = input_img.resize((576, 576), Image.Resampling.LANCZOS)\n",
        "    print(f'🎬 開始生成 SVD-XT 視頻 (無文本引導，純圖像物理推演)...')\n",
        "    video_frames = pipe(svd_in, decode_chunk_size=4, generator=generator, num_frames=total_frames).frames[0]\n",
        "    export_to_video(video_frames, out_vid_name, fps=fps)\n",
        "\n",
        "elif 'LTX-Video' in model_choice:\n",
        "    from diffusers import LTXImageToVideoPipeline\n",
        "    model_id = 'Lightricks/LTX-Video'\n",
        "    print(f'🚀 載入 LTX-Video 2B DiT 管線 ({model_id})...')\n",
        "    pipe = LTXImageToVideoPipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)\n",
        "    pipe.to('cuda')\n",
        "    generator = torch.Generator(device='cuda').manual_seed(42)\n",
        "    ltx_w = (target_w // 32) * 32\n",
        "    ltx_h = (target_h // 32) * 32\n",
        "    ltx_in = input_img.resize((ltx_w, ltx_h), Image.Resampling.LANCZOS)\n",
        "    print(f'🎬 開始生成 LTX-Video 換裝動態 ({ltx_w}x{ltx_h})...')\n",
        "    video_frames = pipe(\n",
        "        image=ltx_in,\n",
        "        prompt=motion_prompt,\n",
        "        negative_prompt=negative_prompt,\n",
        "        width=ltx_w,\n",
        "        height=ltx_h,\n",
        "        num_frames=total_frames,\n",
        "        num_inference_steps=inference_steps,\n",
        "        generator=generator\n",
        "    ).frames[0]\n",
        "    export_to_video(video_frames, out_vid_name, fps=fps)\n",
        "\n",
        "dt = round(time.time() - t0, 2)\n",
        "vid_sz_mb = round(os.path.getsize(out_vid_name) / (1024 * 1024), 2)\n",
        "print(f'\\n🎉 生成完成！總耗時: {dt} 秒，檔案大小: {vid_sz_mb} MB')\n",
        "\n",
        "# 實時客觀抽檢幀\n",
        "cap = cv2.VideoCapture(out_vid_name)\n",
        "real_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))\n",
        "real_fps = cap.get(cv2.CAP_PROP_FPS)\n",
        "real_dur = round(real_frames / real_fps, 2) if real_fps > 0 else 0\n",
        "ret, f0 = cap.read()\n",
        "if ret: cv2.imwrite('real_frame_start.jpg', f0)\n",
        "cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames // 2)\n",
        "ret, fmid = cap.read()\n",
        "if ret: cv2.imwrite('real_frame_mid.jpg', fmid)\n",
        "cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames - 1)\n",
        "ret, fend = cap.read()\n",
        "if ret: cv2.imwrite('real_frame_end.jpg', fend)\n",
        "cap.release()\n",
        "\n",
        "bench = {\n",
        "    'model': model_choice,\n",
        "    'gpu': gpu_name,\n",
        "    'elapsed_sec': dt,\n",
        "    'frames': real_frames,\n",
        "    'fps': real_fps,\n",
        "    'duration_sec': real_dur,\n",
        "    'resolution': f'{target_w}x{target_h}',\n",
        "    'prompt_used': motion_prompt,\n",
        "    'video_file': out_vid_name,\n",
        "    'file_size_mb': vid_sz_mb\n",
        "}\n",
        "with open('video_benchmark_report.json', 'w', encoding='utf-8') as bf:\n",
        "    json.dump(bench, bf, indent=2, ensure_ascii=False)\n",
        "print(f'✅ 基準報告已產製: video_benchmark_report.json (實測時長: {real_dur}s, 幀數: {real_frames})')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# =========================================================================\n",
        "# 5. 自動打包並下載至本地 (本地 auto-sync watcher 自動攔截入庫)\n",
        "# =========================================================================\n",
        "from google.colab import files\n",
        "import zipfile\n",
        "\n",
        "tag = 'wan21' if 'Wan2.1' in model_choice else ('svd' if 'SVD' in model_choice else 'ltx')\n",
        "batch_zip = f'colab_{tag}_{time.strftime(\"%Y%m%d_%H%M%S\")}.zip'\n",
        "\n",
        "with zipfile.ZipFile(batch_zip, 'w') as zf:\n",
        "    zf.write(out_vid_name, arcname=f'changing_clothes_{tag}.mp4')\n",
        "    zf.write('real_frame_start.jpg')\n",
        "    zf.write('real_frame_mid.jpg')\n",
        "    zf.write('real_frame_end.jpg')\n",
        "    zf.write('video_benchmark_report.json')\n",
        "    if os.path.exists('input_prepared.jpg'):\n",
        "        zf.write('input_prepared.jpg')\n",
        "\n",
        "print(f'⬇️ 正在打包對照組成果: {batch_zip} ...')\n",
        "files.download(batch_zip)\n",
        "print('🎉 下載完成！本地 watcher 即刻自動解壓並刷新相簿！')"
      ]
    }
  ],
  "metadata": {
    "accelerator": "GPU",
    "colab": {
      "provenance": []
    },
    "kernelspec": {
      "display_name": "Python 3",
      "name": "python3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 0
}

# 1. 寫入 master 統一工作室
master_path = os.path.join(REPO_DIR, "notebooks", "unified_benchmark_worker.ipynb")
with open(master_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
print("Unified Master Notebook written to:", master_path)

# 2. 同步更新 wan21_a100_worker.ipynb 以採用 560x720 零裁切與相同 Golden Prompt
wan21_path = os.path.join(REPO_DIR, "notebooks", "wan21_a100_worker.ipynb")
with open(wan21_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)
print("Wan21 A100 Notebook synchronized to:", wan21_path)
