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
sys.path.insert(0, os.path.dirname(__file__))
from prompt_randomizer import build_gallery_html


def build_svd_worker_notebook(source_image_name="portrait_2.jpg", video_name="changing_clothes_svd_5s.mp4"):
    """
    建立 SVD-XT (Stable Video Diffusion XT 雙段接力 + 光流插幀 5 秒換裝短片) Kaggle Worker Notebook
    """
    worker_code = f"""
# =========================================================================
# SVD-XT (Stable Video Diffusion) 5秒高保真換裝短片 Worker (雙段接力 + 光流平滑)
# =========================================================================
import os, sys, time, gc, json, urllib.request, subprocess
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch, psutil
from PIL import Image
import cv2
import numpy as np

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
gpu_name = f"{{torch.cuda.get_device_name(0)}} (x{{gpu_count}})" if gpu_count > 0 else "CPU"
vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_count > 0 else 0
ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
print(f"✅ 硬體檢測完成 | GPU: {{gpu_name}} | 單卡 VRAM: {{vram_gb}} GB | System RAM: {{ram_gb}} GB")

print("📦 正在安裝與確認 SVD 視頻生成依賴庫...")
subprocess.run(["pip", "install", "-q", "diffusers>=0.30.0", "transformers", "accelerate", "imageio[ffmpeg]"], check=False)

from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import export_to_video

# 使用公開無需 HF Token 的 SVD-XT 旗艦模型
model_id = "stabilityai/stable-video-diffusion-img2vid-xt"
print(f"🎬 [頂級真實照片圖生影模型] 正在載入: {{model_id}}...")

pipe = StableVideoDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    variant="fp16"
)
print("⚙️ 啟用 Model CPU Offload 節能模式...")
pipe.enable_model_cpu_offload()

# 載入通過品質檢驗的首幀 2K 母圖
mother_url = "https://raw.githubusercontent.com/Chenponpon/colab-ai-media-lab/main/assets/mother_images/{source_image_name}"
print(f"📥 正在從 GitHub 載入母圖: {{mother_url}} ...")
urllib.request.urlretrieve(mother_url, "input_mother.jpg")
input_img = Image.open("input_mother.jpg").convert("RGB")
orig_w, orig_h = input_img.size
print(f"   首幀原始解析度: {{orig_w}}x{{orig_h}}")

# SVD 標準最佳直式解析度 (576x1024，長寬均為 64 的整倍數，維持直式閨蜜並坐視角)
vid_w, vid_h = 576, 1024
img_seg1 = input_img.resize((vid_w, vid_h), Image.LANCZOS)
print(f"   縮放至 SVD 標準解析度: {{vid_w}}x{{vid_h}}")

# -------------------------------------------------------------
# 階段一：第一段 25 幀（晨袍滑落、露出蕾絲連身衣，真實物理動態）
# -------------------------------------------------------------
print("⏳ [階段一/二] 正在生成第 1 段換裝動態 (前 25 幀，motion_bucket=150)...")
t0 = time.time()
gen = torch.manual_seed(1024)

seg1_frames = pipe(
    img_seg1,
    height=vid_h,
    width=vid_w,
    num_frames=25,
    decode_chunk_size=8,
    motion_bucket_id=150, # 較高動態幅度：絲袍滑落、呼吸起伏、眼神交流
    noise_aug_strength=0.03,
    generator=gen
).frames[0]
print(f"   第 1 段完成！幀數: {{len(seg1_frames)}}")

# -------------------------------------------------------------
# 階段二：第二段 25 幀（以第一段末幀作為母圖接力，整理細肩帶與閨蜜互動）
# -------------------------------------------------------------
img_seg2 = seg1_frames[-1]
print("⏳ [階段二/二] 正在生成第 2 段接力換裝動態 (後 25 幀，motion_bucket=127)...")
gen2 = torch.manual_seed(2048)
seg2_frames = pipe(
    img_seg2,
    height=vid_h,
    width=vid_w,
    num_frames=25,
    decode_chunk_size=8,
    motion_bucket_id=127, # 自然穩定換裝微調動態
    noise_aug_strength=0.02,
    generator=gen2
).frames[0]
print(f"   第 2 段完成！幀數: {{len(seg2_frames)}}")

# 拼接兩段幀 (去除重複連接幀)
all_frames = seg1_frames + seg2_frames[1:]
total_raw_frames = len(all_frames)
print(f"🎞️ 兩段接力合成原生總幀數: {{total_raw_frames}} 幀")

# 輸出原生 49 幀臨時影片
raw_temp_path = "raw_combined.mp4"
export_to_video(all_frames, raw_temp_path, fps=10)

# -------------------------------------------------------------
# 階段三：高階光流補幀與時長擴展至完整 5 秒 (5.0s @ 20 FPS = 100 幀)
# -------------------------------------------------------------
final_vid_name = "{video_name}"
print(f"🚀 正在使用 FFmpeg 進行光流插幀平滑化，目標輸出完整 5 秒動態視頻 (20 FPS)...")
ffmpeg_cmd = [
    "ffmpeg", "-y", "-i", raw_temp_path,
    "-vf", "minterpolate=fps=20:mi_mode=mci:mc_mode=aobmc:vsbmc=1",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", "2500k",
    final_vid_name
]
res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if res.returncode != 0 or not os.path.exists(final_vid_name):
    print("⚠️ minterpolate 不可用，改用標準雙倍平滑導出...")
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_temp_path,
        "-filter:v", "setpts=2.0*PTS",
        "-r", "20",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        final_vid_name
    ], check=True)

dt = round(time.time() - t0, 2)
vid_sz_mb = round(os.path.getsize(final_vid_name) / (1024 * 1024), 2)

# 讀取真實視頻規格
cap = cv2.VideoCapture(final_vid_name)
real_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
real_fps = cap.get(cv2.CAP_PROP_FPS)
real_dur = round(real_frames / real_fps, 2) if real_fps > 0 else 0

# 即時從最終視頻導出唯一的真實驗收截圖（首幀、中幀、末幀），徹底杜絕圖片不符！
ret, f_start = cap.read()
if ret:
    cv2.imwrite("real_frame_start.jpg", f_start)

cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames // 2)
ret, f_mid = cap.read()
if ret:
    cv2.imwrite("real_frame_mid.jpg", f_mid)

cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames - 1)
ret, f_end = cap.read()
if ret:
    cv2.imwrite("real_frame_end.jpg", f_end)
cap.release()

print(f"🎉 5 秒換裝動態短片已成功輸出！耗時: {{dt}}s | 幀數: {{real_frames}} | 時長: {{real_dur}}s | 體積: {{vid_sz_mb}} MB")

bench = {{
    "engine": "Stable Video Diffusion XT (SVD-XT 2-Stage Chaining + Optical Flow)",
    "gpu": gpu_name,
    "elapsed_sec": dt,
    "frames": real_frames,
    "fps": real_fps,
    "duration_sec": real_dur,
    "resolution": f"{{vid_w}}x{{vid_h}}",
    "video_file": final_vid_name,
    "file_size_mb": vid_sz_mb
}}
with open("video_benchmark_report.json", "w", encoding="utf-8") as bf:
    json.dump(bench, bf, indent=2)
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

    nb_path = os.path.join(REPO_DIR, "auto_worker_svd.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
    print(f"✅ SVD-XT 5秒換裝短片 Notebook 建置完成: {nb_path}")
    return nb_path


def push_and_run_svd_video(source_image_name="portrait_2.jpg", target_batch_dir=None, video_name="changing_clothes_svd_5s.mp4"):
    """
    推送 SVD-XT 5 秒換裝任務至 Kaggle GPU
    """
    if target_batch_dir is None:
        target_batch_dir = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")

    # 複製母圖至 assets 供雲端下載
    assets_mother_dir = os.path.join(REPO_DIR, "assets", "mother_images")
    os.makedirs(assets_mother_dir, exist_ok=True)
    src_mother = os.path.join(target_batch_dir, source_image_name)
    dst_mother = os.path.join(assets_mother_dir, source_image_name)
    if os.path.exists(src_mother):
        shutil.copy2(src_mother, dst_mother)

    nb_path = build_svd_worker_notebook(source_image_name=source_image_name, video_name=video_name)

    git_exe = r"C:\Users\user\AppData\Local\Programs\MinGit\cmd\git.exe"
    subprocess.run([git_exe, "-C", REPO_DIR, "add", "assets/", "auto_worker_svd.ipynb", "scripts/"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "commit", "-m", "feat(video): deploy SVD-XT 5-second dynamic changing clothes worker"], check=False)
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

    push_res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir], capture_output=True, text=True)
    print(f"📡 [Kaggle 推送回應] {push_res.stdout.strip()} {push_res.stderr.strip()}")

    print(f"🚀 SVD-XT 5 秒真實換裝動態任務已成功發射至 Kaggle GPU！")
    return True


def monitor_and_download_svd(kernel_id="chenponpon/colab-ai-media-lab-gpu-v2", target_batch_dir=None, video_name="changing_clothes_svd_5s.mp4"):
    if target_batch_dir is None:
        target_batch_dir = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")

    print(f"⏳ 正在即時監控 Kaggle SVD-XT 5 秒換裝動態運算進度 ({kernel_id})...")
    start_wait = time.time()
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        elapsed = round(time.time() - start_wait, 1)
        print(f"📡 [Kaggle SVD-XT 狀態 ({elapsed}s)] {out}")

        if "complete" in out.lower():
            print(f"🎉 5 秒換裝短片雲端運算完畢！正在無損下載成果至 {target_batch_dir} ...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", target_batch_dir], check=False)
            
            # 刷新圖鑑
            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ 成果已即時注入展示圖鑑: {gallery}")
            return True

        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端運算發生錯誤，下載紀錄檔檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", target_batch_dir], check=False)
            return False

        time.sleep(15)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--push":
        push_and_run_svd_video()
    elif len(sys.argv) > 1 and sys.argv[1] == "--run":
        push_and_run_svd_video()
        monitor_and_download_svd()
    else:
        build_svd_worker_notebook()
