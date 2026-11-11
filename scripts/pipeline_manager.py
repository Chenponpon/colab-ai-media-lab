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
CONFIG_PATH = os.path.join(REPO_DIR, "configs", "model_registry.json")
OUT_DIR = os.path.join(REPO_DIR, "outputs")
sys.path.insert(0, os.path.dirname(__file__))

from prompt_randomizer import build_gallery_html
from svd_video_runner import build_svd_worker_notebook, push_and_run_svd_video, monitor_and_download_svd
from wan_video_runner import build_wan21_worker_notebook, push_and_run_wan21_video, monitor_and_download_wan21
from qwen_auto_runner import push_and_run_qwen_gpu
from kaggle_auto_runner import push_and_run_headless_gpu


def load_registry():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"找不到配置檔: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_pipelines():
    reg = load_registry()
    print("=" * 80)
    print("🎯 AI 寫實人像與換裝動態 — 集中式模型管線切換中心 (Model Pipeline Hub)")
    print("=" * 80)
    print(f"🎬 當前啟用影片管線: [{reg.get('active_video_pipeline')}]")
    print(f"🖼️ 當前啟用生圖管線: [{reg.get('active_image_pipeline')}]")
    print("-" * 80)
    for pid, p in reg.get("pipelines", {}).items():
        is_active = (pid == reg.get("active_video_pipeline") or pid == reg.get("active_image_pipeline"))
        tag = "⭐ [當前啟用]" if is_active else "  "
        print(f"{tag} ID: {pid}")
        print(f"     名稱: {p.get('name')} ({p.get('type').upper()})")
        print(f"     預估耗時: {p.get('inference_time_est')} | 顯存需求: {p.get('vram_gb_required')} GB | 狀態: {p.get('status')}")
        print(f"     機制特點: {p.get('strengths')}")
        print("-" * 80)


def set_active_pipeline(pipe_id):
    reg = load_registry()
    if pipe_id not in reg.get("pipelines", {}):
        print(f"❌ 錯誤: 找不到管線 ID '{pipe_id}'。請執行 --list 查看可用管線。")
        return False
    ptype = reg["pipelines"][pipe_id].get("type")
    if ptype == "video":
        reg["active_video_pipeline"] = pipe_id
        print(f"✅ 已成功切換啟用影片管線為: {pipe_id} ({reg['pipelines'][pipe_id]['name']})")
    else:
        reg["active_image_pipeline"] = pipe_id
        print(f"✅ 已成功切換啟用生圖管線為: {pipe_id} ({reg['pipelines'][pipe_id]['name']})")
    save_registry(reg)
    return True


def deploy_active_video():
    reg = load_registry()
    active_id = reg.get("active_video_pipeline", "video_svd_xt_5s")
    print(f"🚀 正在準備發射當前啟用影片管線: [{active_id}] ...")
    if active_id == "video_svd_xt_5s":
        push_and_run_svd_video()
    elif active_id == "video_wan21_14b_4bit":
        push_and_run_wan21_video()
    else:
        print(f"❌ 未知或已棄用之影片管線: {active_id}")


def monitor_active_video():
    reg = load_registry()
    active_id = reg.get("active_video_pipeline", "video_svd_xt_5s")
    if active_id == "video_svd_xt_5s":
        monitor_and_download_svd()
    elif active_id == "video_wan21_14b_4bit":
        monitor_and_download_wan21()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--list":
            list_pipelines()
        elif cmd == "--switch" and len(sys.argv) > 2:
            set_active_pipeline(sys.argv[2])
        elif cmd == "--deploy-video":
            if len(sys.argv) > 2:
                set_active_pipeline(sys.argv[2])
            deploy_active_video()
        elif cmd == "--monitor":
            monitor_active_video()
        elif cmd == "--run":
            if len(sys.argv) > 2:
                set_active_pipeline(sys.argv[2])
            deploy_active_video()
            monitor_active_video()
        else:
            print("用法: python pipeline_manager.py [--list | --switch <id> | --deploy-video [id] | --monitor | --run [id]]")
    else:
        list_pipelines()
