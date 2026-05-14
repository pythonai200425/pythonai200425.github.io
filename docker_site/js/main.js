/* ============================================================
   DOCKER TUTORIAL — MAIN JS
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ---- Page-exit transitions ---- */
  document.querySelectorAll('a[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto') ||
        href.startsWith('http') || href.startsWith('//')) return;
    link.addEventListener('click', e => {
      e.preventDefault();
      const dest = link.href;
      document.body.style.cssText = 'opacity:0;transform:translateY(-8px);transition:0.25s ease;';
      setTimeout(() => { window.location.href = dest; }, 260);
    });
  });

  /* ---- Copy buttons ---- */
  document.querySelectorAll('.code-wrap').forEach(wrap => {
    const btn  = wrap.querySelector('.copy-btn');
    const code = wrap.querySelector('pre code') || wrap.querySelector('pre');
    if (!btn || !code) return;
    btn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.innerText.trim());
        btn.innerHTML = '✓ Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.innerHTML = '⎘ Copy'; btn.classList.remove('copied'); }, 2000);
      } catch { btn.textContent = 'Failed'; }
    });
  });

  /* ---- Scroll-reveal ---- */
  const ro = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); ro.unobserve(e.target); } });
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(el => ro.observe(el));

  /* ---- Sidebar toggle (mobile) ---- */
  const menuBtn = document.querySelector('.menu-toggle');
  const sidebar  = document.querySelector('.sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', e => {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) && e.target !== menuBtn) {
        sidebar.classList.remove('open');
      }
    });
  }

  /* ---- Progress tracking with localStorage ---- */
  const pathMatch = window.location.pathname.match(/(\d{2})-/);
  if (pathMatch) {
    const num = parseInt(pathMatch[1], 10);
    localStorage.setItem(`docker-tut-ch${num}`, '1');

    // Mark visited chapters in sidebar
    document.querySelectorAll('.chapter-item').forEach(item => {
      const a = item.querySelector('a');
      if (!a) return;
      const m = a.getAttribute('href').match(/(\d{2})-/);
      if (m && localStorage.getItem(`docker-tut-ch${parseInt(m[1], 10)}`)) {
        item.classList.add('visited');
      }
    });
  }

  /* ---- Particles (home page only) ---- */
  const canvas = document.getElementById('particles');
  if (canvas) initParticles(canvas);

  /* ---- Active chapter highlight on home page ---- */
  const grid = document.querySelector('.chapters-grid');
  if (grid) {
    for (let i = 1; i <= 10; i++) {
      if (localStorage.getItem(`docker-tut-ch${i}`)) {
        const card = grid.querySelector(`[data-ch="${i}"]`);
        if (card) card.classList.add('visited-card');
      }
    }
  }
});

/* ---- Particle system ---- */
function initParticles(canvas) {
  const ctx = canvas.getContext('2d');
  let w, h;

  const resize = () => {
    w = canvas.width  = canvas.offsetWidth  || window.innerWidth;
    h = canvas.height = canvas.offsetHeight || window.innerHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  const pts = Array.from({ length: 70 }, () => ({
    x:  Math.random() * 1500, y: Math.random() * 900,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
    r:  Math.random() * 1.8 + 0.4,
    a:  Math.random() * 0.35 + 0.06
  }));

  const LINK = 110;

  const tick = () => {
    ctx.clearRect(0, 0, w, h);
    pts.forEach(p => {
      p.x = ((p.x + p.vx) + w) % w;
      p.y = ((p.y + p.vy) + h) % h;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(36,150,237,${p.a})`;
      ctx.fill();
    });
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x;
        const dy = pts[i].y - pts[j].y;
        const d  = Math.hypot(dx, dy);
        if (d < LINK) {
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.strokeStyle = `rgba(36,150,237,${0.1 * (1 - d / LINK)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(tick);
  };
  tick();
}
