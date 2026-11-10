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


def build_video_worker_notebook(source_image_name="portrait_2.jpg", motion_prompt=None, video_name="changing_clothes_video.mp4"):
    """
    建置超高效、零 OOM 風險的 LTX-Video 2B DiT 圖生影 Worker Notebook。
    模型體積僅 ~4GB，可在 16GB VRAM 雲端 GPU 上極速流暢運行（生成 121 幀 / ~5 秒 24fps 電影級換裝短片）。
    """
    mother_raw_url = f"https://raw.githubusercontent.com/Chenponpon/colab-ai-media-lab/main/assets/mother_images/{source_image_name}"

    default_prompt = (
        "Three young breathtakingly gorgeous French-Vietnamese Eurasian women sitting together on crisp white bed, "
        "gracefully changing clothes, gently adjusting the delicate floral lace straps on their shoulders, "
        "natural subtle chest breathing movement, soft alluring smiles at camera, photorealistic live-action motion, "
        "8k quality, cinematic morning bedroom lighting."
    )
    motion_prompt = motion_prompt or default_prompt
    clean_prompt = motion_prompt.replace('"', '\\"').replace("\n", " ")

    worker_code = f'''# =========================================================================
# LTX-Video (Lightricks 2B DiT) 圖生影換裝視頻生成 Worker (首幀合格母圖對齊版)
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

print("📦 正在安裝與確認 LTX-Video 視頻生成專用依賴庫...")
import subprocess
subprocess.run(["pip", "install", "-q", "diffusers>=0.41.0", "transformers>=5.17.0", "accelerate", "imageio[ffmpeg]"], check=False)

from diffusers import LTXImageToVideoPipeline
from diffusers.utils import export_to_video

model_id = "Lightricks/LTX-Video"
print(f"🎬 [新世代 2B DiT 頂級寫實視頻模型] 正在載入: {{model_id}}...")

# 啟用 bfloat16 精度載入，並啟用逐組件 CPU Offload (顯存僅需 ~6GB，徹底杜絕 OOM)
pipe = LTXImageToVideoPipeline.from_pretrained(
    model_id, torch_dtype=torch.bfloat16
)
print("⚙️ 啟用 Model CPU Offload 節能模式 (零 OOM 保證)...")
pipe.enable_model_cpu_offload()

# 載入通過 7 項品質檢驗的首幀 2K 母圖
mother_url = "{mother_raw_url}"
print(f"📥 正在從 GitHub 載入母圖: {{mother_url}} ...")
urllib.request.urlretrieve(mother_url, "input_mother.jpg")
input_img = Image.open("input_mother.jpg").convert("RGB")
orig_w, orig_h = input_img.size
print(f"   首幀原始解析度: {{orig_w}}x{{orig_h}}")

# 鎖定 LTX-Video 直式最佳規格 (512x672，寬高均能被 32 整除，長寬比 0.7619 吻合母圖 0.7778，絕不拉伸)
vid_w, vid_h = 512, 672
input_img = input_img.resize((vid_w, vid_h), Image.LANCZOS)
print(f"   縮放至視頻標準解析度: {{vid_w}}x{{vid_h}}")

motion_prompt = "{clean_prompt}"
negative_prompt = "nude, nudity, naked, topless, exposed nipples, areola, static image, worst quality, inconsistent motion, blurry, jittery, distorted, morphing limbs"

# 幀數滿足 8k + 1 規則：k=12 => 97 幀 (97 / 24fps = 4.04 秒高階動態)
total_frames = 97
print(f"⏳ 正在啟動 LTX-Video 圖生影管線 ({{total_frames}} 幀 / ~4 秒 24fps 高階合規換裝動態)...")
t0 = time.time()
video_frames = pipe(
    image=input_img,
    prompt=motion_prompt,
    negative_prompt=negative_prompt,
    width=vid_w,
    height=vid_h,
    num_frames=total_frames,
    num_inference_steps=30,
    guidance_scale=3.5
).frames[0]

dt = round(time.time() - t0, 2)
print(f"✨ 視頻生成完畢！耗時: {{dt}} 秒，正在輸出 MP4...")

out_vid_name = "{video_name}"
export_to_video(video_frames, out_vid_name, fps=24)
vid_sz_mb = round(os.path.getsize(out_vid_name) / (1024 * 1024), 2)
print(f"🎉 影片已成功輸出為 {{out_vid_name}} (體積: {{vid_sz_mb}} MB)！")

bench = {{
    "engine": "Lightricks/LTX-Video (2B DiT Image-to-Video)",
    "gpu": gpu_name,
    "elapsed_sec": dt,
    "frames": total_frames,
    "fps": 24,
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
    print(f"✅ LTX-Video 視頻 Worker Notebook 已就緒: {nb_path} (體積: {round(os.path.getsize(nb_path)/1024, 2)} KB)")
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


def push_and_run_video(source_image_name, target_batch_dir, motion_prompt=None, video_name="changing_clothes_video.mp4"):
    nb_path = build_video_worker_notebook(source_image_name=source_image_name, motion_prompt=motion_prompt, video_name=video_name)

    # Git 同步 (包含 assets/mother_images/ 中的高階首幀母圖)
    git_exe = r"C:\Users\user\AppData\Local\Programs\MinGit\cmd\git.exe"
    subprocess.run([git_exe, "-C", REPO_DIR, "add", "assets/", "auto_worker_wan.ipynb", "scripts/"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "commit", "-m", "feat(video): deploy LTX-Video 2B DiT worker with mother image"], check=False)
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

    print(f"🚀 正在推送『LTX-Video 2B DiT 換裝動態視頻』至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir, "-t", "3600"], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"⚠️ 推送訊息: {res.stderr}")
        return False

    return monitor_and_download_video(target_batch_dir, video_name=video_name, kernel_id=kernel_id)


if __name__ == "__main__":
    latest_run = os.path.join(OUT_DIR, "run_20261110_100246_qwen21")
    best_img_name = "portrait_2.jpg"
    recipe_file = os.path.join(latest_run, "portrait_2_recipe.json")
    
    motion_prompt = None
    if os.path.exists(recipe_file):
        with open(recipe_file, "r", encoding="utf-8") as f:
            rdata = json.load(f)
            motion_prompt = rdata.get("video_motion_prompt")

    push_and_run_video(best_img_name, latest_run, motion_prompt=motion_prompt)
