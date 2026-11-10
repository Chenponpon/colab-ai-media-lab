import os
import sys
import json
import time
import shutil
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_DIR, "outputs")

def build_wan_worker_notebook(source_image_path, motion_prompt=None):
    img_name = os.path.basename(source_image_path)
    default_prompt = (
        "Three young breathtakingly gorgeous French-Vietnamese Eurasian women in sunlit white boudoir changing clothes, "
        "slowly adjusting thin floral lace shoulder straps of their sheer lingerie bodysuits, natural soft upper body movement, "
        "subtle breathing, warm alluring smiles at camera, photorealistic live-action motion, 8k quality, cinematic lighting."
    )
    motion_prompt = motion_prompt or default_prompt

    worker_code = f"""
import os, sys, time, gc
import torch, psutil
from PIL import Image

print("📦 正在確認 Wan2.1 視頻生成依賴庫...")
import subprocess
subprocess.run(["pip", "install", "-q", "diffusers>=0.41.0", "transformers>=5.17.0", "accelerate", "imageio[ffmpeg]"], check=False)

from diffusers import WanImageToVideoPipeline
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers"
print(f"🎬 [新世代開源頂級視頻模型] 正在載入萬相 Wan2.1: {{model_id}}...")

# 啟用 CPU offload 確保 16GB VRAM 零負擔流暢運行
pipe = WanImageToVideoPipeline.from_pretrained(
    model_id, torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()

source_img_file = "{img_name}"
print(f"🖼️ 載入首幀合格母圖: {{source_img_file}}")
input_img = Image.open(source_img_file).convert("RGB")
input_img = input_img.resize((832, 480))

motion_prompt = \"\"\"{motion_prompt}\"\"\"
negative_prompt = "nude, nudity, naked, topless, exposed nipples, areola, static image, jerky motion, distorted face, blurry, low quality"

print("⏳ 正在啟動 Wan2.1 圖生影管線 (81 幀 / ~5 秒 16fps 高階合規換裝動態)...")
t0 = time.time()
video_frames = pipe(
    image=input_img,
    prompt=motion_prompt,
    negative_prompt=negative_prompt,
    height=480,
    width=832,
    num_frames=81,
    guidance_scale=5.0,
    num_inference_steps=40
).frames[0]

dt = round(time.time() - t0, 2)
print(f"✨ 視頻生成完畢！耗時: {{dt}} 秒，正在輸出 MP4...")

out_vid_name = "changing_clothes_wan21.mp4"
export_to_video(video_frames, out_vid_name, fps=16)
print(f"🎉 影片已成功輸出為 {{out_vid_name}}！")
"""

    nb = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [worker_code]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    nb_path = os.path.join(REPO_DIR, "auto_worker_wan.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
    print(f"✅ Wan2.1 視頻 Worker Notebook 已就緒: {nb_path}")
    return nb_path

if __name__ == "__main__":
    print("Wan2.1 video pipeline builder ready!")
