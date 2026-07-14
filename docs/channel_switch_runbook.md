# 販路切替ランブック (Yahoo → BASE)

作成: 2026-07-14 (Sol裁定)。切替判断は 9/30 第一次経済判定・10/31 最終判定
(判断基準の詳細はメモリ project_sol_priorities_20260714 / ソルスレッド参照)。

## 前提

- 通常時: primary_channel = "yahoo"。BASE店は**非公開のホットスタンバイ**(並売しない)
- SNS・LINE・HPのリンクは全て `/go/buy`(または `/go/buy/main`)経由。直URLを置かない
- 切替は深夜の15分メンテ枠で行い、二重販売状態を作らない

## 切替手順(この順番厳守)

1. Yahooストアの新規受付を停止(注文受付停止 or 全品在庫0)
2. Yahoo側の注文・予約・在庫数を確定し記録
3. BASEへ残在庫数を設定
4. BASEショップを公開に切り替え
5. [functions/go/_channels.js](../functions/go/_channels.js) の `primary_channel` を `"base"`、
   `effective_at` を切替日時にしてコミット+プッシュ(CF Pagesが自動デプロイ)
6. LINEリッチメニュー・自動応答を更新(事前作成済みの切替用メニューを公開)
7. 確認: `/go/buy` がBASEへ302すること、GA4に流入が来ること、BASEでテスト注文が通ること
8. 確認: Yahoo側に新規注文が入らないこと

## ロールバック(切替後に問題が出た場合)

1. `_channels.js` の `primary_channel` を `"yahoo"` に戻してプッシュ
2. BASEショップを非公開に戻す
3. Yahooの受付を再開
4. LINEリッチメニューを元に戻す

## 禁止事項

- **切替直後にYahooを退店しない**。Yahooは自己都合退店すると同一アカウントで再開不可・
  データ復活不可(公式案内)。注文・LINE・レビュー・データ移行を確認してから判断する
- BASEとYahooの同時公開(並売)はしない
