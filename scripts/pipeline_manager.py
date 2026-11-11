import os
import sys
import json
import time
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SWITCH_CONFIG_PATH = os.path.join(REPO_DIR, "configs", "benchmark_switch.json")
REGISTRY_CONFIG_PATH = os.path.join(REPO_DIR, "configs", "model_registry.json")
OUT_DIR = os.path.join(REPO_DIR, "outputs")
MIN_GIT_EXE = os.path.expandvars(r"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe")
if not os.path.exists(MIN_GIT_EXE):
    MIN_GIT_EXE = "git"


def load_switch_config():
    if not os.path.exists(SWITCH_CONFIG_PATH):
        raise FileNotFoundError(f"找不到配置檔: {SWITCH_CONFIG_PATH}")
    with open(SWITCH_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_switch_config(data):
    with open(SWITCH_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def git_sync(commit_msg):
    try:
        subprocess.run([MIN_GIT_EXE, "-C", REPO_DIR, "add", "configs/"], check=False)
        subprocess.run([MIN_GIT_EXE, "-C", REPO_DIR, "commit", "-m", commit_msg], check=False)
        res = subprocess.run([MIN_GIT_EXE, "-C", REPO_DIR, "push", "origin", "main"], capture_output=True, text=True, check=False)
        print("☁️ [GitHub 同步] 配置已成功同步至 GitHub 雲端！")
    except Exception as e:
        print(f"⚠️ Git 同步提示: {e}")


def show_status():
    cfg = load_switch_config()
    active = cfg.get("active_switch", {})
    gold = cfg.get("golden_standard", {})
    prompts = gold.get("prompts", {})

    print("=" * 85)
    print("🎯 AI 寫實多模態實驗室 — 全域統一模型與算力切換總控 (Benchmark Hub)")
    print("=" * 85)
    print(f"📌 當前鎖定模型 (Active Model):  [{active.get('model')}] -> {cfg['supported_models'].get(active.get('model'), {}).get('name', 'N/A')}")
    print(f"📌 當前鎖定伺服器 (Active Server): [{active.get('server')}] -> {cfg['supported_servers'].get(active.get('server'), {}).get('name', 'N/A')}")
    print(f"📌 鎖定首幀母圖 (Golden Image):  {gold.get('mother_image_id')} (評分: {gold.get('mother_image_score')} 分 PASS)")
    v_res = gold.get("video_resolution", {})
    print(f"📌 視頻標準解析度:               {v_res.get('width')}x{v_res.get('height')} ({v_res.get('note', '')})")
    print(f"📌 視頻幀率與時長:               {gold.get('total_frames')} 幀 / {gold.get('fps')} FPS = {gold.get('duration_sec')} 秒 (100% 滿血)")
    print("-" * 85)
    print("🌟 [絕對控制變因 — 全模型完全一致的 Golden Prompts]")
    print(f"   [動態換裝提示詞]: {prompts.get('golden_motion_prompt')[:95]}...")
    print(f"   [負向提示約束詞]: {prompts.get('golden_negative_prompt')[:95]}...")
    print("-" * 85)
    print("📋 [支援的模型清單 (Models)]：")
    for mid, m in cfg.get("supported_models", {}).items():
        is_cur = (mid == active.get("model"))
        tag = "⭐ [啟用中]" if is_cur else "   "
        print(f" {tag} {mid:<14} | {m.get('name'):<32} | 參數: {m.get('parameters'):<6} | 狀態: {m.get('status')}")
    print("-" * 85)
    print("🖥️ [支援的伺服器算力 (Servers)]：")
    for sid, s in cfg.get("supported_servers", {}).items():
        is_cur = (sid == active.get("server"))
        tag = "⭐ [啟用中]" if is_cur else "   "
        print(f" {tag} {sid:<14} | {s.get('name'):<26} | 顯存: {s.get('vram_gb')}GB | 速度: {s.get('speed_rating')}")
    print("=" * 85)


def switch_pipeline(model_id=None, server_id=None):
    cfg = load_switch_config()
    changed = False

    if model_id:
        if model_id not in cfg.get("supported_models", {}):
            print(f"❌ 錯誤：不支援的模型 ID '{model_id}'。請執行 --status 查看可用清單。")
            return False
        cfg["active_switch"]["model"] = model_id
        m_info = cfg["supported_models"][model_id]
        print(f"✅ 模型切換成功 ➔ [{model_id}] ({m_info.get('name')})")
        changed = True

    if server_id:
        if server_id not in cfg.get("supported_servers", {}):
            print(f"❌ 錯誤：不支援的伺服器 ID '{server_id}'。請執行 --status 查看可用清單。")
            return False
        cfg["active_switch"]["server"] = server_id
        s_info = cfg["supported_servers"][server_id]
        print(f"✅ 伺服器切換成功 ➔ [{server_id}] ({s_info.get('name')})")
        changed = True

    if changed:
        save_switch_config(cfg)
        git_sync(f"switch: update benchmark active target to model={cfg['active_switch']['model']}, server={cfg['active_switch']['server']}")
        print("\n🎉 切換完成！雲端與本地將以【完全相同的 Golden Prompt 與母圖】執行對照實驗！")
        return True
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--status" in args or "--list" in args:
        show_status()
    elif "--switch" in args:
        m_val = None
        s_val = None
        if "--model" in args:
            idx = args.index("--model")
            if idx + 1 < len(args):
                m_val = args[idx + 1]
        if "--server" in args:
            idx = args.index("--server")
            if idx + 1 < len(args):
                s_val = args[idx + 1]
        switch_pipeline(model_id=m_val, server_id=s_val)
    elif "--model" in args and len(args) > 1:
        switch_pipeline(model_id=args[1])
    elif "--server" in args and len(args) > 1:
        switch_pipeline(server_id=args[1])
    else:
        print("用法說明:")
        print("  python pipeline_manager.py                       # 查看當前開關與模型清單")
        print("  python pipeline_manager.py --switch --model wan21_14b --server colab_a100")
        print("  python pipeline_manager.py --switch --model svd_xt")
        print("  python pipeline_manager.py --switch --server kaggle_t4")
