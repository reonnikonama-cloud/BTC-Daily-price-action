import os
from datetime import timezone, timedelta

# 厳格な日本時間 (JST) 定義
JST = timezone(timedelta(hours=9), 'JST')

# Discord Webhook URLs (GitHub Secrets より取得)
DISCORD_WEBHOOK_DAILY_REPORT = os.getenv("DISCORD_WEBHOOK_DAILY_REPORT")
DISCORD_WEBHOOK_ANALYTICS = os.getenv("DISCORD_WEBHOOK_ANALYTICS")
DISCORD_WEBHOOK_RANKING = os.getenv("DISCORD_WEBHOOK_RANKING")
DISCORD_WEBHOOK_DEBUG_LOG = os.getenv("DISCORD_WEBHOOK_DEBUG_LOG")

# Coincheck 全27銘柄
COINCHECK_PAIRS = [
    "btc_jpy", "eth_jpy", "etc_jpy", "lsk_jpy", "xrp_jpy", "xem_jpy", "ltc_jpy",
    "bch_jpy", "mona_jpy", "xlm_jpy", "qtum_jpy", "bat_jpy", "iost_jpy", "enj_jpy",
    "omg_jpy", "plt_jpy", "sand_jpy", "dot_jpy", "fnct_jpy", "chz_jpy", "link_jpy",
    "dai_jpy", "maker_jpy", "avax_jpy", "shib_jpy", "ape_jpy", "wbtc_jpy"
]
