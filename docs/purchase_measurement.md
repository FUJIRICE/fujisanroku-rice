# 販売所へのクリック計測（2026-10-23）

## 指標を混同しない

- `page_view`: ページの表示回数。人数ではない。
- `purchase_link_click`: 販売所へ進む操作の回数。注文・決済完了ではない。
- `go_redirect`: LINE等、購入先以外への外部転送。購入クリックと合算しない。
- 実注文・売上は各販売所の注文管理で確認する。テストクリックもクリック数に含まれる。

## 媒体の引継ぎ

`/go/t/instagram/profile` 等でLPへ入った媒体名と掲載場所を、同じタブのsessionStorageに最大30分保存する。内部ページを移動しても `/go/buy/base/site/...` を既存の媒体別 `/go/buy/base/instagram/profile/...` 等に差し替え、BASE側のUTMにも引き継ぐ。価格、表示文言、商品ID、販売先は変えない。

新しい有効なUTM流入があれば上書きする。保存できないブラウザでも当ページ内の媒体判別と購入遷移は維持する。過去の流入や、タグなしの未判別SNS流入は復元できない。

明示的な媒体別リンクは変更しない。任意URLへの転送・リファラーからの推測は行わない。保存するのは検証済み媒体・掲載場所・失効時刻だけ。

## GA4の項目

| 表示名 | イベントパラメータ | 範囲 |
|---|---|---|
| 購入導線の媒体 | `purchase_source` | イベント |
| 購入導線の掲載場所 | `purchase_placement` | イベント |
| 購入導線の商品 | `product_code` | イベント |

GA4探索「FUJI RICE 媒体別購入クリック 20261023」は、イベント名が `purchase_link_click` と完全一致するものだけを、媒体・商品・掲載場所別に表示する。通常レポートへの新規項目の反映は24〜48時間かかることがある。作成前のイベントは `(not set)` で、ゼロ流入という意味ではない。

LPのクリックはmain.jsで送信する。外部SNS等から販売所向けURLへ直接来た通常ブラウザには、短い中継ページから同じイベントを送信する。自サイトのRefererがある場合は中継側で送らず、通常の二重計測を避ける。Refererが削除される環境や未知のクローラーは完全に識別できないため、厳密な実人数の計測ではない。

GAの読込がブロックされても中継は800msで転送する。JavaScript無効時も転送する。HEAD・既知クローラーは従来の302転送。計測のために購入を止めない。

## 運用リンク例

- Instagramプロフィール: `/go/t/instagram/profile`
- Xプロフィール: `/go/t/x/profile`
- YouTubeプロフィール: `/go/t/youtube/profile/reserve`
- TikTokプロフィール: `/go/t/tiktok/profile`（BASEへ直接）
- YouTube動画: `/go/buy/base/youtube/video`
- X投稿: `/go/buy/base/x/post`
- Threads投稿: `/go/buy/base/threads/post`
- Threadsプロフィール: `/go/t/threads/profile`
- Facebookプロフィール: `/go/t/facebook/profile`
- Facebook投稿: `/go/buy/base/facebook/post`
- Instagramから白米5kgへ: `/go/buy/base/instagram/profile/hakumai5kg`

全て公式サイトのドメインに続ける。直接BASEにUTMを付ける運用と混ぜず、既存の計測用URLを使用する。

## 検証

```sh
node --test tests/test_purchase_attribution.js tests/test_purchase_routes.mjs
```

公開後は実際にプロフィール→LP→BASEをたどり、媒体名・商品IDを確認する。GA4のリアルタイムで `purchase_link_click` と媒体パラメータを受信できたかも別に確認する。UTM付きURLが開いたことだけを「受信成功」と扱わない。
