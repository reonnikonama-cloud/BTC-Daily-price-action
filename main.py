import json
import os
import time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# --------------------------------------------------
# 環境変数の取得（GitHub Secrets）
# --------------------------------------------------
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not DISCORD_WEBHOOK_URL:
    raise ValueError("エラー: DISCORD_WEBHOOK_URL が設定されていません。")

DATA_FILE = "price_data.json"
JST = timezone(timedelta(hours=9), 'JST')

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
        time.sleep(0.2)
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

def send_discord_webhook(current_prices, open_prices, date_str):
    all_fields = []

    for pair in PAIRS:
        curr = current_prices.get(pair)       # 終値 (23:55時点)
        open_val = open_prices.get(pair)      # 始値 (00:00時点)
        symbol = pair.split('_')[0].upper()
        
        if curr is None:
            continue

        if open_val and open_val > 0:
            diff = curr - open_val
            change_pct = (diff / open_val) * 100
            
            # 暴騰・暴落判定（5%以上の変動で強調表示）
            if change_pct >= 5.0:
                icon = "🚀"  # 暴騰
            elif change_pct > 0:
                icon = "🟢"  # 上昇
            elif change_pct <= -5.0:
                icon = "💥"  # 暴落
            elif change_pct < 0:
                icon = "🔴"  # 下降
            else:
                icon = "⚪"  # 変化なし

            sign = "+" if diff > 0 else ""
            text = f"{icon} {sign}¥{diff:,.2f}\n({sign}{change_pct:.2f}%)"
            value_str = f"**¥{curr:,.2f}**\n{text}"
        else:
            value_str = f"**¥{curr:,.2f}**\n⚪ 始値データなし"

        all_fields.append({
            "name": symbol,
            "value": value_str,
            "inline": True
        })

    # Discord Embed（25個制限対策）
    chunk_size = 25
    embeds = []
    
    for i in range(0, len(all_fields), chunk_size):
        fields_chunk = all_fields[i:i + chunk_size]
        embed_title = f"📊 Coincheck 日次騰落率レポート ({date_str})" if i == 0 else ""
        
        embed = {
            "color": 3447003,
            "fields": fields_chunk
        }
        if embed_title:
            embed["title"] = embed_title
        if i + chunk_size >= len(all_fields):
            embed["footer"] = {"text": "Coincheck API Status"}
            
        embeds.append(embed)

    payload = {"embeds": embeds}

    req = Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
        method='POST'
    )
    
    try:
        with urlopen(req) as res:
            print("Discordへ通知を送信しました。")
    except HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Discord送信エラー: HTTP Error {e.code}: {e.reason}\n詳細: {error_body}")
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
    open_prices = saved_data.get("open_prices", {})

    # 日付が変わっている、または始値データがない場合は始値保存処理
    if last_updated_date != today_str or not open_prices:
        print(f"日付初回の実行を検知 ({today_str})。現在の価格を始値 (Open) として保存します。")
        saved_data = {
            "date": today_str,
            "open_prices": current_prices
        }
        save_data(saved_data)
        
        # 始値データを保存した段階では通知を送らずに終了（2重送信防止）
        print("始値データの記録が完了しました。Discord通知はスキップします。")
        return

    # 2回目以降の実行（23:55の終値取得時）：保存されている始値と終値を比較してDiscord通知
    print("終値を取得。始値と比較してDiscordへ通知を送信します。")
    send_discord_webhook(current_prices, open_prices, today_str)

if __name__ == "__main__":
    main()
