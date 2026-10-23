import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { onRequest as buy } from '../functions/go/buy/[[path]].js';
import { onRequest as entry } from '../functions/go/t/[[path]].js';
import { measuredRedirect } from '../functions/go/_measure.js';

const origin = 'https://fujisanroku-rice.pages.dev';
function context(path, { referrer, ua = 'Mozilla/5.0', method = 'GET' } = {}) {
  const headers = { 'User-Agent': ua };
  if (referrer) headers.Referer = referrer;
  return { params: { path: path.split('/').slice(3) },
    request: new Request(origin + path, { method, headers }) };
}

test('Instagram product route preserves medium and the exact product', async () => {
  const response = await buy(context('/go/buy/base/instagram/profile/hakumai5kg', { referrer: origin + '/reserve/' }));
  assert.equal(response.status, 302);
  const target = new URL(response.headers.get('Location'));
  assert.equal(target.pathname, '/items/150147936');
  assert.equal(target.searchParams.get('utm_source'), 'instagram');
  assert.equal(target.searchParams.get('utm_medium'), 'profile');
  assert.equal(target.searchParams.get('utm_content'), 'hakumai5kg');
});

test('YouTube profile source is valid for product purchase links', async () => {
  const response = await buy(context('/go/buy/base/youtube/profile/hakumai5kg', { method: 'HEAD' }));
  assert.equal(response.status, 302);
  assert.equal(new URL(response.headers.get('Location')).searchParams.get('utm_source'), 'youtube');
});

test('unsupported source, placement, or product never redirects externally', async () => {
  for (const path of ['/go/buy/base/evil/profile', '/go/buy/base/instagram/evil', '/go/buy/base/instagram/profile/evil']) {
    const response = await buy(context(path));
    assert.equal(response.status, 302);
    assert.equal(response.headers.get('Location'), origin + '/reserve/');
  }
});

test('external browser purchase has one purchase event, not a second go_redirect event', async () => {
  const response = await buy(context('/go/buy/base/instagram/profile/hakumai5kg'));
  const html = await response.text();
  assert.equal(response.status, 200);
  assert.match(html, /gtag\("event", "purchase_link_click", ev\)/);
  assert.doesNotMatch(html, /gtag\("event", "go_redirect"/);
  assert.match(html, /"purchase_source":"instagram"/);
  assert.match(html, /"purchase_placement":"profile"/);
  assert.match(html, /"campaign_source":"instagram"/);
  assert.match(html, /<noscript><meta http-equiv="refresh"/);
});

test('same-origin link, HEAD, or known crawler bypass the measurement bridge', async () => {
  for (const options of [{ referrer: origin + '/reserve/' }, { method: 'HEAD' }, { ua: 'facebookexternalhit/1.1' }]) {
    assert.equal((await buy(context('/go/buy/base/instagram/profile', options))).status, 302);
  }
});

test('YouTube profile BASE link now carries attribution', async () => {
  const response = await entry(context('/go/t/youtube/profile/base', { method: 'HEAD' }));
  const target = new URL(response.headers.get('Location'));
  assert.equal(target.hostname, 'iwatayacom.thebase.in');
  assert.equal(target.searchParams.get('utm_source'), 'youtube');
  assert.equal(target.searchParams.get('utm_medium'), 'profile');
});

test('existing Instagram and TikTok entries retain their destinations', async () => {
  const instagram = await entry(context('/go/t/instagram/profile', { method: 'HEAD' }));
  const tiktok = await entry(context('/go/t/tiktok/profile', { method: 'HEAD' }));
  assert.equal(new URL(instagram.headers.get('Location')).pathname, '/reserve/');
  assert.equal(new URL(tiktok.headers.get('Location')).hostname, 'iwatayacom.thebase.in');
});

test('non-purchase redirects retain go_redirect and arbitrary queries are not sent', async () => {
  const request = new Request(origin + '/go/t/youtube/profile/line?email=private-example', { headers: { 'User-Agent': 'Mozilla/5.0' } });
  const html = await measuredRedirect(request, 'https://lin.ee/Clcbnkj', { destination: 'line', source: 'youtube', placement: 'profile' }, 'LINE').text();
  assert.match(html, /gtag\("event", "go_redirect", ev\)/);
  assert.doesNotMatch(html, /private-example/);
});

test('blocked GA still transfers once within the existing 800ms fallback', async () => {
  const response = await buy(context('/go/buy/base/instagram/profile'));
  const html = await response.text();
  const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
  const moves = [], timers = [], dataLayer = [];
  vm.runInNewContext(script, {
    window: { dataLayer }, dataLayer, Date,
    location: { replace: value => moves.push(value) },
    setTimeout: (fn, ms) => timers.push([fn, ms]),
  });
  assert.equal(timers[0][1], 800);
  timers[0][0]();
  const event = dataLayer.find(args => args[0] === 'event');
  event[2].event_callback();
  assert.equal(moves.length, 1);
  assert.equal(new URL(moves[0]).hostname, 'iwatayacom.thebase.in');
});
