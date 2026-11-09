import os
import sys
import json
import time
import shutil
import subprocess

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_DIR, "outputs")
sys.path.insert(0, os.path.dirname(__file__))
from prompt_randomizer import build_gallery_html


def build_self_contained_worker_notebook():
    """將最新的 scripts/prompt_randomizer.py 直接編譯進 auto_worker.ipynb，並自動掛載 Kaggle 內部高速 SSD 模型 (免外網、秒速載入)。"""
    with open(os.path.join(REPO_DIR, "scripts", "prompt_randomizer.py"), "r", encoding="utf-8") as f:
        pr_code = f.read()

    pr_core = pr_code.split("def migrate_flat_outputs_to_subfolders")[0]

    worker_tail = """
import sys, gc, glob
import torch, psutil
from PIL import Image, ImageFilter

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
gpu_name = f"{torch.cuda.get_device_name(0)} (x{gpu_count})" if gpu_count > 0 else "CPU"
vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_count > 0 else 0
ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
print(f"✅ 硬體檢測完成 | GPU: {gpu_name} | 單卡 VRAM: {vram_gb} GB | System RAM: {ram_gb} GB")

# 自動搜尋 Kaggle 內部高速掛載的 RealVisXL Diffusers 模型目錄 (免外網、10GB/s 秒速載入)
local_model_dir = None
for cand in glob.glob("/kaggle/input/**/model_index.json", recursive=True):
    d = os.path.dirname(cand)
    if os.path.exists(os.path.join(d, "unet")) and os.path.exists(os.path.join(d, "text_encoder")):
        local_model_dir = d
        break

from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

if local_model_dir:
    print(f"🚀 [極速本地 SSD 掛載] 發現 Kaggle 內部寫實模型: {local_model_dir}")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        local_model_dir, torch_dtype=torch.float16, variant="fp16", local_files_only=True
    ).to("cuda")
    engine_label = "RealVisXL (SDXL Dual-CLIP 30-Steps + Kaggle Local SSD)"
else:
    print("🌐 正在從 Hugging Face 載入 SG161222/RealVisXL_V5.0...")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "SG161222/RealVisXL_V5.0", torch_dtype=torch.float16, variant="fp16"
    ).to("cuda")
    engine_label = "RealVisXL V5.0 (SDXL Dual-CLIP 30-Steps)"

pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++"
)
pipe.vae.enable_tiling()

image_times = []
image_peak_vram = 0.0
max_res_str = "1536x2304"
human_ts = time.strftime("%Y-%m-%d %H:%M:%S")
num_imgs = 4

for i in range(num_imgs):
    nat_w, nat_h = (1024, 1536) if i == num_imgs - 1 else (960, 1440)
    out_w, out_h = (1536, 2304) if i == num_imgs - 1 else (1440, 2160)
    full_prompt, recipe = generate_diversified_prompt()

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    gen = torch.Generator("cuda").manual_seed(recipe["seed"])
    img = pipe(
        prompt=recipe["clip_short_prompt"],
        prompt_2=full_prompt,
        negative_prompt=recipe.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT),
        negative_prompt_2=recipe.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT),
        width=nat_w, height=nat_h,
        num_inference_steps=30,
        guidance_scale=5.5,
        generator=gen
    ).images[0]

    if img.size != (out_w, out_h):
        img = img.resize((out_w, out_h), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=45, threshold=3))

    dt = round(time.time() - t0, 2)
    pk = round(torch.cuda.max_memory_allocated() / (1024**3), 2)
    image_times.append(dt)
    image_peak_vram = max(image_peak_vram, pk)
    max_res_str = f"{out_w}x{out_h}"

    recipe["timestamp"] = human_ts
    recipe["model_engine"] = engine_label
    recipe["elapsed_sec"] = dt
    recipe["peak_vram_gb"] = pk
    recipe["resolution"] = f"{out_w}x{out_h}"

    fname = f"portrait_{i+1}.jpg"
    rname = f"portrait_{i+1}_recipe.json"
    img.save(fname, quality=96)
    with open(rname, "w", encoding="utf-8") as rf:
        json.dump(recipe, rf, ensure_ascii=False, indent=2)

    print(f"\\n================ 🎲 第 {i+1} 張 [{out_w}x{out_h}] 耗時: {dt}s | 峰值 VRAM: {pk} GB ================")
    print(recipe["summary_text"])

bench_report = {
    "gpu_name": gpu_name,
    "vram_gb": vram_gb,
    "ram_gb": ram_gb,
    "avg_image_time_sec": round(sum(image_times)/len(image_times), 2) if image_times else 0,
    "image_peak_vram_gb": image_peak_vram,
    "max_resolution_tested": max_res_str,
    "avg_video_time_sec": 0,
    "video_peak_vram_gb": 0,
    "video_model": "已關閉 (純生圖極速模式)"
}
with open("benchmark_report.json", "w", encoding="utf-8") as bf:
    json.dump(bench_report, bf, ensure_ascii=False, indent=2)

print("\\n🏆 雲端 2K 寫實生圖全部完成！")
"""

    worker_code = pr_core + worker_tail
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# ⚡ 100% 合規雲端 GPU 2K 寫實私房寫真工作站 (內建 Kaggle SSD 高速模型掛載 + 零外網依賴)"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in worker_code.splitlines()]
            }
        ],
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "T4", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "kaggle": {
                "accelerator": "nvidiaTeslaT4",
                "dockerImageVersionId": 30627,
                "isInternetEnabled": True,
                "language": "python",
                "sourceType": "notebook",
                "isGpuEnabled": True
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }

    nb_path = os.path.join(REPO_DIR, "notebooks", "auto_worker.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    return nb_path


def sync_code_to_github():
    env = os.environ.copy()
    min_git = os.path.expandvars(r"%LOCALAPPDATA%\Programs\MinGit\cmd")
    git_exe = os.path.join(min_git, "git.exe")
    gh_cli = r"C:\Program Files\GitHub CLI"
    env["Path"] = f"{env.get('Path', '')};{min_git};{gh_cli}"
    subprocess.run([git_exe, "rm", "-r", "--cached", "--ignore-unmatch", "outputs"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "add", "."], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "commit", "-m", "Mount Kaggle internal RealVisXL SSD dataset for zero-network instant 2K generation"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "push"], cwd=REPO_DIR, env=env, check=False)
    print("✅ [GitHub 程式碼同步完成] https://github.com/Chenponpon/colab-ai-media-lab")


