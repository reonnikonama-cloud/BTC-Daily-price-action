import json
import os
import time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# --------------------------------------------------
# 環境変数の取得（GitHub Secrets から注入される）
# --------------------------------------------------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("エラー: DISCORD_WEBHOOK_URL が設定されていません。GitHub Secrets を確認してください。")

DATA_FILE = "price_data.json"
JST = timezone(timedelta(hours=9), 'JST')

# Coincheck JPYペア一覧
PAIRS = [
    "btc_jpy", "eth_jpy", "etc_jpy", "lsk_jpy", "xrp_jpy", "xem_jpy", 
    "bch_jpy", "mona_jpy", "iost_jpy", "chz_jpy", "imx_jpy", "shib_jpy", 
    "avax_jpy", "fnct_jpy", "dai_jpy", "wbtc_jpy", "bril_jpy", "bc_jpy", 
    "doge_jpy", "pepe_jpy", "mask_jpy", "mana_jpy", "grt_jpy", "trx_jpy", 
    "sol_jpy", "fpl_jpy", "sui_jpy"
]

def fetch_all_tickers():
    prices = {}
    for pair in PAIRS:
        url = f"https://coincheck.com/api/ticker?pair={pair}"
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                prices[pair] = float(data.get('last', 0))
        except (URLError, HTTPError, ValueError) as e:
            print(f"[{pair}] 価格取得エラー: {e}")
        time.sleep(0.2)  # APIレートリミット対策
    return prices

def load_saved_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_discord_webhook(current_prices, base_prices, date_str):
    fields = []
    
    # ANSIカラーコードのエスケープシーケンス
    # 32m: 緑色 / 31m: 赤色 / 0m: リセット
    ESC = "\u001b"
    GREEN = f"{ESC}[32m"
    RED = f"{ESC}[31m"
    RESET = f"{ESC}[0m"

    for pair in PAIRS:
        curr = current_prices.get(pair)
        base = base_prices.get(pair) if base_prices else None
        symbol = pair.split('_')[0].upper()
        
        if curr is None:
            continue

        if base and base > 0:
            diff = curr - base
            change_pct = (diff / base) * 100
            
            if diff >= 0:
                # プラス：緑色 ➕〇〇円 (+◯◯%)
                text = f"➕{diff:,.2f}円 (+{change_pct:.2f}%)"
                color_code = GREEN
            else:
                # マイナス：赤色 ➖〇〇円 (-◯◯%)（absで符号重複を防止）
                text = f"➖{abs(diff):,.2f}円 ({change_pct:.2f}%)"
                color_code = RED

            # ANSI装飾付きコードブロックで出力
            value_str = f"現在値: ¥{curr:,.2f}\n```ansi\n{color_code}{text}{RESET}\n```"
        else:
            value_str = f"現在値: ¥{curr:,.2f}\n```\n--- データなし ---\n```"

        fields.append({
            "name": symbol,
            "value": value_str,
            "inline": True
        })

    payload = {
        "embeds": [{
            "title": f"📊 Coincheck 前日比レポート ({date_str})",
            "color": 3447003,
            "fields": fields,
            "footer": {"text": "Coincheck API Status"}
        }]
    }

    req = Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        method='POST'
    )
    
    try:
        with urlopen(req) as res:
            print("Discordへ通知を送信しました。")
    except Exception as e:
        print(f"Discord送信エラー: {e}")

def main():
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    print(f"--- 処理開始 [{now.strftime('%Y-%m-%d %H:%M:%S')}] ---")

    current_prices = fetch_all_tickers()
    if not current_prices:
        print("価格データが取得できませんでした。")
        return

    saved_data = load_saved_data()
    last_updated_date = saved_data.get("date")
    base_prices = saved_data.get("prices", {})

    if last_updated_date != today_str:
        print(f"新しい日付を検知しました ({today_str})。基準価格を更新します。")
        saved_data = {
            "date": today_str,
            "prices": current_prices
        }
        save_data(saved_data)
        if not base_prices:
            base_prices = current_prices

    send_discord_webhook(current_prices, base_prices, today_str)

if __name__ == "__main__":
    main()
