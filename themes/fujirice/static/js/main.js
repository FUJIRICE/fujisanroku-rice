// FUJI RICE - Main JavaScript v3.0 (Grand Design Dark Edition)

(function () {
  'use strict';

  // ── Header scroll effect ──
  const header = document.getElementById('site-header');
  if (header) {
    window.addEventListener('scroll', () => {
      header.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
  }

  // ── Mobile nav toggle ──
  const navToggle = document.getElementById('nav-toggle');
  const mainNav = document.getElementById('main-nav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', () => {
      const isOpen = mainNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen);
    });
    // Close nav on link click
    mainNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        mainNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // ── Share buttons ──
  document.querySelectorAll('.share-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const type = btn.dataset.share;
      const url = encodeURIComponent(location.href);
      const title = encodeURIComponent(document.title);
      let shareURL = '';
      if (type === 'twitter') shareURL = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
      else if (type === 'facebook') shareURL = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
      else if (type === 'line') shareURL = `https://social-plugins.line.me/lineit/share?url=${url}`;
      if (shareURL) window.open(shareURL, '_blank', 'width=600,height=450');
    });
  });

  // ── Purchase attribution ──
  // Keep only validated attribution in this tab.  No referrer or arbitrary
  // query parameters are persisted, and only the existing site purchase
  // routes are decorated.
  const ATTRIBUTION_KEY = 'fuji_purchase_attribution';
  const ATTRIBUTION_TTL = 30 * 60 * 1000;
  const ATTRIBUTION_SOURCES = {
    ig: 'instagram',
    instagram: 'instagram',
    twitter: 'x',
    x: 'x',
    youtube: 'youtube',
    tiktok: 'tiktok',
    threads: 'threads',
    facebook: 'facebook',
    bluesky: 'bluesky',
    pinterest: 'pinterest',
    line: 'line',
    site: 'site',
    official_site: 'site',
  };
  const ATTRIBUTION_PLACEMENTS = {
    youtube: ['profile', 'video', 'short', 'live'],
    instagram: ['profile', 'post'],
    tiktok: ['profile', 'post'],
    x: ['profile', 'post', 'morning-reserve', 'evening-reserve'],
    threads: ['profile', 'post', 'morning-reserve', 'evening-reserve'],
    facebook: ['profile', 'post', 'morning-reserve', 'evening-reserve'],
    bluesky: ['post', 'morning-reserve', 'evening-reserve'],
    pinterest: ['profile', 'post'],
    line: ['menu'],
    site: ['home', 'reserve', 'links', 'auto-post'],
  };
  const ATTRIBUTION_PLACEMENT_ALIASES = {
    social_post: 'post',
    video_description: 'video',
    live_description: 'live',
  };
  const originalPurchaseHrefs = new WeakMap();
  let memoryAttribution = null;
  const SITE_PURCHASE_RE = /^\/go\/buy\/base\/site\/(home|reserve|links|auto-post)(?:\/([^/?#]+))?\/?$/;

  function readAttribution() {
    try {
      const raw = window.sessionStorage.getItem(ATTRIBUTION_KEY);
      if (!raw) return null;
      const value = JSON.parse(raw);
      if (!value || !value.source || !value.placement || !Number.isFinite(value.expiresAt) || value.expiresAt <= Date.now() || value.expiresAt > Date.now() + ATTRIBUTION_TTL) {
        window.sessionStorage.removeItem(ATTRIBUTION_KEY);
        return null;
      }
      if (!ATTRIBUTION_PLACEMENTS[value.source] || !ATTRIBUTION_PLACEMENTS[value.source].includes(value.placement)) {
        window.sessionStorage.removeItem(ATTRIBUTION_KEY);
        return null;
      }
      return value;
    } catch (_) {
      return null;
    }
  }

  function saveAttribution(source, placement) {
    const expiresAt = Date.now() + ATTRIBUTION_TTL;
    memoryAttribution = { source, placement, expiresAt };
    try {
      window.sessionStorage.setItem(ATTRIBUTION_KEY, JSON.stringify({
        source,
        placement,
        expiresAt,
      }));
    } catch (_) {
      // Storage is optional; navigation and measurement must still work.
    }
  }

  function attributionFromURL(url) {
    const rawSource = (url.searchParams.get('utm_source') || '').toLowerCase();
    const source = ATTRIBUTION_SOURCES[rawSource];
    const rawPlacement = (url.searchParams.get('utm_medium') || '').toLowerCase();
    let placement = ATTRIBUTION_PLACEMENT_ALIASES[rawPlacement] || rawPlacement;
    if (source === 'instagram' && rawPlacement === 'social') placement = 'profile';
    if (!source || !ATTRIBUTION_PLACEMENTS[source] || !ATTRIBUTION_PLACEMENTS[source].includes(placement)) return null;
    return { source, placement };
  }

  function sitePurchaseParts(url) {
    if (url.origin !== window.location.origin) return null;
    const match = url.pathname.match(SITE_PURCHASE_RE);
    return match ? { placement: match[1], product: match[2] || '' } : null;
  }

  function explicitPurchaseAttribution(url) {
    if (url.origin !== window.location.origin) return null;
    const match = url.pathname.match(/^\/go\/buy\/base\/([^/]+)\/([^/]+)(?:\/[^/?#]+)?\/?$/);
    if (!match) return null;
    const source = ATTRIBUTION_SOURCES[match[1]];
    const placement = match[2];
    if (!source || source === 'site' || !ATTRIBUTION_PLACEMENTS[source]?.includes(placement)) return null;
    return { source, placement };
  }

  function currentAttribution() {
    const stored = readAttribution();
    if (stored) return stored;
    if (!memoryAttribution || !Number.isFinite(memoryAttribution.expiresAt) || memoryAttribution.expiresAt <= Date.now() || memoryAttribution.expiresAt > Date.now() + ATTRIBUTION_TTL) {
      memoryAttribution = null;
      return null;
    }
    return memoryAttribution;
  }

  function decoratePurchaseLink(link) {
    if (!link || !link.href) return;
    if (!originalPurchaseHrefs.has(link)) originalPurchaseHrefs.set(link, link.href);
    link.href = originalPurchaseHrefs.get(link);
    const url = new URL(link.href, window.location.href);
    const parts = sitePurchaseParts(url);
    const attribution = currentAttribution();
    if (!parts || !attribution) return;
    url.pathname = `/go/buy/base/${attribution.source}/${attribution.placement}/${parts.product}`.replace(/\/$/, '');
    link.href = url.toString();
  }

  const initialAttribution = attributionFromURL(new URL(window.location.href));
  if (initialAttribution) saveAttribution(initialAttribution.source, initialAttribution.placement);
  document.querySelectorAll('a[href]').forEach(decoratePurchaseLink);

  // ── Purchase link measurement ──
  // /go/buy/ is a same-domain redirect, so GA4's automatic outbound-click
  // measurement cannot reliably identify the moment a visitor chooses a shop.
  function handlePurchaseInteraction(event) {
    const link = event.target.closest('a[href]');
    if (!link) return;
    decoratePurchaseLink(link);

    const target = new URL(link.href, window.location.href);
    const pathParts = target.pathname.split('/').filter(Boolean);
    const linkText = (link.textContent || '').trim().slice(0, 100);

    if (target.origin === window.location.origin && pathParts[0] === 'go' && pathParts[1] === 'buy' && typeof window.gtag === 'function') {
      const attribution = explicitPurchaseAttribution(target) || currentAttribution();
      window.gtag('event', 'purchase_link_click', {
        destination: pathParts[2] || 'unknown',
        placement: pathParts.slice(3, 5).join('/') || 'unspecified',
        product_code: pathParts[5] || 'unspecified',
        source_page: window.location.pathname,
        link_url: link.href,
        link_text: linkText,
        transport_type: 'beacon',
        purchase_source: attribution ? attribution.source : 'official_site',
        purchase_placement: attribution ? attribution.placement : 'official_site',
      });
      return;
    }

    if (typeof window.gtag === 'function' && (target.hostname === 'line.me' || target.hostname === 'lin.ee' || target.pathname === '/go/line' || target.pathname === '/go/line/')) {
      window.gtag('event', 'line_lead_click', {
        source_page: window.location.pathname,
        link_url: link.href,
        link_text: linkText,
        transport_type: 'beacon',
      });
    }
  }
  document.addEventListener('click', handlePurchaseInteraction);
  document.addEventListener('auxclick', event => {
    if (event.button === 1) handlePurchaseInteraction(event);
  });

  // ── Fade-in on scroll ──
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('gd-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.gd-stat, .gd-blog-card, .post-card').forEach(el => {
      el.classList.add('gd-fade-in');
      observer.observe(el);
    });
  }

})();
