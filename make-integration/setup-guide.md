# Make.com 連携セットアップガイド

## 全体の自動化フロー

git push → GitHub Actions → Cloudflare Pages → Make.com → Instagram / X / LINE

## ステップ 4: GitHub Secrets に追加

| Secret 名 | 値 |
|-----------|-----|
| `CLOUDFLARE_API_TOKEN` | Cloudflare APIトークン |
| `CLOUDFLARE_ACCOUNT_ID` | CloudflareアカウントID |
| `MAKE_WEBHOOK_URL` | MakeのWebhook URL |

詳細手順は make-integration/setup-guide.md を参照
