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


def sync_code_to_github():
    """先將最新程式碼、Prompt 隨機引擎與 Notebook 同步至 GitHub，讓雲端 GPU Worker 抓取最新版本（不包含 outputs/）。"""
    env = os.environ.copy()
    min_git = os.path.expandvars(r"%LOCALAPPDATA%\Programs\MinGit\cmd")
    git_exe = os.path.join(min_git, "git.exe")
    gh_cli = r"C:\Program Files\GitHub CLI"
    env["Path"] = f"{env.get('Path', '')};{min_git};{gh_cli}"
    subprocess.run([git_exe, "rm", "-r", "--cached", "--ignore-unmatch", "outputs"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "add", "."], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "commit", "-m", "Update per-run folder structure, anti-truncation SDXL prompts, and changing-clothes I2V"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "push"], cwd=REPO_DIR, env=env, check=False)
    print("✅ [GitHub 程式碼同步完成] https://github.com/Chenponpon/colab-ai-media-lab")


def monitor_and_download_kernel(kernel_id="jpachen/colab-ai-media-lab-gpu-v2"):
    os.environ["KAGGLE_API_TOKEN"] = os.environ.get("KAGGLE_API_TOKEN", "KGAT_5671d3ad25e2be2457b4e3f93d2a1679")
    batch_ts = time.strftime("%Y%m%d_%H%M%S")
    run_subdir = os.path.join(OUT_DIR, f"run_{batch_ts}")
    os.makedirs(run_subdir, exist_ok=True)

    print(f"⏳ 正在監控 Kaggle 雲端 GPU ({kernel_id})，完成後將自動存入獨立資料夾: outputs/run_{batch_ts}/")
    while True:
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        print(f"📡 [Kaggle 雲端狀態] {out}")
        if "complete" in out.lower():
            print(f"🎉 雲端執行完畢！正在將本批次圖片與換裝動態影片下載至 {run_subdir} ...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ 全部下載完成！中文參數圖鑑已更新: {gallery}")
            subprocess.run(["powershell", "-Command", f'Start-Process "{gallery}"'], check=False)
            return True
        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端執行發生錯誤，正在下載紀錄檔至 {run_subdir} 供檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", run_subdir], check=False)
            return False
        time.sleep(15)


def push_and_run_headless_gpu():
    sync_code_to_github()

    os.environ["KAGGLE_API_TOKEN"] = os.environ.get("KAGGLE_API_TOKEN", "KGAT_5671d3ad25e2be2457b4e3f93d2a1679")
    username = "jpachen"
    slug = "colab-ai-media-lab-gpu-v2"
    kernel_id = f"{username}/{slug}"

    build_dir = os.path.join(REPO_DIR, ".kaggle_build")
    os.makedirs(build_dir, exist_ok=True)
    shutil.copy2(os.path.join(REPO_DIR, "notebooks", "auto_worker.ipynb"), os.path.join(build_dir, "auto_worker.ipynb"))

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
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": []
    }
    with open(os.path.join(build_dir, "kernel-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"🚀 正在透過命令列將新版任務推送至 Kaggle 雲端 GPU ({kernel_id})...")
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
