// /go/yt/[shorts|live]/[platform]/[placement]
// SNSからYouTubeへの回遊を、販売導線と混ぜずに計測する固定リダイレクト。
// 任意URLは受け付けず、下記の媒体と掲載場所だけを許可する。

const TARGETS = {
  shorts: "https://www.youtube.com/@fujirice_official/shorts",
  live: "https://www.youtube.com/@fujirice_official/live",
};

const PLACEMENTS = {
  shorts: "morning-shorts",
  live: "sunday-live",
};

const PLATFORMS = new Set(["facebook", "x", "threads", "bluesky"]);
const CAMPAIGN = "r8_2026_youtube";
const FALLBACK = "https://www.youtube.com/@fujirice_official";

export async function onRequest(context) {
  const rawPath = context.params.path || [];
  const segments = Array.isArray(rawPath) ? rawPath : [rawPath];
  const [kind, platform, placement] = segments;

  if (!TARGETS[kind] || !PLATFORMS.has(platform) || PLACEMENTS[kind] !== placement) {
    return Response.redirect(FALLBACK, 302);
  }

  const dest = new URL(TARGETS[kind]);
  dest.searchParams.set("utm_source", platform);
  dest.searchParams.set("utm_medium", placement);
  dest.searchParams.set("utm_campaign", CAMPAIGN);
  return Response.redirect(dest.toString(), 302);
}
