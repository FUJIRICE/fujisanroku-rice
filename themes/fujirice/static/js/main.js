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
