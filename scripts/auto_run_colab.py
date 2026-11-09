import os
import sys
import json
import time
import subprocess
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JOB_FILE = os.path.join(REPO_DIR, "queue", "current_job.json")
OUT_DIR = os.path.join(REPO_DIR, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

COLAB_WORKER_URL = "https://colab.research.google.com/github/Chenponpon/colab-ai-media-lab/blob/main/notebooks/auto_worker.ipynb"

def push_latest_job():
    print("🔄 [本機端] 正在將最新任務設定推送至 GitHub...")
    env = os.environ.copy()
    min_git = os.path.expandvars(r"%LOCALAPPDATA%\Programs\MinGit\cmd")
    git_exe = os.path.join(min_git, "git.exe")
    gh_cli = r"C:\Program Files\GitHub CLI"
    env["Path"] = f"{env.get('Path', '')};{min_git};{gh_cli}"
    subprocess.run([git_exe, "add", "."], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "commit", "-m", "Update automated Colab job config"], cwd=REPO_DIR, env=env, check=False)
    subprocess.run([git_exe, "push"], cwd=REPO_DIR, env=env, check=False)
    print("✅ [本機端] GitHub 任務同步完成！")

def launch_browser_and_trigger_run():
    print(f"🌐 [本機端] 正在為你開啟 Colab 自動工作站網頁:\n   {COLAB_WORKER_URL}")
    subprocess.run(["powershell", "-Command", f'Start-Process "{COLAB_WORKER_URL}"'], check=False)
    print("⏳ 等待 12 秒讓 Colab 網頁載入，將自動發送 Ctrl+F9 (全部執行)...")
    time.sleep(12)
    ps_keys = (
        "$wshell = New-Object -ComObject wscript.shell; "
        "$wshell.SendKeys('^{F9}'); "
        "Start-Sleep -Seconds 2; "
        "$wshell.SendKeys('{TAB}{ENTER}')"
    )
    subprocess.run(["powershell", "-Command", ps_keys], check=False)
    print("⚡ 已自動向瀏覽器發送 Ctrl+F9 啟動訊號！(若瀏覽器詢問『仍要執行/Run anyway』，已自動嘗試確認，或請點一下確認)")

def download_file(url, dest_path):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Colab-Client/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as out:
                out.write(resp.read())
            return True
        except Exception as e:
            print(f"⚠️ 下載重試中 ({attempt+1}/5): {e}")
            time.sleep(3)
    return False

def send_ack(tunnel_url):
    if not tunnel_url:
        return
    try:
        req = urllib.request.Request(f"{tunnel_url}/ack", data=b"ACK", method="POST")
        urllib.request.urlopen(req, timeout=10)
        print("✅ [本機端] 已發送下載完成確認 (ACK)，Colab 即將自動切斷 A100 電源！")
    except Exception as e:
        print(f"⚠️ ACK 發送警告 (Colab 仍會在逾時後自動關機): {e}")

def listen_for_colab_events(ntfy_topic):
    stream_url = f"https://ntfy.sh/{ntfy_topic}/json"
    print(f"📡 [本機端] 正在監聽 Colab 雲端回傳通道 ({ntfy_topic})...")
    downloaded_files = []
    tunnel_url = None

    req = urllib.request.Request(stream_url, headers={"User-Agent": "Antigravity-Colab-Listener/1.0"})
    with urllib.request.urlopen(req, timeout=3600) as resp:
        for raw_line in resp:
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                outer = json.loads(line)
                if outer.get("event") != "message":
                    continue
                payload = json.loads(outer.get("message", "{}"))
            except Exception:
                continue

            ev = payload.get("event")
            msg = payload.get("message", "")
            if payload.get("tunnel_url"):
                tunnel_url = payload["tunnel_url"]

            if ev == "WORKER_ONLINE":
                print(f"\n🔥 [雲端連線成功] {msg}")
                print(f"🔗 專屬加密傳輸通道: {tunnel_url}")
            elif ev == "STATUS":
                print(f"⏳ [雲端進度] {msg}")
            elif ev == "FILE_READY":
                fname = payload.get("filename")
                furl = payload.get("url")
                dest = os.path.join(OUT_DIR, fname)
                print(f"⬇️ [自動下載中] {msg} -> {dest}")
                if download_file(furl, dest):
                    print(f"🎉 [下載成功] 檔案已儲存至本機: {dest}")
                    downloaded_files.append(dest)
            elif ev == "JOB_COMPLETED":
                print(f"\n🏁 [任務完成] {msg}")
                send_ack(tunnel_url)
            elif ev == "SHUTDOWN":
                print(f"🛑 [自動省額度關機] {msg}")
                print("\n==========================================")
                print("✨ 本次全自動產圖與產影片已全部儲存至本機：")
                for f in downloaded_files:
                    print(f"   📁 {f}")
                print("==========================================")
                return downloaded_files

if __name__ == "__main__":
    with open(JOB_FILE, "r", encoding="utf-8") as f:
        job = json.load(f)
    push_latest_job()
    launch_browser_and_trigger_run()
    listen_for_colab_events(job["ntfy_topic"])
