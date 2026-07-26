import json
import os

HISTORY_FILE = "data/history.json"

def record_30min_snapshot(current_data, time_str):
    """30分ごとの現在値を一時ファイルに追記"""
    os.makedirs("data", exist_ok=True)
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}

    history[time_str] = {pair: data["last"] for pair, data in current_data.items()}

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"[{time_str}] 30分スナップショットを記録しました。")

def cleanup_history_file():
    """分析終了後、一時ログファイルを完全削除（リポジトリ容量節約）"""
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
            print("本日の履歴データ (data/history.json) を一括削除・クリーンアップしました。")
        except Exception as e:
            print(f"履歴ファイル削除エラー: {e}")
