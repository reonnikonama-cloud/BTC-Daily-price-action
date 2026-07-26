import json
import time  # ← time モジュールを追加
from urllib.request import Request, urlopen
from src.config import DISCORD_WEBHOOK_DAILY_REPORT, DISCORD_WEBHOOK_ANALYTICS, DISCORD_WEBHOOK_DEBUG_LOG

def send_embed_to_discord(webhook_url: str, embeds: list):
    """汎用 Webhook 送信関数"""
    if not webhook_url:
        print("[Warn] Webhook URLが設定されていません。")
        return

    payload = {"embeds": embeds}
    req = Request(
        webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        method='POST'
    )
    try:
        with urlopen(req, timeout=10) as res:
            pass
    except Exception as e:
        print(f"Discord送信エラー: {e}")

def send_debug_log(message: str):
    """システムステータス・エラーログをログ専用チャンネルへ送信"""
    if not DISCORD_WEBHOOK_DEBUG_LOG:
        print(f"[DEBUG LOG]: {message}")
        return

    payload = {"content": f"🛠 **[System Log]** {message}"}
    req = Request(
        DISCORD_WEBHOOK_DEBUG_LOG,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        method='POST'
    )
    try:
        with urlopen(req, timeout=5) as res:
            pass
    except Exception as e:
        print(f"デバッグログ送信失敗: {e}")

def send_daily_report_cards(current_data, open_prices, date_str):
    """日次市況カード（全27銘柄）の分割送信"""
    embeds = []
    for pair, data in current_data.items():
        symbol = data["symbol"]
        last = data["last"]
        open_p = open_prices.get(pair, 0.0)
        pct = ((last - open_p) / open_p * 100) if open_p > 0 else 0.0
        
        direction = "🟢 +" if pct >= 0 else "🔴 "
        card = {
            "title": f"{symbol} / JPY",
            "color": 0x2ECC71 if pct >= 0 else 0xE74C3C,
            "fields": [
                {"name": "現在値", "value": f"¥{last:,} ({direction}{pct:.2f}%)", "inline": True},
                {"name": "24H 高値/安値", "value": f"¥{data['high']:,} / ¥{data['low']:,}", "inline": True},
                {"name": "板圧力(Bid ratio)", "value": f"{data['bid_ratio']:.1f}% 買い優勢" if data['bid_ratio'] >= 50 else f"{100-data['bid_ratio']:.1f}% 売り優勢", "inline": False}
            ]
        }
        embeds.append(card)

    # 10件ずつ分割して送信 (Discord API制限回避のためウェイトを追加)
    for i in range(0, len(embeds), 10):
        chunk = embeds[i:i+10]
        send_embed_to_discord(DISCORD_WEBHOOK_DAILY_REPORT, chunk)
        time.sleep(1.5)  # ★Discordの連投制限回避のため1.5秒待機★

def send_analytics_report(analytics_data, date_str):
    """激動時間帯解析の発表"""
    fields = []
    for symbol, info in list(analytics_data.items())[:10]: # ハイライト10銘柄
        fields.append({
            "name": f"⚡ {symbol}",
            "value": f"ピーク時間帯: `{info['peak_slot']}`\n変動率: `{info['change_pct']:+.2f}%`",
            "inline": True
        })

    embed = [{
        "title": f"⚡ 本日の激動時間帯（ピークボラティリティ解析） ({date_str})",
        "color": 0x9B59B6,
        "fields": fields,
        "footer": {"text": "Coincheck Market Monitor • Peak Volatility Analytics"}
    }]
    send_embed_to_discord(DISCORD_WEBHOOK_ANALYTICS, embed)
