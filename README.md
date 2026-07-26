# 📈 Coincheck Market Monitor & Analytics Bot

Coincheckで取り扱われている全27銘柄の暗号資産データを自動で監視・蓄積・分析し、Discordへ日次レポート、アナリティクス、およびランキングを自動投稿する完全自動化システムです。

---

## ✨ 主な機能

1. **📊 全27銘柄 日次市況レポートカード (`DISCORD_WEBHOOK_DAILY_REPORT`)**
   * 毎夜 23:55 JST に、全27銘柄の価格・始値比較（騰落率 %）・24H高値/安値・出来高・気配値（Bid/Ask）板圧力を Discord Embed カード形式で分割送信します。
2. **⚡ 本日の激動時間帯アナリティクス (`DISCORD_WEBHOOK_ANALYTICS`)**
   * 毎夜 23:55 JST に、1日48回（30分間隔）蓄積されたログから **「本日最も値動きが激しかった30分枠（ピークボラティリティ時間）」** を自動解析して発表します。
3. **🏆 独立 騰落率ランキング (`DISCORD_WEBHOOK_RANKING`)**
   * 毎夜 23:50 JST に、本日の **値上がり TOP3 (Gainers)**、**値下がり TOP3 (Losers)**、および上位銘柄のモメンタム一覧を独立ワークフローから専用チャンネルへ送信します。
4. **🛠️ 自動クリーンアップ ＆ エコ運用**
   * 解析・レポート送信完了後、一時保持していた 30分間ログ（`data/history.json`）を即座に一括削除。リポジトリの容量増加を防ぎ、数MB以下の軽量状態を永久維持します。
5. **🚨 システムログ・デバッグ通知 (`DISCORD_WEBHOOK_DEBUG_LOG`)**
   * APIエラーやGitHub Actions実行時のステータス、ログ消去完了通知などを独立したログチャンネルへ飛ばし、サイレント落ちを防ぎます。

---

## 📂 ディレクトリ構造

```text
.
├── .github/
│   └── workflows/
│       ├── snapshot.yml          # 30分毎のデータ取得・一時ログ保存用
│       ├── ranking.yml           # 【23:50 JST】独立 騰落率ランキング発表用
│       └── daily_report.yml      # 【23:55 JST】日次レポート・解析・削除用
├── data/
│   ├── price_data.json           # 始値記録用（永続保持・軽量JSON）
│   └── history.json              # 30分スナップショット一時保存用（23:55に自動削除）
├── src/
│   ├── config.py                 # 定数・銘柄リスト・環境変数定義
│   ├── collectors/
│   │   └── coincheck.py          # APIデータ取得（エラー＆Rate Limit対策済）
│   ├── history.py                # 30分スナップショット追記 ＆ 自動クリーンアップ
│   ├── analyzer.py               # 激動時間帯（ピークボラティリティ）解析
│   ├── ranking.py                # 独立 騰落率ランキング算出 ＆ Embed生成
│   ├── storage.py                # 始値データ読み書きモジュール
│   └── discord.py                # Discord Webhook 送信処理 ＆ デバッグログ送信
├── main.py                       # CLIエントリーポイント (--snapshot / --ranking / --report)
└── README.md
