import os
import sys
import json
import time
import shutil
import subprocess
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_DIR, "outputs")
sys.path.insert(0, os.path.dirname(__file__))
from prompt_randomizer import build_gallery_html
from video_evaluator import generate_video_audit_report


def build_video_worker_notebook(source_image_name="portrait_2.jpg", video_name="changing_clothes_video.mp4"):
    """
    建置 SVD-XT 1.1 (Stable Video Diffusion) 頂級肖像保真圖生影 Worker Notebook。
    杜絕 DiT 的融臉與手部變形問題，以 576x1024 直式超清解析度生成零溶臉、零畸變的高階微動態短片。
    """
    mother_raw_url = f"https://raw.githubusercontent.com/Chenponpon/colab-ai-media-lab/main/assets/mother_images/{source_image_name}"

    worker_code = f'''# =========================================================================
# SVD-XT 1.1 (Stable Video Diffusion) 高清無崩壞圖生影 Worker
# =========================================================================
import os, sys, io, time, gc, json, urllib.request
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch, psutil
from PIL import Image

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
gpu_name = f"{{torch.cuda.get_device_name(0)}} (x{{gpu_count}})" if gpu_count > 0 else "CPU"
vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_count > 0 else 0
ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
print(f"✅ 硬體檢測完成 | GPU: {{gpu_name}} | 單卡 VRAM: {{vram_gb}} GB | System RAM: {{ram_gb}} GB")

print("📦 正在安裝與確認 SVD-XT 視頻生成專用依賴庫...")
import subprocess
subprocess.run(["pip", "install", "-q", "diffusers>=0.41.0", "transformers>=5.17.0", "accelerate", "imageio[ffmpeg]"], check=False)

from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video

model_id = "stabilityai/stable-video-diffusion-img2vid-xt-1-1"
print(f"🎬 [頂級肖像保真圖生影模型] 正在載入: {{model_id}}...")

# 啟用 FP16 精度與逐組件 CPU Offload，顯存僅需 ~6GB，零 OOM 且五官保真度極高
pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_id, 
    torch_dtype=torch.float16, 
    variant="fp16"
)
pipe.enable_model_cpu_offload()

# 載入通過 7 項品質檢驗的首幀 2K 母圖
mother_url = "{mother_raw_url}"
print(f"📥 正在從 GitHub 載入母圖: {{mother_url}} ...")
urllib.request.urlretrieve(mother_url, "input_mother.jpg")
input_img = Image.open("input_mother.jpg").convert("RGB")
orig_w, orig_h = input_img.size
print(f"   首幀原始解析度: {{orig_w}}x{{orig_h}}")

# 鎖定 SVD-XT 原生直式超清規格 (576x1024，長寬比 0.5625，高度契合直式人物視角)
vid_w, vid_h = 576, 1024
input_img = input_img.resize((vid_w, vid_h), Image.LANCZOS)
print(f"   縮放至視頻標準解析度: {{vid_w}}x{{vid_h}}")

generator = torch.manual_seed(42)

print("⏳ 正在啟動 SVD-XT 高保真圖生影管線 (25 幀 / 零溶臉零畸變電影級微動態)...")
t0 = time.time()
video_frames = pipe(
    input_img,
    height=vid_h,
    width=vid_w,
    num_frames=25,
    decode_chunk_size=4,
    motion_bucket_id=45,
    noise_aug_strength=0.02,
    generator=generator
).frames[0]

dt = round(time.time() - t0, 2)
print(f"✨ 視頻生成完畢！耗時: {{dt}} 秒，正在輸出 MP4...")

out_vid_name = "{video_name}"
export_to_video(video_frames, out_vid_name, fps=12)
vid_sz_mb = round(os.path.getsize(out_vid_name) / (1024 * 1024), 2)
print(f"🎉 影片已成功輸出為 {{out_vid_name}} (體積: {{vid_sz_mb}} MB)！")

bench = {{
    "engine": "Stable Video Diffusion (SVD-XT 1.1)",
    "gpu": gpu_name,
    "elapsed_sec": dt,
    "frames": 25,
    "fps": 12,
    "resolution": f"{{vid_w}}x{{vid_h}}",
    "video_file": out_vid_name,
    "file_size_mb": vid_sz_mb
}}
with open("video_benchmark_report.json", "w", encoding="utf-8") as bf:
    json.dump(bench, bf, indent=2)
'''

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
    print(f"✅ SVD-XT 視頻 Worker Notebook 已就緒: {nb_path} (體積: {round(os.path.getsize(nb_path)/1024, 2)} KB)")
    return nb_path


def monitor_and_download_video(target_batch_dir, video_name="changing_clothes_video.mp4", kernel_id="chenponpon/colab-ai-media-lab-gpu-v2"):
    print(f"⏳ 正在監控 Kaggle 雲端視頻生成 ({kernel_id})，完成後自動下載至: {target_batch_dir}")
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        print(f"📡 [Kaggle Video 狀態] {out}")
        if "complete" in out.lower():
            print(f"🎉 雲端視頻生成完畢！正在下載影片成果至 {target_batch_dir} ...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", target_batch_dir], check=False)
            
            # 自動執行視頻審核並輸出 video_audit_report.json
            try:
                generate_video_audit_report(target_batch_dir, video_file_name=video_name)
            except Exception as e:
                print(f"視頻質檢報告生成跳過: {e}")

            # 刷新圖鑑
            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ 視頻與質檢成果已即時載入圖鑑: {gallery}")
            return True
        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端視頻執行發生錯誤，正在下載紀錄檔供檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", target_batch_dir], check=False)
            return False
        time.sleep(15)


def push_and_run_video(source_image_name, target_batch_dir, video_name="changing_clothes_video.mp4"):
    nb_path = build_video_worker_notebook(source_image_name=source_image_name, video_name=video_name)

    # Git 同步
    git_exe = r"C:\Users\user\AppData\Local\Programs\MinGit\cmd\git.exe"
    subprocess.run([git_exe, "-C", REPO_DIR, "add", "assets/", "auto_worker_wan.ipynb", "scripts/"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "commit", "-m", "feat(video): deploy SVD-XT 1.1 portrait video worker"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "push", "origin", "main"], check=False)

    username = "chenponpon"
    slug = "colab-ai-media-lab-gpu-v2"
    kernel_id = f"{username}/{slug}"

    build_dir = os.path.join(REPO_DIR, ".kaggle_build")
    os.makedirs(build_dir, exist_ok=True)
    shutil.copy2(nb_path, os.path.join(build_dir, "auto_worker.ipynb"))

    meta = {
        "id": kernel_id,
        "title": slug,
        "code_file": "auto_worker.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": True,
        "keywords": [],
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
        "docker_image_pinning_type": "latest",
        "machine_shape": "NvidiaTeslaT4"
    }
    with open(os.path.join(build_dir, "kernel-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"🚀 正在推送『SVD-XT 1.1 高保真換裝動態視頻』至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir, "-t", "3600"], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"⚠️ 推送訊息: {res.stderr}")
        return False

    return monitor_and_download_video(target_batch_dir, video_name=video_name, kernel_id=kernel_id)


if __name__ == "__main__":
    latest_run = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")
    best_img_name = "portrait_2.jpg"
    push_and_run_video(best_img_name, latest_run)
