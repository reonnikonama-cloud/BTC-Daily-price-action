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
    """30分スナップショット処理（日付跨ぎの始値自動セット＆00:00ログ出力対応）"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    saved_data = load_saved_data()
    is_new_day = (saved_data.get("date") != today_str)

    # 00:00（新しい日付の最初のリクエスト）の場合、データ収集開始ログを出力
    if is_new_day:
        send_debug_log(f"🌅 [{today_str} {time_str}] 新しい日付を検知しました。00:00 データ収集および始値セット処理を開始します。")

    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log(f"⚠️ [{today_str} {time_str}] エラー: スナップショット用データの取得に失敗しました。")
        return

    # 1. 30分スナップショットログを追記
    record_30min_snapshot(current_data, time_str)

    # 2. 【日付跨ぎ判定】保存データの日付が「今日」でなければ、自動的に始値を更新して保存
    if is_new_day:
        current_prices = {pair: data["last"] for pair, data in current_data.items()}
        save_data({"date": today_str, "open_prices": current_prices})
        send_debug_log(f"✅ [{today_str} {time_str}] 当日の始値データセットおよび 00:00 スナップショットの記録が完了しました。")

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
