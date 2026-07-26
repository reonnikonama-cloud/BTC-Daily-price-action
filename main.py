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
    """30分スナップショット処理（日付跨ぎの始値自動セット機能付き）"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log("エラー: スナップショット用データの取得に失敗しました。")
        return

    # 1. 30分スナップショットログを追記
    record_30min_snapshot(current_data, time_str)

    # 2. 【日付跨ぎ判定】保存データの日付が「今日」でなければ、自動的に始値を更新して保存
    saved_data = load_saved_data()
    if saved_data.get("date") != today_str:
        current_prices = {pair: data["last"] for pair, data in current_data.items()}
        save_data({"date": today_str, "open_prices": current_prices})
        send_debug_log(f"[{today_str} {time_str}] 新しい日付を検知したため、始値データを更新しました。")

def handle_ranking():
    """23:50 独立騰落率ランキング送信"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log("エラー: ランキング用データの取得に失敗しました。")
        return
    
    saved_data = load_saved_data()
    open_prices = saved_data.get("open_prices", {})
    
    process_and_send_ranking(current_data, open_prices, today_str)

def handle_report():
    """23:55 日次レポート・激動時間帯解析送信および一括削除"""
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")

    current_data = fetch_coincheck_full_data()
    if not current_data:
        send_debug_log("エラー: 日次レポート用データの取得に失敗しました。")
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

    # 3. 始値データ更新保存 ＆ 一時ログ削除
    save_data({"date": today_str, "open_prices": current_prices})
    cleanup_history_file()
    send_debug_log(f"[{today_str}] 全レポート送信およびログクリーンアップが完了しました。")

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
