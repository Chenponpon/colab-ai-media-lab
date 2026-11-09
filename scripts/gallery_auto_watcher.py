import os
import sys
import time
import zipfile

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.prompt_randomizer import build_gallery_html

OUTPUTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

def get_state(path):
    state = {}
    if not os.path.exists(path):
        return state
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                if f == "gallery_index.html":
                    continue
                fp = os.path.join(root, f)
                try:
                    state[fp] = os.path.getmtime(fp)
                except OSError:
                    pass
    except Exception:
        pass
    return state

def check_colab_downloads():
    if not os.path.exists(DOWNLOADS_DIR):
        return False
    extracted_any = False
    try:
        for fname in os.listdir(DOWNLOADS_DIR):
            if (fname.startswith("run_") or fname.startswith("colab_")) and fname.endswith(".zip"):
                zpath = os.path.join(DOWNLOADS_DIR, fname)
                folder_name = os.path.splitext(fname)[0]
                target_folder = os.path.join(OUTPUTS_DIR, folder_name)
                try:
                    # 測試是否可以完整讀取 (避免讀取下載中檔案)
                    with zipfile.ZipFile(zpath, 'r') as zf:
                        zf.extractall(target_folder)
                    os.remove(zpath)
                    print(f"[Auto-Sync] 🚀 成功攔截 Colab 下載包 {fname}，已自動解壓存入共用資料夾：{target_folder}！")
                    extracted_any = True
                except Exception:
                    pass
    except Exception:
        pass
    return extracted_any

def main():
    print(f"[Watcher] 開始即時監控 outputs 目錄：{OUTPUTS_DIR}")
    print(f"[Auto-Sync] Colab 下載無縫自動攔截同步已啟動：{DOWNLOADS_DIR} ➔ {OUTPUTS_DIR}")
    build_gallery_html(OUTPUTS_DIR)
    prev_state = get_state(OUTPUTS_DIR)
    
    while True:
        time.sleep(2.0)
        # 1. 檢查 Colab 瀏覽器自動下載並無縫搬移
        if check_colab_downloads():
            build_gallery_html(OUTPUTS_DIR)
            prev_state = get_state(OUTPUTS_DIR)
            continue

        # 2. 檢查 outputs 本地目錄變更
        curr_state = get_state(OUTPUTS_DIR)
        if curr_state != prev_state:
            print("[Watcher] 偵測到 outputs 資料夾變更，正在自動更新 gallery_index.html...")
            try:
                build_gallery_html(OUTPUTS_DIR)
                print("[Watcher] gallery_index.html 已自動更新完畢！")
            except Exception as e:
                print(f"[Watcher] 更新錯誤: {e}")
            prev_state = curr_state

if __name__ == "__main__":
    main()
