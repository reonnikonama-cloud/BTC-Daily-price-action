import argparse
from datetime import datetime
from src.config import JST
from src.collectors.coincheck import fetch_coincheck_full_data
from src.history import record_30min_snapshot, cleanup_history_file
from src.analyzer import analyze_volatile_timeframes
from src.ranking import process_and_send_ranking
from src.discord import send_daily_report_cards, send_analytics_report, send_debug_log
from src.storage import load_saved_data, save_data

def handle_snapshot():
    """30分スナップショット処理（日中の始値上書き防衛ロジック追加版）"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    saved_data = load_saved_data()
    saved_date = saved_data.get("date")

    # 【防衛ロジック】GitHub ActionsのCron遅延を考慮し「0時台 (00:00〜00:59)」を真の00:00跨ぎと判定
    is_true_midnight = (saved_date != today_str) and (now.hour == 0)

    if is_true_midnight:
        send_debug_log(f"🌅 [{today_str} {time_str}] 新しい日付を検知しました。00:00 データ収集および始値セット処理を開始します。")

    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log(f"⚠️ [{today_str} {time_str}] エラー: スナップショット用データの取得に失敗しました。")
        return

    # 1. 30分スナップショットログを追記
    record_30min_snapshot(current_data, time_str)

    # 2. 深夜 00:00 時台のみ始値（open_prices）をセットして保存
    if is_true_midnight:
        current_prices = {pair: data["last"] for pair, data in current_data.items()}
        save_data({"date": today_str, "open_prices": current_prices})
        send_debug_log(f"✅ [{today_str} {time_str}] 当日の始値データセットおよび 00:00 スナップショットの記録が完了しました。")
    elif saved_date != today_str:
        # 日中に初回起動・リカバリ等で日付がズレていた場合、始値を上書きせずに日付のみ補正
        saved_data["date"] = today_str
        save_data(saved_data)

def handle_ranking():
    """23:50 (JST) 独立騰落率ランキング送信"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    send_debug_log(f"🚀 [{today_str} {time_str}] 騰落率ランキング処理を開始しました。")

    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log(f"🚨 [{today_str} {time_str}] エラー: ランキング用データの取得に失敗しました。")
        return
    
    saved_data = load_saved_data()
    open_prices = saved_data.get("open_prices", {})
    
    process_and_send_ranking(current_data, open_prices, today_str)
    send_debug_log(f"✅ [{today_str} {time_str}] 騰落率ランキングの送信が正常に完了しました。")

def handle_report():
    """23:55 (JST) 日次レポート・激動時間帯解析送信および一括削除"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    send_debug_log(f"🚀 [{today_str} {time_str}] 23:55 日次締め処理（レポート・解析・ログ削除）を開始しました。")

    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log(f"🚨 [{today_str} {time_str}] エラー: 日次レポート用データの取得に失敗しました。")
        return

    current_prices = {pair: data["last"] for pair, data in current_data.items()}
    saved_data = load_saved_data()
    open_prices = saved_data.get("open_prices", {})

    # 1. 市況カード送信
    send_daily_report_cards(current_data, open_prices, today_str)

    # 2. 激動時間帯解析送信
    analytics_data = analyze_volatile_timeframes()
    if analytics_data:
        send_analytics_report(analytics_data, today_str)
    else:
        send_debug_log(f"⚠️ [{today_str} {time_str}] 激動時間帯解析データが空のため、アナリティクス送信をスキップしました。")

    # 3. 翌日用始値データ更新保存 ＆ 一時ログ削除
    save_data({"date": today_str, "open_prices": current_prices})
    cleanup_history_file()
    send_debug_log(f"🎉 [{today_str} {time_str}] 全レポートの送信、翌日用データ保存、およびログクリーンアップが正常に完了しました。")

def main():
    parser = argparse.ArgumentParser(description="Crypto Market Monitor CLI")
    parser.add_argument("--snapshot", action="store_true", help="30分スナップショット取得")
    parser.add_argument("--ranking", action="store_true", help="独立騰落率ランキング送信")
    parser.add_argument("--report", action="store_true", help="日次レポート・解析送信およびログ削除")
    args = parser.parse_args()

    if args.snapshot:
        handle_snapshot()
    elif args.ranking:
        handle_ranking()
    elif args.report:
        handle_report()

if __name__ == "__main__":
    main()
