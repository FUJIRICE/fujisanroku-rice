// /go/buy/[yahoo|libe] — 予約LPから販売先への最終出口（2026-07-12 ソル裁定）
// 固定マニフェストのみ参照。/go/t/ と同じ安全設計（クエリからの任意転送はしない）。

const DESTINATIONS = {
  yahoo: "https://store.shopping.yahoo.co.jp/iwatayacom/",
  libe: "https://libecity.com/shops/577",
};

const FALLBACK = "/reserve/";

export async function onRequest(context) {
  const segments = context.params.path || [];
  const key = segments[0];
  const dest = DESTINATIONS[key];

  if (!dest) {
    return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
  }
  return Response.redirect(dest, 302);
}
