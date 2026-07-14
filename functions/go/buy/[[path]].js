// /go/buy[/yahoo|base|libe|main] — 予約LP・SNS・LINEから販売先への最終出口
// (2026-07-12 ソル裁定 / 2026-07-14 ソル裁定でチャネル切替対応)
//
// 固定マニフェストのみ参照。/go/t/ と同じ安全設計(クエリからの任意転送はしない)。
// - /go/buy および /go/buy/main は _channels.js の primary_channel へ転送する。
//   SNS・LINE・HPに置くリンクは今後これを使う(販路切替時にリンク張り替え不要)
// - /go/buy/yahoo 等の明示指定は従来どおり(既存リンクの互換維持)

import { CHANNELS, primaryUrl } from "../_channels.js";

const FALLBACK = "/reserve/";

export async function onRequest(context) {
  const segments = context.params.path || [];
  const key = segments[0];

  if (!key || key === "main") {
    return Response.redirect(primaryUrl(), 302);
  }

  const dest = CHANNELS.destinations[key];
  if (!dest) {
    return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
  }
  return Response.redirect(dest, 302);
}
