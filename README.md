# 📈 Coincheck Market Monitor

Coincheck の暗号資産（仮想通貨）市場データを自動収集し、日次レポート・騰落率ランキング・激動時間帯（ボラティリティ）解析を Discord チャンネルへ自動配信する GitHub Actions 監視システムです。

---

## 🚀 主な機能

* **30分スナップショット蓄積 & 0:00 始値自動更新**
  * 30分ごとに公開API（15銘柄）から現在価格・高値/安値・板圧力を取得して一時ログ化。
  * 日付の切り替わり（0:00）を自動検知し、当日の始値を自動セット。
* **日次市況レポート (23:55)**
  * 全15銘柄の現在値・24H高安・始値比(%)・板圧力を分かりやすい Embed カード形式で一括配信。
* **激動時間帯（ボラティリティ）解析 (23:55)**
  * 蓄積された30分スナップショットデータから、本日最も価格変動が激しかった時間帯を自動解析。
* **独立 騰落率ランキング (23:50)**
  * 値上がり TOP3 / 値下がり TOP3 / 主要銘柄モメンタムを専用チャンネルへ配信。
* **自動ログクリーンアップ**
  * 日次処理の終了時に、翌日へ向けたログの自動削除と次回用の始値保存を自動実行。

---

## 🛠️ システム構成 & Discord Webhook

通知目的に応じて Discord の Webhook を 4 系統に分離して配信しています。

| GitHub Actions Secrets | 送信先チャンネル例 | 配信タイミング (JST) | 内容 |
| :--- | :--- | :--- | :--- |
| `DISCORD_WEBHOOK_DAILY_REPORT` | `#日次市況レポート` | **23:55** | 全15銘柄の個別市況カード |
| `DISCORD_WEBHOOK_ANALYTICS` | `#激動時間帯アナリティクス` | **23:55** | 本日のピークボラティリティ解析結果 |
| `DISCORD_WEBHOOK_RANKING` | `#騰落率ランキング` | **23:50** | 本日の値上がり/値下がりTOP3 & モメンタム |
| `DISCORD_WEBHOOK_DEBUG_LOG` | `#システムログ` | 随時 / **23:55** | 始値自動セット通知・システムステータスログ |

---

## ⏰ スケジュール実行 (`cron-job.org` 連携)

GitHub Actions 内蔵 Cron の遅延を回避するため、外部スケジューラ（`cron-job.org`）から GitHub API (`workflow_dispatch`) を呼び出して正確な時間で実行しています。

* **`snapshot.yml`**: 毎時 00分 / 30分（30分間隔）
* **`ranking.yml`**: 毎日 23:50 (JST)
* **`daily_report.yml`**: 毎日 23:55 (JST)

---

## 📂 対応銘柄 (Coincheck 板取引/公開API対応 15銘柄)

`BTC`, `ETH`, `ETC`, `LSK`, `XRP`, `XEM`, `LTC`, `BCH`, `MONA`, `XLM`, `IOST`, `PLT`, `FNCT`, `DAI`, `SHIB`

---

## ⚙️ セットアップ手順

1. **GitHub Secrets の設定**
   * リポジトリの `Settings > Secrets and variables > Actions` に上記 4 つの Webhook URL を登録。
2. **リポジトリ権限の設定**
   * `Settings > Actions > General > Workflow permissions` で **`Read and write permissions`** を選択して保存。
3. **`cron-job.org` 連携**
   * GitHub の Personal Access Token (PAT) を発行し、`cron-job.org` から POST リクエストで各ワークフローを呼び出し設定。
