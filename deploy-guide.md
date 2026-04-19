# FUJI RICE - Cloudflare Pages デプロイガイド

## 前提条件

- [Hugo](https://gohugo.io/installation/) (v0.128.0 以上, Extended版)
- [Git](https://git-scm.com/)
- [GitHub](https://github.com/) アカウント
- [Cloudflare](https://cloudflare.com/) アカウント（無料プランで可）

## ステップ 4: Cloudflare Pages の設定

| 項目 | 値 |
|------|-----|
| プロジェクト名 | `fujirice` |
| 本番ブランチ | `main` |
| フレームワークプリセット | `Hugo` |
| ビルドコマンド | `hugo --gc --minify` |
| ビルド出力ディレクトリ | `public` |
| HUGO_VERSION | `0.128.0` |
