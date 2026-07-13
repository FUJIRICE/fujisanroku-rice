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
  // 2026-07-13 ソル裁定: 「媒体×掲載場所」単位で分ける(自動投稿キャプションの/go/t/移行)
  "youtube/video-description": { source: "youtube", medium: "video_description" },
  "youtube/live-description": { source: "youtube", medium: "live_description" },
  "instagram/post": { source: "instagram", medium: "social_post" },
  "instagram/profile": { source: "instagram", medium: "profile" },
  "tiktok/profile": { source: "tiktok", medium: "profile" },
  "tiktok/post": { source: "tiktok", medium: "social_post" },
  "x/post": { source: "x", medium: "social_post" },
  "threads/post": { source: "threads", medium: "social_post" },
  "bluesky/post": { source: "bluesky", medium: "social_post" },
  "facebook/post": { source: "facebook", medium: "social_post" },
};

// 2026-07-13 ソル裁定: YouTubeチャンネルの「リンク」ウィジェット(youtube/profile/*)専用。
// 正解データは data/youtube_channel_links.yaml で一元管理する(このFunctionはそれをハードコード
// した写し。編集は必ずYAML→ここの順で行い、ズレたら気づけるようにする)。
// 予約LP・サイトトップは自ドメインなのでUTM付きでGA4計測が効く。
// Yahoo/LINE/Instagramは外部ドメインのためUTMは付けず直接転送する
// (このURL自体へのアクセス数はCloudflareの標準アクセスログで見える)。
const PROFILE_ROUTES = {
  reserve: { type: "internal", path: "/reserve/", medium: "profile" },
  site: { type: "internal", path: "/", medium: "profile" },
  yahoo: { type: "external", url: "https://store.shopping.yahoo.co.jp/iwatayacom/" },
  line: { type: "external", url: "https://line.me/R/ti/p/%40750jyemd" },
  instagram: { type: "external", url: "https://www.instagram.com/fujirice_farm/" },
};

const CAMPAIGN = "r8_2026_newrice";
const FALLBACK = "/reserve/";

export async function onRequest(context) {
  const segments = (context.params.path || []);

  // /go/t/youtube/profile/[reserve|site|yahoo|line|instagram] — チャンネルリンクウィジェット専用
  if (segments[0] === "youtube" && segments[1] === "profile") {
    const profileRoute = PROFILE_ROUTES[segments[2]];
    if (!profileRoute) {
      return Response.redirect(new URL(FALLBACK, context.request.url).toString(), 302);
    }
    if (profileRoute.type === "external") {
      return Response.redirect(profileRoute.url, 302);
    }
    const dest = new URL(profileRoute.path, context.request.url);
    dest.searchParams.set("utm_source", "youtube");
    dest.searchParams.set("utm_medium", profileRoute.medium);
    dest.searchParams.set("utm_campaign", CAMPAIGN);
    dest.searchParams.set("utm_content", segments[2]);
    return Response.redirect(dest.toString(), 302);
  }

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
