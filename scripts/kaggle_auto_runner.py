import os
import sys
import glob
import json
import time
import shutil
import subprocess

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_DIR, "outputs")
KAGGLE_DIR = os.path.expanduser(r"~\.kaggle")
KAGGLE_JSON = os.path.join(KAGGLE_DIR, "kaggle.json")

def ensure_kaggle_credentials():
    """自動從 Downloads 資料夾尋找剛下載的 kaggle.json 並安裝至 ~/.kaggle/kaggle.json"""
    if os.path.exists(KAGGLE_JSON):
        with open(KAGGLE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    downloads = os.path.expanduser(r"~\Downloads")
    candidates = sorted(
        glob.glob(os.path.join(downloads, "kaggle*.json")),
        key=os.path.getmtime,
        reverse=True
    )
    if candidates:
        os.makedirs(KAGGLE_DIR, exist_ok=True)
        shutil.copy2(candidates[0], KAGGLE_JSON)
        print(f"✅ 已自動從下載資料夾匯入 Kaggle 憑證: {candidates[0]}")
        with open(KAGGLE_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def push_and_run_headless_gpu():
    username = "jpachen"
    slug = "colab-ai-media-lab-auto-worker"
    kernel_id = f"{username}/{slug}"

    # 建立 Kaggle Headless GPU 專用執行目錄
    build_dir = os.path.join(REPO_DIR, ".kaggle_build")
    os.makedirs(build_dir, exist_ok=True)
    shutil.copy2(os.path.join(REPO_DIR, "notebooks", "auto_worker.ipynb"), os.path.join(build_dir, "auto_worker.ipynb"))

    meta = {
        "id": kernel_id,
        "title": slug,
        "code_file": "auto_worker.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": []
    }
    with open(os.path.join(build_dir, "kernel-metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"🚀 正在透過命令列將任務直接推送至 Kaggle 雲端 GPU ({kernel_id})...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", build_dir], capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print(f"⚠️ 推送訊息: {res.stderr}")
        return False

    print("⏳ 雲端 GPU 已自動在背景開機並開始算圖與算影片！（算完會自動關機並將成品抓回本機）")
    while True:
        time.sleep(15)
        st = subprocess.run(["kaggle", "kernels", "status", kernel_id], capture_output=True, text=True)
        out = st.stdout.strip()
        print(f"📡 [Kaggle 雲端狀態] {out}")
        if "complete" in out.lower():
            print("🎉 雲端執行完畢（GPU 已自動關機）！正在將所有產出的圖片與影片下載至本機 outputs/...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", OUT_DIR], check=False)
            from prompt_randomizer import build_gallery_html
            gallery = build_gallery_html(OUT_DIR)
            print(f"✨ 全部下載完成！中文參數圖鑑已產生: {gallery}")
            subprocess.run(["powershell", "-Command", f'Start-Process "{gallery}"'], check=False)
            return True
        if "error" in out.lower() or "cancel" in out.lower():
            print(f"❌ 雲端執行發生錯誤，正在下載紀錄檔供檢查...")
            subprocess.run(["kaggle", "kernels", "output", kernel_id, "-p", OUT_DIR], check=False)
            return False

if __name__ == "__main__":
    push_and_run_headless_gpu()
