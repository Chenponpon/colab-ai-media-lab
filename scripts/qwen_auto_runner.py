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

def build_qwen_worker_notebook(identical_seeds=None):
    with open(os.path.join(REPO_DIR, "scripts", "prompt_randomizer.py"), "r", encoding="utf-8") as f:
        pr_code = f.read()

    pr_core = pr_code.split("def migrate_flat_outputs_to_subfolders")[0]

    worker_tail = f"""
import sys, gc, glob
import torch, psutil
from PIL import Image, ImageFilter

gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
gpu_name = f"{{torch.cuda.get_device_name(0)}} (x{{gpu_count}})" if gpu_count > 0 else "CPU"
vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if gpu_count > 0 else 0
ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
print(f"✅ 硬體檢測完成 | GPU: {{gpu_name}} | 單卡 VRAM: {{vram_gb}} GB | System RAM: {{ram_gb}} GB")

# 安裝與升級 Qwen-Image 專屬 Diffusers 與依賴
print("📦 正在確認 Qwen-Image 依賴庫...")
import subprocess
subprocess.run(["pip", "install", "-q", "diffusers>=0.41.0", "transformers>=5.17.0", "accelerate", "pillow"], check=False)

from diffusers import QwenImage21Pipeline

model_id = "Qwen/Qwen-Image-2.1-Turbo"
print(f"💎 [新世代 MMDiT 挑戰者] 正在載入頂級通義千問影像模型: {{model_id}}...")

# 啟用 CPU offload 確保 16GB 顯存毫無壓力
pipe = QwenImage21Pipeline.from_pretrained(
    model_id, torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()

image_times = []
image_peak_vram = 0.0
human_ts = time.strftime("%Y-%m-%d %H:%M:%S")
num_imgs = 4

# 固定種子清單進行嚴格 1:1 橫向對比
fixed_seeds = {identical_seeds or [42424242, 88888888, 12345678, 99999999]}

for i in range(num_imgs):
    curr_seed = fixed_seeds[i] if i < len(fixed_seeds) else None
    full_prompt, recipe = generate_diversified_prompt(seed=curr_seed)

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    gen = torch.Generator("cuda").manual_seed(recipe["seed"])
    
    # Qwen-Image 2.1-Turbo 8-12 步超速收斂，原生支援超長自然語言語義
    print(f"🎨 [Qwen-Image 生成中 #{{i+1}}/4] Seed: {{recipe['seed']}} ...")
    base_img = pipe(
        prompt=recipe["clip_short_prompt"],
        num_inference_steps=12,
        true_cfg_scale=1.0,
        generator=gen
    ).images[0]

    # 無損超取樣至 2K 超清規格
    target_w, target_h = 1440, 1850
    img_2k = base_img.resize((target_w, target_h), Image.LANCZOS)
    img_2k = img_2k.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))

    dt = round(time.time() - t0, 2)
    pk = round(torch.cuda.max_memory_allocated() / (1024**3), 2) if torch.cuda.is_available() else 0.0
    image_times.append(dt)
    image_peak_vram = max(image_peak_vram, pk)

    recipe["timestamp"] = human_ts
    recipe["model_engine"] = "Qwen-Image-2.1-Turbo (MMDiT + Qwen3-VL 語義理解)"
    recipe["elapsed_sec"] = dt
    recipe["peak_vram_gb"] = pk
    recipe["resolution"] = f"{{target_w}}x{{target_h}} (2K Enhanced)"

    fname = f"portrait_{{i+1}}.jpg"
    rname = f"portrait_{{i+1}}_recipe.json"
    img_2k.save(fname, quality=95)
    with open(rname, "w", encoding="utf-8") as rf:
        json.dump(recipe, rf, ensure_ascii=False, indent=2)
    print(f"   ➔ 已產出 {{fname}} (耗時: {{dt}}s, 顯存: {{pk}} GB)")

bench = {{
    "engine": "Qwen-Image-2.1-Turbo (MMDiT + Qwen3-VL)",
    "gpu": gpu_name,
    "vram_gb": vram_gb,
    "avg_image_sec": round(sum(image_times)/len(image_times), 2) if image_times else 0,
    "peak_vram_gb": image_peak_vram,
    "count": num_imgs
}}
with open("benchmark_report.json", "w", encoding="utf-8") as bf:
    json.dump(bench, bf, indent=2)

print("🎉 Qwen-Image 批次生成全數完成！")
"""

    nb = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# =========================================================================\n",
                    "# Qwen-Image-2.1-Turbo A/B 橫向對比實測 Worker (同一套黃金 Prompt 測試)\n",
                    "# =========================================================================\n",
                    pr_core + "\n" + worker_tail
                ]
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

    nb_path = os.path.join(REPO_DIR, "auto_worker_qwen.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
    print(f"✅ Qwen-Image 測試 Notebook 建置完成: {nb_path}")
    return nb_path


def monitor_and_download_qwen(kernel_id="chenponpon/colab-ai-media-lab-gpu-v2"):
    batch_ts = time.strftime("%Y%m%d_%H%M%S")
    run_subdir = os.path.join(OUT_DIR, f"run_{batch_ts}_qwen21")
    os.makedirs(run_subdir, exist_ok=True)

    print(f"⏳ 正在監控 Kaggle 雲端 Qwen-Image-2.1 ({kernel_id})，完成後將自動存入獨立對比資料夾: outputs/run_{batch_ts}_qwen21/")
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        print(f"📡 [Kaggle Qwen 狀態] {out}")
        if "complete" in out.lower():
            print(f"🎉 Qwen-Image 雲端執行完畢！正在下載 2K 成果至 {run_subdir} ...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            
            # 執行質檢
            try:
                from auto_evaluator import generate_audit_report
                generate_audit_report(run_subdir)
            except Exception as e:
                print(f"質檢生成跳過: {e}")

            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ A/B 對比圖鑑已即時更新: {gallery}")
            return True
        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端執行發生錯誤，正在下載紀錄檔至 {run_subdir} 供檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            return False
        time.sleep(12)


def push_and_run_qwen_gpu(identical_seeds=None):
    nb_path = build_qwen_worker_notebook(identical_seeds=identical_seeds)
    
    # Git sync
    git_exe = r"C:\Users\user\AppData\Local\Programs\MinGit\cmd\git.exe"
    subprocess.run([git_exe, "-C", REPO_DIR, "add", "auto_worker_qwen.ipynb", "scripts/"], check=False)
    subprocess.run([git_exe, "-C", REPO_DIR, "commit", "-m", "feat(qwen): deploy Qwen-Image-2.1-Turbo worker for A/B comparison"], check=False)
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

    print(f"🚀 正在推送『Qwen-Image-2.1-Turbo A/B 橫向對比實測』至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir, "-t", "1800"], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"⚠️ 推送訊息: {res.stderr}")
        return False

    return monitor_and_download_qwen(kernel_id)


if __name__ == "__main__":
    seeds_v9 = [81524489, 13838649, 99346877, 38912080]
    push_and_run_qwen_gpu(identical_seeds=seeds_v9)
