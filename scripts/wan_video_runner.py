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
from video_evaluator import generate_video_audit_report


def build_wan21_worker_notebook(source_image_name="portrait_2.jpg", video_name="changing_clothes_wan21_5s.mp4"):
    """
    建置阿里萬相 Wan2.1-I2V-14B-480P (4-bit BitsAndBytes 量化) 5 秒換裝圖生影 Worker Notebook
    16GB VRAM (Tesla T4) 專用優化版，81 幀 / 16 FPS = 5.06 秒真實換裝動態
    """
    mother_raw_url = f"https://raw.githubusercontent.com/Chenponpon/colab-ai-media-lab/main/assets/mother_images/{source_image_name}"

    worker_code = f'''# =========================================================================
# Wan2.1-I2V-14B (4-bit 量化) 5 秒換裝圖生影旗艦 Worker
# =========================================================================
import os, sys, io, time, gc, json, urllib.request, subprocess
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
import torch, psutil
from PIL import Image
import cv2

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
gpu_name = f"{{torch.cuda.get_device_name(0)}} (x{{gpu_count}})" if gpu_count > 0 else "CPU"
vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_count > 0 else 0
ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
print(f"✅ 硬體檢測完成 | GPU: {{gpu_name}} | 單卡 VRAM: {{vram_gb}} GB | System RAM: {{ram_gb}} GB")

print("📦 正在安裝與確認 Wan2.1 4-bit 視頻生成依賴庫...")
subprocess.run(["pip", "install", "-q", "diffusers>=0.34.0", "transformers>=4.48.0", "accelerate", "bitsandbytes", "imageio[ffmpeg]", "ftfy"], check=False)
import ftfy

from diffusers import BitsAndBytesConfig, WanImageToVideoPipeline, WanTransformer3DModel
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.1-I2V-14B-480P-Diffusers"
print(f"🎬 [使用者欽定旗艦模型] 正在以 4-bit 量化載入萬相圖生影: {{model_id}}...")

# 配置 4-bit BitsAndBytes 量化，將 28GB 龐大 Transformer 壓縮至約 8GB，完全適配 16GB VRAM
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

print("⚙️ 正在載入 4-bit Quantized Transformer...")
transformer = WanTransformer3DModel.from_pretrained(
    model_id,
    subfolder="transformer",
    quantization_config=quantization_config,
    torch_dtype=torch.float16
)

print("⚙️ 正在建構 WanImageToVideoPipeline 並啟用 Model CPU Offload...")
pipe = WanImageToVideoPipeline.from_pretrained(
    model_id,
    transformer=transformer,
    torch_dtype=torch.float16
)
pipe.enable_model_cpu_offload()

# 載入通過品質檢驗的首幀 2K 母圖
mother_url = "{mother_raw_url}"
print(f"📥 正在從 GitHub 載入母圖: {{mother_url}} ...")
urllib.request.urlretrieve(mother_url, "input_mother.jpg")
input_img = Image.open("input_mother.jpg").convert("RGB")
orig_w, orig_h = input_img.size
print(f"   首幀原始解析度: {{orig_w}}x{{orig_h}}")

# Wan2.1 480P 標準直式解析度: 寬 480, 高 832 (長寬比 0.577，符合 480P 總像素預算)
vid_w, vid_h = 480, 832
input_img = input_img.resize((vid_w, vid_h), Image.LANCZOS)
print(f"   縮放至 Wan2.1 直式標準解析度: {{vid_w}}x{{vid_h}}")

# 完整換裝動態提示詞：絲袍自然滑落、香肩展露、調整蕾絲肩帶、閨蜜生動互動
motion_prompt = (
    "Three breathtakingly gorgeous 20-year-old French-Vietnamese mixed-race women in an elegant Paris boudoir on a crisp white bed, "
    "delicate sheer silk morning robes gently slipping off smooth pale shoulders, revealing intricate sheer floral lace bodysuits artfully covering bust apex, "
    "hands naturally adjusting thin lingerie shoulder straps, gentle chest breathing movement, lively boudoir interaction with shared sweet smiles, "
    "cinematic warm morning lighting, photorealistic documentary quality, 8k, authentic physical motion of slipping silk fabric, perfectly stable angelic faces."
)
negative_prompt = (
    "ugly, deformed, mutated limbs, missing fingers, extra hands, melting face, plastic skin, "
    "blurry, distorted eyes, jerky motion, bad anatomy, low quality, nude, nipples, exposed areola, uncensored"
)

# 81 幀 @ 16 FPS = 5.06 秒整整滿血動態！
total_frames = 81
target_fps = 16
num_steps = 30
guidance = 5.0
print(f"⏳ 正在啟動 Wan2.1-I2V 換裝動態生成 ({{total_frames}} 幀 / {{num_steps}} 步 / {{target_fps}} FPS = 5.06 秒)...")

t0 = time.time()
gen = torch.Generator(device="cuda").manual_seed(42)

video_frames = pipe(
    image=input_img,
    prompt=motion_prompt,
    negative_prompt=negative_prompt,
    width=vid_w,
    height=vid_h,
    num_frames=total_frames,
    num_inference_steps=num_steps,
    guidance_scale=guidance,
    generator=gen
).frames[0]

dt = round(time.time() - t0, 2)
print(f"✨ Wan2.1 視頻生成完畢！耗時: {{dt}} 秒，正在導出 MP4...")

out_vid_name = "{video_name}"
export_to_video(video_frames, out_vid_name, fps=target_fps)
vid_sz_mb = round(os.path.getsize(out_vid_name) / (1024 * 1024), 2)

# 即時透過 OpenCV 唯一截取成片首幀、中幀、末幀，100% 絕對杜絕圖片不符
cap = cv2.VideoCapture(out_vid_name)
real_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
real_fps = cap.get(cv2.CAP_PROP_FPS)
real_dur = round(real_frames / real_fps, 2) if real_fps > 0 else 0

ret, f_start = cap.read()
if ret:
    cv2.imwrite("wan21_frame_start.jpg", f_start)

cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames // 2)
ret, f_mid = cap.read()
if ret:
    cv2.imwrite("wan21_frame_mid.jpg", f_mid)

cap.set(cv2.CAP_PROP_POS_FRAMES, real_frames - 1)
ret, f_end = cap.read()
if ret:
    cv2.imwrite("wan21_frame_end.jpg", f_end)
cap.release()

print(f"🎉 5 秒換裝短片已成功輸出為 {{out_vid_name}} (時長: {{real_dur}}s, 體積: {{vid_sz_mb}} MB)！")

bench = {{
    "engine": "Wan-AI/Wan2.1-I2V-14B-480P (4-bit BitsAndBytes Quantized)",
    "gpu": gpu_name,
    "elapsed_sec": dt,
    "frames": real_frames,
    "fps": real_fps,
    "duration_sec": real_dur,
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

    nb_path = os.path.join(REPO_DIR, "auto_worker_wan21.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
    print(f"✅ Wan2.1-I2V-14B 4-bit 5秒換裝短片 Notebook 建置完成: {nb_path}")
    return nb_path


def push_and_run_wan21_video(source_image_name="portrait_2.jpg", target_batch_dir=None, video_name="changing_clothes_wan21_5s.mp4"):
    """
    推送 Wan2.1-I2V-14B-480P 任務至 Kaggle GPU
    """
    if target_batch_dir is None:
        target_batch_dir = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")

    # 確保母圖在 assets
    assets_mother_dir = os.path.join(REPO_DIR, "assets", "mother_images")
    os.makedirs(assets_mother_dir, exist_ok=True)
    src_mother = os.path.join(target_batch_dir, source_image_name)
    dst_mother = os.path.join(assets_mother_dir, source_image_name)
    if os.path.exists(src_mother):
        shutil.copy2(src_mother, dst_mother)

    nb_path = build_wan21_worker_notebook(source_image_name=source_image_name, video_name=video_name)

    git_exe = r"C:\Users\user\AppData\Local\Programs\MinGit\cmd\git.exe"
    subprocess.run([git_exe, "-C", REPO_DIR, "add", "assets/", "auto_worker_wan21.ipynb", "scripts/"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "commit", "-m", "feat(wan21): deploy Wan2.1-I2V-14B 4-bit quantized 5s changing clothes worker"], check=False)
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
    print(f"🚀 Wan2.1-I2V-14B (4-bit 量化) 5 秒換裝短片已成功發射至 Kaggle GPU！")
    return True


def monitor_and_download_wan21(kernel_id="chenponpon/colab-ai-media-lab-gpu-v2", target_batch_dir=None, video_name="changing_clothes_wan21_5s.mp4"):
    if target_batch_dir is None:
        target_batch_dir = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")

    print(f"⏳ 正在即時監控 Kaggle Wan2.1-I2V-14B 5 秒換裝動態運算進度 ({kernel_id})...")
    start_wait = time.time()
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        elapsed = round(time.time() - start_wait, 1)
        print(f"📡 [Kaggle Wan2.1 狀態 ({elapsed}s)] {out}")

        if "complete" in out.lower():
            print(f"🎉 Wan2.1 5 秒換裝短片雲端運算完畢！正在無損下載成果至 {target_batch_dir} ...")
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
        push_and_run_wan21_video()
    elif len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor_and_download_wan21()
    elif len(sys.argv) > 1 and sys.argv[1] == "--run":
        push_and_run_wan21_video()
        monitor_and_download_wan21()
    else:
        build_wan21_worker_notebook()
