document.addEventListener('DOMContentLoaded', function() {
  const header = document.querySelector('.site-header');
  if (header) {
    window.addEventListener('scroll', function() {
      header.classList.toggle('scrolled', window.scrollY > 50);
    });
  }
  const navToggle = document.querySelector('.nav-toggle');
  const mainNav = document.querySelector('.main-nav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', function() {
      mainNav.classList.toggle('open');
      const isOpen = mainNav.classList.contains('open');
      navToggle.setAttribute('aria-expanded', isOpen);
      const spans = navToggle.querySelectorAll('span');
      if (isOpen) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      }
    });
    document.addEventListener('click', function(e) {
      if (!header.contains(e.target)) {
        mainNav.classList.remove('open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.addEventListener('load', function() { entry.target.classList.add('loaded'); });
          imageObserver.unobserve(entry.target);
        }
      });
    });
    document.querySelectorAll('img[loading="lazy"]').forEach(function(img) { imageObserver.observe(img); });
    const animObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry, i) {
        if (entry.isIntersecting) {
          setTimeout(function() { entry.target.style.opacity='1'; entry.target.style.transform='translateY(0)'; }, i*80);
          animObserver.unobserve(entry.target);
        }
      });
    }, {threshold:0.1});
    document.querySelectorAll('.post-card,.feature-item').forEach(function(el) {
      el.style.opacity='0'; el.style.transform='translateY(20px)'; el.style.transition='opacity 0.5s ease,transform 0.5s ease';
      animObserver.observe(el);
    });
  }
  document.querySelectorAll('.share-btn[data-share]').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      const url = encodeURIComponent(window.location.href);
      const title = encodeURIComponent(document.title);
      let shareUrl = '';
      switch(btn.dataset.share) {
        case 'twitter': shareUrl = 'https://twitter.com/intent/tweet?url='+url+'&text='+title; break;
        case 'facebook': shareUrl = 'https://www.facebook.com/sharer/sharer.php?u='+url; break;
        case 'line': shareUrl = 'https://social-plugins.line.me/lineit/share?url='+url; break;
      }
      if (shareUrl) window.open(shareUrl,'_blank','width=600,height=400');
    });
  });
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) { e.preventDefault(); window.scrollTo({top:target.getBoundingClientRect().top+window.pageYOffset-80,behavior:'smooth'}); }
    });
  });
});
