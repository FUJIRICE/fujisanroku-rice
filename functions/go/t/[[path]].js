// /go/t/[platform]/[type][/content-id] — 予約導線計測用リダイレクト（2026-07-12 ソル裁定）
//
// 設計方針:
//   - 固定マニフェストのみを参照する。クエリパラメータから転送先を受け取ることは絶対にしない
//     （オープンリダイレクト対策。/go/t/?url=... のような任意転送は不可）
//   - 既存の /go/yahoo 等9本(static/_redirects)には触れない。名前空間が別なので衝突しない
//   - Cloudflare Pagesの仕様上、Pages Functionが処理するリクエストには_redirectsが適用されない。
//     このFunctionのルートは /go/t/ 配下だけに限定すること（catch-allを広げない）
//   - 転送先は原則 /reserve/ に統一し、UTMパラメータを付与してGA4で流入元を識別する
//   - 不明なパスは 404 を返さず、安全に /reserve/ へフォールバックする

const ROUTES = {
  "youtube/short": { source: "youtube", medium: "short" },
  "youtube/live": { source: "youtube", medium: "live" },
  "youtube/profile": { source: "youtube", medium: "profile" },
  "instagram/profile": { source: "instagram", medium: "profile" },
  "instagram/post": { source: "instagram", medium: "social_post" },
  "tiktok/profile": { source: "tiktok", medium: "profile" },
  "tiktok/post": { source: "tiktok", medium: "social_post" },
  "x/post": { source: "x", medium: "social_post" },
  "threads/post": { source: "threads", medium: "social_post" },
  "bluesky/post": { source: "bluesky", medium: "social_post" },
  "facebook/post": { source: "facebook", medium: "social_post" },
};

const CAMPAIGN = "r8_2026_newrice";
const FALLBACK = "/reserve/";

export async function onRequest(context) {
  const segments = (context.params.path || []);
  // /go/t/youtube/short/rain-reveal-01 → key="youtube/short", content="rain-reveal-01"
  const key = segments.slice(0, 2).join("/");
  const content = segments[2];

  const route = ROUTES[key];
  if (!route) {
    // 不明なパスは安全にフォールバック（外部URLへの任意転送はしない）
    return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
  }

  const dest = new URL(FALLBACK, context.request.url);
  dest.searchParams.set("utm_source", route.source);
  dest.searchParams.set("utm_medium", route.medium);
  dest.searchParams.set("utm_campaign", CAMPAIGN);
  if (content) {
    dest.searchParams.set("utm_content", content);
  }

  return Response.redirect(dest.toString(), 302);
}