def monitor_and_download_kernel(kernel_id="chenponpon/colab-ai-media-lab-gpu-v2"):
    batch_ts = time.strftime("%Y%m%d_%H%M%S")
    run_subdir = os.path.join(OUT_DIR, f"run_{batch_ts}")
    os.makedirs(run_subdir, exist_ok=True)
    build_gallery_html(OUT_DIR)

    print(f"⏳ 正在監控 Kaggle 雲端 GPU ({kernel_id})，完成後將自動存入獨立資料夾: outputs/run_{batch_ts}/")
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        print(f"📡 [Kaggle 雲端狀態] {out}")
        if "complete" in out.lower():
            print(f"🎉 雲端執行完畢！正在將本批次 2K 圖片與配方下載至 {run_subdir} ...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ 全部下載完成！中文參數圖鑑已更新: {gallery}")
            subprocess.run(["powershell", "-Command", f'Start-Process "{gallery}"'], check=False)
            return True
        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端執行發生錯誤，正在下載紀錄檔至 {run_subdir} 供檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            return False
        time.sleep(12)


def push_and_run_headless_gpu():
    nb_path = build_self_contained_worker_notebook()
    sync_code_to_github()

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
        "dataset_sources": ["zenbot99/storydiffusion-realvisxl-v4-0"],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
        "docker_image_pinning_type": "latest",
        "machine_shape": "NvidiaTeslaT4"
    }
    with open(os.path.join(build_dir, "kernel-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"🚀 正在透過命令列將『內建 Kaggle SSD 模型掛載 + 免外網極速 2K 生圖任務』推送至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"⚠️ 推送訊息: {res.stderr}")
        return False

    return monitor_and_download_kernel(kernel_id)


if __name__ == "__main__":
    if "--monitor-only" in sys.argv:
        monitor_and_download_kernel()
    else:
        push_and_run_headless_gpu()
