import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from src.config import COINCHECK_PAIRS

def fetch_coincheck_full_data():
    """全27銘柄のTickerおよびOrderBook情報を取得"""
    market_data = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    for pair in COINCHECK_PAIRS:
        symbol = pair.split('_')[0].upper()
        ticker_url = f"https://coincheck.com/api/ticker?pair={pair}"
        ob_url = f"https://coincheck.com/api/order_books?pair={pair}"
        
        try:
            # 1. Ticker 取得
            req_t = Request(ticker_url, headers=headers)
            with urlopen(req_t, timeout=10) as res:
                t_json = json.loads(res.read().decode('utf-8'))
                last_price = float(t_json.get('last', 0))
                high = float(t_json.get('high', 0))
                low = float(t_json.get('low', 0))
                volume = float(t_json.get('volume', 0))

            # 2. OrderBook (板情報) 取得
            req_ob = Request(ob_url, headers=headers)
            with urlopen(req_ob, timeout=10) as res:
                ob_json = json.loads(res.read().decode('utf-8'))
                bids = ob_json.get("bids", [])[:10]
                asks = ob_json.get("asks", [])[:10]

                total_bid_vol = sum(float(b[1]) for b in bids)
                total_ask_vol = sum(float(a[1]) for a in asks)
                total_vol = total_bid_vol + total_ask_vol

                bid_ratio = (total_bid_vol / total_vol * 100) if total_vol > 0 else 50.0

            market_data[pair] = {
                "symbol": symbol,
                "last": last_price,
                "high": high,
                "low": low,
                "volume": volume,
                "bid_ratio": bid_ratio
            }

        except (HTTPError, URLError, TimeoutError, ValueError) as e:
            print(f"[{pair}] API取得失敗（スキップします）: {e}")

        time.sleep(0.12)  # Rate Limit 回避

    return market_data
