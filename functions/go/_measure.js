// 外部販売所・外部サイトへ出る /go/ リンクのクリック計測(2026-10-22)
//
// これまで /go/buy などは 302 で即転送していたため、SNSから直接来た人は
// LPのGA4を一度も通らず、どの媒体・掲載場所でクリックされたか記録されていなかった。
// (LP上のボタンは main.js の purchase_link_click で計測済み)
//
// そこで「自サイト以外からの通常のブラウザアクセス」で、GA4イベントを送ってから
// 転送する短いページを返す。転送は最長0.8秒で必ず行う(GA4が読めなくても止まらない)。
// 購入先は purchase_link_click、それ以外は従来の go_redirect。
// クローラー判定は完全ではないため、イベント数を実人数・注文数と扱わない。
//
// 次の場合は従来どおり 302 で即転送する:
//   - LP内のボタンから来た(Refererが自ドメイン) … main.js で計測済みのため二重計測を避ける
//   - SNSのリンクカードを作るクローラー … 302 でないとカード表示が崩れる
//   - GET 以外(HEAD など)
//
// このファイルは onRequest を持たないので、Pages Functions のルートにはならない。

const GA4_ID = "G-ZGY13FK4V1";

// リンクカード生成・検索エンジンのクローラー。
// アプリ内ブラウザ(Instagram / LINE / Pinterest / TikTok 等)は人間なので含めない。
const CRAWLER_UA =
  /bot\b|bot\/|crawler|spider|facebookexternalhit|facebookcatalog|meta-externalagent|cardyb|embedly|skypeuripreview|whatsapp|google-inspectiontool|googleother|headlesschrome|curl\/|wget\/|python-requests|okhttp/i;

function isSameOriginReferer(request) {
  const ref = request.headers.get("Referer");
  if (!ref) return false;
  try {
    return new URL(ref).origin === new URL(request.url).origin;
  } catch {
    return false;
  }
}

export function shouldMeasure(request) {
  if (request.method !== "GET") return false;
  const ua = request.headers.get("User-Agent") || "";
  if (!ua || CRAWLER_UA.test(ua)) return false;
  if (isSameOriginReferer(request)) return false;
  return true;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// JSON をそのまま <script> に埋めても </script> で閉じられないようにする
function safeJson(v) {
  return JSON.stringify(v).replace(/</g, "\\u003c");
}

/**
 * 計測付きで転送する。計測不要なリクエストには 302 を返す。
 * @param {Request} request
 * @param {string} dest 転送先(固定マニフェストから組み立てた URL のみ)
 * @param {object} params GA4 に送るパラメータ(destination / source / placement / product_code)
 * @param {string} label 画面に出す行き先名
 */
export function measuredRedirect(request, dest, params, label) {
  if (!shouldMeasure(request)) return Response.redirect(dest, 302);

  const purchase = ["base", "libe"].includes(params.destination);
  const eventName = purchase ? "purchase_link_click" : "go_redirect";
  const event = {
    ...params,
    ...(purchase ? {
      purchase_source: params.source === "site" ? "official_site" : params.source,
      purchase_placement: params.placement,
      source_page: new URL(request.url).pathname,
    } : {}),
    go_path: new URL(request.url).pathname,
    transport_type: "beacon",
  };
  const config = {
    send_page_view: false,
    // 任意の入力クエリ（個人情報等の混入）をGA4へ渡さない。
    page_location: new URL(request.url).origin + new URL(request.url).pathname,
  };
  const target = new URL(dest);
  if (purchase && target.searchParams.has("utm_source")) {
    config.campaign_source = target.searchParams.get("utm_source");
    config.campaign_medium = target.searchParams.get("utm_medium");
    config.campaign_name = target.searchParams.get("utm_campaign");
  }
  const html = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>${escapeHtml(label)}へ移動しています｜FUJI RICE</title>
<noscript><meta http-equiv="refresh" content="0;url=${escapeHtml(dest)}"></noscript>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans",sans-serif;background:#faf8f2;color:#3b3a36;text-align:center}
p{margin:.5em 1em;font-size:15px}a{color:#3b6b35}
</style>
<script async src="https://www.googletagmanager.com/gtag/js?id=${GA4_ID}"></script>
<script>
(function () {
  var dest = ${safeJson(dest)};
  var moved = false;
  function go() { if (moved) return; moved = true; location.replace(dest); }
  window.dataLayer = window.dataLayer || [];
  function gtag() { dataLayer.push(arguments); }
  gtag("js", new Date());
  gtag("config", ${safeJson(GA4_ID)}, ${safeJson(config)});
  var ev = ${safeJson(event)};
  ev.event_callback = go;
  ev.event_timeout = 600;
  gtag("event", ${safeJson(eventName)}, ev);
  setTimeout(go, 800);
})();
</script>
</head>
<body>
<div>
<p>${escapeHtml(label)}へ移動しています…</p>
<p><a href="${escapeHtml(dest)}">移動しない場合はこちら</a></p>
</div>
</body>
</html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
      "Referrer-Policy": "strict-origin-when-cross-origin",
    },
  });
}
