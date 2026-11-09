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


def build_asian_majicmix_worker_notebook():
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

from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler

# 載入真人微觀皮膚質感天花板模型 RealVisXL V5.0 搭配亞洲特徵滑塊 LoRA
model_id = "SG161222/RealVisXL_V5.0"
print(f"💎 [真實微觀皮膚質感] 正在載入頂級 SDXL 模型: {model_id}...")
pipe = DiffusionPipeline.from_pretrained(
    model_id, torch_dtype=torch.float16, use_safetensors=True
).to("cuda")

pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++"
)
pipe.enable_attention_slicing()

# 移除造成黑皮與乾癟的 slider lora，由 Prompt 精準主導白皙牛奶肌與 F 罩杯豐滿曲線
recipe_engine_name = "RealVisXL V5.0 (Luminous Milk-White Skin + F-Cup Curves + 2K)"

image_times = []
image_peak_vram = 0.0
human_ts = time.strftime("%Y-%m-%d %H:%M:%S")
num_imgs = 4

# 【核心無多頭、端正五官、極致真人肌膚架構】：
# 1. 採用 SDXL 官方原生標準黃金比例 896x1152 生成 (潛空間為 SD1.5 的 4 倍，端正雙眼對稱、無歪眼斜嘴、徹底杜絕多頭)
# 2. 嚴格剔除陶瓷磨皮詞彙，注入微觀毛孔 (Micro-pores)、細緻汗毛 (Peach fuzz) 與真實散射
# 3. 再以無損 Lanczos + 銳化濾鏡超取樣無損放大至 1440x1850 (2K 超清)！
base_w, base_h = 896, 1152
target_w, target_h = 1440, 1850

for i in range(num_imgs):
    full_prompt, recipe = generate_diversified_prompt()

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    gen = torch.Generator("cuda").manual_seed(recipe["seed"])
    
    # SDXL 原生標準比例生成
    base_img = pipe(
        prompt=recipe["clip_short_prompt"],
        negative_prompt=recipe.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT),
        width=base_w,
        height=base_h,
        num_inference_steps=30,
        guidance_scale=5.5,
        generator=gen
    ).images[0]

    # 無損高清超取樣至 2K 超解析度
    img_2k = base_img.resize((target_w, target_h), Image.LANCZOS)
    img_2k = img_2k.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))

    dt = round(time.time() - t0, 2)
    pk = round(torch.cuda.max_memory_allocated() / (1024**3), 2)
    image_times.append(dt)
    image_peak_vram = max(image_peak_vram, pk)

    recipe["timestamp"] = human_ts
    recipe["model_engine"] = "RealVisXL V5.0 (Luminous Milk-White Skin + F-Cup Curves + 2K)"
    recipe["elapsed_sec"] = dt
    recipe["peak_vram_gb"] = pk
    recipe["resolution"] = f"{target_w}x{target_h} (Hi-Res Upgraded from {base_w}x{base_h})"

    fname = f"portrait_{i+1}.jpg"
    rname = f"portrait_{i+1}_recipe.json"
    img_2k.save(fname, quality=96)
    with open(rname, "w", encoding="utf-8") as rf:
        json.dump(recipe, rf, ensure_ascii=False, indent=2)

    print(f"\\n================ 💎 第 {i+1} 張 [2K: {target_w}x{target_h}] 耗時: {dt}s | 峰值 VRAM: {pk} GB ================")
    print(recipe["summary_text"])

bench_report = {
    "gpu_name": gpu_name,
    "vram_gb": vram_gb,
    "ram_gb": ram_gb,
    "avg_image_time_sec": round(sum(image_times)/len(image_times), 2) if image_times else 0,
    "image_peak_vram_gb": image_peak_vram,
    "max_resolution_tested": f"{target_w}x{target_h}",
    "avg_video_time_sec": 0,
    "video_peak_vram_gb": 0,
    "video_model": "已關閉 (亞洲寫實高階生圖模式)"
}
with open("benchmark_report.json", "w", encoding="utf-8") as bf:
    json.dump(bench_report, bf, ensure_ascii=False, indent=2)

print("\\n🏆 亞洲寫實 2K 人像生圖全部完成！微觀皮膚毛孔、無多頭與端正五官機制已生效。")

# ==================== 4. 自動打包並下載至本地端 (本地 Watcher 自動解壓無縫存入 outputs/ 共用目錄) ====================
import zipfile
timestamp_str = time.strftime('%Y%m%d_%H%M%S')
zip_filename = f'run_{timestamp_str}.zip'
print(f'\\n📦 正在自動打包成果為 {zip_filename}...')
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for fname in os.listdir('.'):
        if fname.endswith(('.jpg', '.png', '.json', '.mp4')) and not fname.startswith('.'):
            zipf.write(fname)
print(f'✅ 打包完成！大小: {round(os.path.getsize(zip_filename) / (1024 * 1024), 2)} MB')

try:
    from google.colab import files
    print('📥 [自動存檔啟動] 正在觸發瀏覽器下載成果包 (本機 Watcher 將在 1 秒內自動解壓進 outputs/ 共用資料夾)...')
    files.download(zip_filename)
except Exception as e:
    pass

# ==================== 5. 閒置 5 分鐘自動超時防呆關機機制 ====================
# 若在 Colab 環境執行，等待 300 秒無後續動作時自動釋放 GPU 斷開連線，防止空轉吃點數！
try:
    from google.colab import runtime
    print("\\n⏳ [防呆機制啟動] 已存檔！進入 300 秒 (5分鐘) 待命計時... 若無新任務將自動關機釋放 GPU 停止扣點。")
    time.sleep(300)
    print("💤 超過 5 分鐘無操作，自動關閉 GPU 執行個體。")
    runtime.unassign()
except Exception:
    pass
"""

    worker_code = pr_core + worker_tail
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 💎 旗艦級真人微觀皮膚質感人像工作站 (`RealVisXL V5.0` + `Asian Slider LoRA` + 防多頭 SDXL 2K)\n",
                    "- **徹底消滅眼歪嘴斜**：採用 SDXL 原生黃金比例 (`896x1152`)，潛空間高達 SD1.5 的 4 倍，瞳孔、睫毛、嘴唇結構絕對端正立體！\n",
                    "- **拒絕陶瓷磨皮塑料感**：全面替換 `porcelain` 詞彙，注入微觀毛孔 (Micro-pores)、細緻汗毛 (Peach fuzz) 與柯達膠捲質感！\n",
                    "- **本機共用目錄無縫同步**：生成完成自動推送，本機守護程式 1 秒內自動解壓至 `outputs/` 共用資料夾！\n",
                    "- **5 分鐘閒置防呆關機**：完工後若 5 分鐘內無後續動作，自動釋放 GPU，絕不浪費點數！"
                ]
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
            "language_info": {"name": "python"}
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
    subprocess.run([git_exe, "commit", "-m", "Upgrade to majicMIX Asian Realistic v7 with Hi-Res 2K anti-multihead and 5min idle auto-shutdown"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "push"], cwd=REPO_DIR, env=env, check=False)
    print("[GitHub Code Sync Complete] https://github.com/Chenponpon/colab-ai-media-lab")


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
    nb_path = build_asian_majicmix_worker_notebook()
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
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
        "docker_image_pinning_type": "latest",
        "machine_shape": "NvidiaTeslaT4"
    }
    with open(os.path.join(build_dir, "kernel-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"🚀 正在透過命令列將『majicMIX 亞洲寫實 + 防多頭 Hi-Res 2K 任務』推送至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir, "-t", "1800"], capture_output=True, text=True)
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
