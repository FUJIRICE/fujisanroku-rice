const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('themes/fujirice/static/js/main.js', 'utf8');

function boot({ href, links = [], storage = {}, storageThrows = false, gtag = true, now = 0 }) {
  const listeners = {};
  const store = { ...storage };
  const document = {
    getElementById: () => null,
    querySelectorAll: selector => selector === 'a[href]' ? links : [],
    addEventListener: (name, fn) => { listeners[name] = fn; },
  };
  const sessionStorage = {
    getItem: key => storageThrows ? (() => { throw new Error('storage'); })() : store[key] || null,
    setItem: (key, value) => { if (storageThrows) throw new Error('storage'); store[key] = value; },
    removeItem: key => { if (storageThrows) throw new Error('storage'); delete store[key]; },
  };
  const events = [];
  const window = {
    location: { href, origin: new URL(href).origin, pathname: new URL(href).pathname, scrollY: 0 },
    sessionStorage,
    ...(gtag ? { gtag: (...args) => events.push(args) } : {}),
  };
  const clock = { value: now };
  const context = { window, document, URL, Date: { now: () => clock.value }, JSON, IntersectionObserver: undefined };
  vm.runInNewContext(source, context);
  return { links, listeners, store, events, setNow: value => { clock.value = value; } };
}

function link(href, text = '購入') {
  return { href, textContent: text, addEventListener: () => {}, dataset: {} };
}
function click(env, href) {
  const target = env.links.find(item => item.href === href) || link(href);
  env.listeners.click({ target: { closest: () => target } });
}

// Instagram direct attribution is normalized and decorates an initial site link.
{
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=ig&utm_medium=social', links: [a] });
  assert(a.href.includes('/go/buy/base/instagram/profile/hakumai5kg'));
}

// Instagram social_post remains the post placement.
{
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=instagram&utm_medium=social_post', links: [a] });
  assert(a.href.includes('/go/buy/base/instagram/post/hakumai5kg'));
}

// YouTube profile is allowed, while the explicit route wins over stored Instagram attribution.
{
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=ig&utm_medium=profile', gtag: true });
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/youtube/profile/hakumai5kg');
  env.links.push(a);
  env.listeners.click({ target: { closest: () => a } });
  assert.strictEqual(env.events[0][2].purchase_source, 'youtube');
  assert.strictEqual(env.events[0][2].purchase_placement, 'profile');
}

// After 31 minutes, an initially decorated link is restored to its original site URL.
{
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=ig&utm_medium=social', links: [a], now: 0 });
  assert(a.href.includes('/go/buy/base/instagram/profile/hakumai5kg'));
  env.setNow(31 * 60 * 1000);
  env.listeners.click({ target: { closest: () => a } });
  assert.strictEqual(a.href, 'https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  assert.strictEqual(env.events[0][2].purchase_source, 'official_site');
}

// Internal navigation keeps attribution; aliases from /go/t/ are accepted.
{
  const first = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=youtube&utm_medium=video_description' });
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/posts/today', storage: first.store });
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/links/hakumai5kg');
  env.links.push(a);
  click(env, a.href);
  assert(a.href.includes('/go/buy/base/youtube/video/hakumai5kg'));
}

// X profile attribution is accepted through the twitter alias and survives internal navigation.
{
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  boot({ href: 'https://fujisanroku-rice.pages.dev/go/t/x/profile?utm_source=twitter&utm_medium=profile', links: [a] });
  assert(a.href.includes('/go/buy/base/x/profile/hakumai5kg'));
}

// Expired, invalid, and storage-failing attribution never blocks navigation.
{
  const expired = JSON.stringify({ source: 'instagram', placement: 'profile', expiresAt: 1 });
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/reserve/', links: [link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve')], storage: { fuji_purchase_attribution: expired }, now: 1800000 });
  assert(env.links[0].href.endsWith('/go/buy/base/site/reserve'));
  const failedLink = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/reserve/hakumai5kg');
  const failed = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=ig&utm_medium=profile', links: [failedLink], storageThrows: true, gtag: false });
  assert(failedLink.href.includes('/go/buy/base/instagram/profile/hakumai5kg'));
  failed.listeners.click({ target: { closest: () => failedLink } });
  assert(failedLink.href.includes('/go/buy/base/instagram/profile/hakumai5kg'));
  assert.strictEqual(failed.events.length, 0);
}

// Invalid medium, explicit SNS routes, and libe routes remain unchanged.
{
  const links = [
    link('https://fujisanroku-rice.pages.dev/go/buy/base/site/home'),
    link('https://fujisanroku-rice.pages.dev/go/buy/base/instagram/post'),
    link('https://fujisanroku-rice.pages.dev/go/buy/libe'),
  ];
  boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=instagram&utm_medium=unknown', links });
  assert(links[0].href.endsWith('/go/buy/base/site/home'));
  assert(links[1].href.endsWith('/go/buy/base/instagram/post'));
  assert(links[2].href.endsWith('/go/buy/libe'));
}

// GA-free decoration and dynamic/auxclick links work; GA params preserve product/source page.
{
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=twitter&utm_medium=social_post', gtag: true });
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/auto-post/hakumai5kg');
  env.listeners.auxclick({ button: 1, target: { closest: () => a } });
  assert(a.href.includes('/go/buy/base/x/post/hakumai5kg'));
  assert.strictEqual(env.events[0][2].product_code, 'hakumai5kg');
  assert.strictEqual(env.events[0][2].purchase_source, 'x');
  assert.strictEqual(env.events[0][2].purchase_placement, 'post');
  assert.strictEqual(env.events[0][2].source_page, '/');
}

// Right-click auxclick must not emit a purchase event.
{
  const env = boot({ href: 'https://fujisanroku-rice.pages.dev/?utm_source=ig&utm_medium=profile', gtag: true });
  const a = link('https://fujisanroku-rice.pages.dev/go/buy/base/site/home');
  env.listeners.auxclick({ button: 2, target: { closest: () => a } });
  assert.strictEqual(env.events.length, 0);
}

console.log('purchase attribution tests: ok');
