from src.config import DISCORD_WEBHOOK_RANKING
from src.discord import send_embed_to_discord

def process_and_send_ranking(current_data, open_prices, date_str):
    """独立コンポーネントとして全銘柄の騰落率ランキングを生成・送信"""
    rankings = []
    for pair, data in current_data.items():
        symbol = data["symbol"]
        last_price = data["last"]
        open_price = open_prices.get(pair, 0.0)
        change_pct = ((last_price - open_price) / open_price * 100) if open_price > 0 else 0.0

        rankings.append({
            "symbol": symbol,
            "last": last_price,
            "change_pct": change_pct
        })

    rankings.sort(key=lambda x: x["change_pct"], reverse=True)

    top_gainers = rankings[:3]
    top_losers = sorted(rankings, key=lambda x: x["change_pct"])[:3]

    gainers_text = "".join([f"{['🥇','🥈','🥉'][i]} **{item['symbol']}**: +{item['change_pct']:.2f}% (¥{item['last']:,})\n" for i, item in enumerate(top_gainers)])
    losers_text = "".join([f"{['📉','🔻','⚠️'][i]} **{item['symbol']}**: {item['change_pct']:.2f}% (¥{item['last']:,})\n" for i, item in enumerate(top_losers)])
    summary_line = " > ".join([f"{r['symbol']}({r['change_pct']:+.1f}%)" for r in rankings[:5]])

    embed = {
        "title": f"🏆 本日の全銘柄 騰落率ランキング ({date_str})",
        "color": 0xF1C40F,  # ゴールド
        "fields": [
            {"name": "🚀 値上がり TOP 3 (Gainers)", "value": gainers_text or "該当なし", "inline": False},
            {"name": "💥 値下がり TOP 3 (Losers)", "value": losers_text or "該当なし", "inline": False},
            {"name": "📊 全体モメンタム (上位5銘柄)", "value": f"`{summary_line}`", "inline": False}
        ],
        "footer": {"text": "Coincheck Market Monitor • Standalone Ranking System"}
    }

    send_embed_to_discord(DISCORD_WEBHOOK_RANKING, [embed])
    print(f"[{date_str}] 独立騰落率ランキングの送信が完了しました。")
