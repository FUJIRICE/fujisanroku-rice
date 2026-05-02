// FUJI RICE - Main JavaScript v2.0

(function() {
  'use strict';
  
  // Navigation scroll effect
  const nav = document.getElementById('site-header');
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 80) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    });
  }
  
  // Mobile nav toggle
  const navToggle = document.getElementById('nav-toggle');
  const mainNav = document.getElementById('main-nav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', () => {
      const isOpen = mainNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen);
    });
  }
  
  // Fade in animation on scroll (intersection observer)
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  
  document.querySelectorAll('.season, .product, .stat, .journal-card, .bl-card, .bl-article').forEach(el => {
    el.classList.add('fade-in-up');
    observer.observe(el);
  });
  
})();
