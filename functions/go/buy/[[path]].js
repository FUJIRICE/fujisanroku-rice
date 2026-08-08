// /go/buy[/yahoo|base|libe|main] — 予約LP・SNS・LINEから販売先への最終出口
// (2026-07-12 ソル裁定 / 2026-07-14 ソル裁定でチャネル切替対応)
//
// 固定マニフェストのみ参照。/go/t/ と同じ安全設計(クエリからの任意転送はしない)。
// - /go/buy および /go/buy/main は _channels.js の primary_channel へ転送する。
//   SNS・LINE・HPに置くリンクは今後これを使う(販路切替時にリンク張り替え不要)
// - /go/buy/libe 等の明示指定は従来どおり(既存リンクの互換維持)
// - 2026-08-08: Yahoo店の解約(9/30)に伴い _channels.js から yahoo を削除した。
//   /go/buy/yahoo は転送先なしとなり、下の FALLBACK(/reserve/)へ落ちる。
//   過去に配ったリンク(YouTube動画5本など)を死なせないための設計。

import { CHANNELS, primaryUrl } from "../_channels.js";

const FALLBACK = "/reserve/";
const CAMPAIGN = "r8_2026_newrice";

// BASEの媒体別計測導線。任意URLは受け付けず、ここにある媒体・掲載場所だけを許可する。
const BASE_PLACEMENTS = {
  youtube: ["video", "short", "live"],
  instagram: ["profile", "post"],
  tiktok: ["profile", "post"],
  x: ["post"],
  threads: ["post"],
  facebook: ["post"],
  bluesky: ["post"],
  pinterest: ["profile", "post"],
  line: ["menu"],
  site: ["home", "reserve", "links", "auto-post"],
};

// 商品コードからBASE商品ページへの固定対応。予約LPの商品ボタンで使用する。
const BASE_PRODUCTS = {
  hakumai1kg: "150147951",
  hakumai2kg: "150148195",
  hakumai3kg: "150148574",
  hakumai4kg: "150148645",
  hakumai4kgw: "150148719",
  hakumai5kg: "150147936",
  hakumai10kg: "150147965",
  hakumai10kgw: "150148018",
  hakumai20kg: "150147940",
  hakumai20kgw: "150148107",
  hakumai30kg: "150147971",
  hakumai30kgw: "150148352",
  genmai1kg: "150147984",
  genmai2kg: "150147990",
  genmai3kg: "150148004",
  genmai4kg: "150148008",
  genmai4kgw: "150148011",
  genmai5kg: "150147608",
  genmai10kg: "150147708",
  genmai10kgw: "150147975",
  genmai20kg: "150147895",
  genmai20kgw: "153138154",
  genmai30kg: "150147681",
  genmai30kgw: "150147999",
};

function trackedBaseUrl(source, placement, productCode) {
  if (!BASE_PLACEMENTS[source]?.includes(placement)) return null;
  const productId = productCode ? BASE_PRODUCTS[productCode] : null;
  if (productCode && !productId) return null;

  const target = new URL(
    productId
      ? `https://iwatayacom.thebase.in/items/${productId}`
      : CHANNELS.destinations.base,
  );
  target.searchParams.set("utm_source", source === "site" ? "official_site" : source);
  target.searchParams.set("utm_medium", placement);
  target.searchParams.set("utm_campaign", CAMPAIGN);
  if (productCode) target.searchParams.set("utm_content", productCode);
  return target.toString();
}

export async function onRequest(context) {
  const rawPath = context.params.path || [];
  const segments = Array.isArray(rawPath) ? rawPath : [rawPath];
  const key = segments[0];

  if (!key || key === "main") {
    return Response.redirect(primaryUrl(), 302);
  }

  if (key === "base" && segments.length >= 3) {
    const dest = trackedBaseUrl(segments[1], segments[2], segments[3]);
    if (!dest) {
      return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
    }
    return Response.redirect(dest, 302);
  }

  const dest = CHANNELS.destinations[key];
  if (!dest) {
    return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
  }
  return Response.redirect(dest, 302);
}
