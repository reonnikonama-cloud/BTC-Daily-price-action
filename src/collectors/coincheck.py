import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from src.config import COINCHECK_PAIRS

def fetch_coincheck_full_data():
    """全銘柄の最新価格およびTicker/OrderBook情報を安全に取得"""
    market_data = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # 1. 全銘柄の現在レートを一括取得（404エラー防止のベースデータ）
    all_rates = {}
    try:
        req_rates = Request("https://coincheck.com/api/rate/all", headers=headers)
        with urlopen(req_rates, timeout=10) as res:
            all_rates = json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"全レート一括取得失敗: {e}")

    for pair in COINCHECK_PAIRS:
        symbol = pair.split('_')[0].upper()
        ticker_url = f"https://coincheck.com/api/ticker?pair={pair}"
        ob_url = f"https://coincheck.com/api/order_books?pair={pair}"
        
        # /api/rate/all から初期値（現在価格）を取得。取れなければ 0.0
        last_price = float(all_rates.get(pair, 0.0))
        high = 0.0
        low = 0.0
        volume = 0.0
        bid_ratio = 50.0

        # 2. Ticker 取得（/api/ticker が 404 を返しても rate/all の価格でカバー）
        try:
            req_t = Request(ticker_url, headers=headers)
            with urlopen(req_t, timeout=5) as res:
                t_json = json.loads(res.read().decode('utf-8'))
                last_price = float(t_json.get('last', last_price))
                high = float(t_json.get('high', 0))
                low = float(t_json.get('low', 0))
                volume = float(t_json.get('volume', 0))
        except HTTPError as e:
            if e.code == 404:
                pass # Ticker未対応銘柄は /api/rate/all の価格を採用するため無視
            else:
                print(f"[{pair}] Ticker取得エラー ({e.code})")
        except Exception as e:
            print(f"[{pair}] Ticker取得失敗: {e}")

        time.sleep(0.05)

        # 3. OrderBook (板情報) 取得
        try:
            req_ob = Request(ob_url, headers=headers)
            with urlopen(req_ob, timeout=5) as res:
                ob_json = json.loads(res.read().decode('utf-8'))
                bids = ob_json.get("bids", [])[:10]
                asks = ob_json.get("asks", [])[:10]

                total_bid_vol = sum(float(b[1]) for b in bids)
                total_ask_vol = sum(float(a[1]) for a in asks)
                total_vol = total_bid_vol + total_ask_vol

                if total_vol > 0:
                    bid_ratio = (total_bid_vol / total_vol) * 100
        except Exception as e:
            pass # 板情報が取れなくても継続

        # 最低限価格が取得できている場合のみデータに追加
        if last_price > 0:
            market_data[pair] = {
                "symbol": symbol,
                "last": last_price,
                "high": high,
                "low": low,
                "volume": volume,
                "bid_ratio": bid_ratio
            }

        time.sleep(0.05)

    print(f"取得成功銘柄数: {len(market_data)} / {len(COINCHECK_PAIRS)}")
    return market_data
