/* Della Antony — portfolio. Vanilla JS, no dependencies, no tracking. */
(() => {
  'use strict';
  const d = document, root = d.documentElement;
  const $ = (s, c = d) => c.querySelector(s);
  const $$ = (s, c = d) => Array.from(c.querySelectorAll(s));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const wait = ms => new Promise(r => setTimeout(r, ms));

  /* ── 1. Title sequence: black → typed slate line → name → languages → slate ── */
  async function titleSequence() {
    const on = k => $$('[data-in="' + k + '"]').forEach(el => el.classList.add('on'));
    if (reduce) { ['typed', 'img', 'name', 'line', 'langs', 'meta'].forEach(on); return; }

    const typed = $('#typed'), out = $('.typed-out', typed), text = typed.dataset.text;
    out.textContent = '';

    await wait(600);                       // a black screen, then…
    on('typed'); typed.classList.add('typing');
    setTimeout(() => on('img'), 300);      // her face arrives while the line types
    setTimeout(() => on('name'), 650);     // name fades in, tracking tightens over 2 s
    for (const ch of text) { out.textContent += ch; await wait(26 + Math.random() * 20); }
    typed.classList.remove('typing');
    await wait(300);  on('line');
    await wait(900);  on('langs');
    await wait(500);  on('meta');
  }

  /* ── 2. Scroll reveals ── */
  function reveals() {
    const els = $$('.reveal');
    // Browsers with scroll-driven animations (animation-timeline) handle this in CSS
    if (window.CSS && CSS.supports && CSS.supports('animation-timeline: view()')) return;
    if (!('IntersectionObserver' in window)) { els.forEach(e => e.classList.add('in')); return; }
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(e => io.observe(e));
  }

  /* ── 3. Nav: current scene gets the red dot; bar gains a backing after the title ── */
  function nav() {
    const links = $$('.scenes a'), bar = $('.bar');
    const mark = id => links.forEach(a => a.setAttribute('aria-current', String(a.dataset.scene === id)));
    mark('sc1');
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) mark(e.target.id); }),
        { rootMargin: '-45% 0px -50% 0px' });
      $$('main > section').forEach(s => io.observe(s));
    }
    const onScroll = () => bar.classList.toggle('scrolled', scrollY > 40);
    addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  /* ── 4. Lightbox: arrows, swipe, Esc ── */
  function lightbox() {
    const dlg = $('#lb'), img = $('#lb-img'), count = $('#lb-count');
    const btns = $$('.pair .fr-btn'), total = btns.length;
    let i = 0, opener = null;
    const pad = n => String(n).padStart(2, '0');
    const show = n => {
      i = (n + total) % total;
      const b = btns[i];
      img.src = b.dataset.full;
      img.alt = $('img', b).alt;
      count.textContent = 'FR. ' + pad(i + 1) + ' / ' + pad(total) + ' — ' + b.dataset.word.toUpperCase();
    };
    const open = n => {
      opener = btns[n]; show(n);
      if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
      root.style.overflow = 'hidden';
    };
    const close = () => { if (dlg.open) dlg.close(); };
    dlg.addEventListener('close', () => { root.style.overflow = ''; img.removeAttribute('src'); opener && opener.focus({ preventScroll: true }); });
    btns.forEach((b, n) => b.addEventListener('click', () => open(n)));
    $('#lb-close').addEventListener('click', close);
    $('#lb-prev').addEventListener('click', () => show(i - 1));
    $('#lb-next').addEventListener('click', () => show(i + 1));
    dlg.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(i - 1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); show(i + 1); }
    });
    // swipe
    let x0 = null, y0 = null;
    dlg.addEventListener('pointerdown', e => { x0 = e.clientX; y0 = e.clientY; });
    dlg.addEventListener('pointerup', e => {
      if (x0 === null) return;
      const dx = e.clientX - x0, dy = e.clientY - y0; x0 = y0 = null;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) show(i + (dx < 0 ? 1 : -1));
      else if (e.target === dlg || e.target.classList.contains('lb-stage')) close();   // tap on black closes
    });
    dlg.addEventListener('pointercancel', () => { x0 = y0 = null; });
  }

  /* ── 4b. Biodata tabs (English / മലയാളം / हिंदी) ── */
  function tabs() {
    const tabs = $$('.tabs [role="tab"]');
    const pick = t => {
      tabs.forEach(x => {
        const on = x === t;
        x.setAttribute('aria-selected', String(on)); x.tabIndex = on ? 0 : -1;
        $('#' + x.getAttribute('aria-controls')).hidden = !on;
      });
    };
    tabs.forEach((t, k) => {
      t.addEventListener('click', () => pick(t));
      t.addEventListener('keydown', e => {
        const n = { ArrowRight: k + 1, ArrowLeft: k - 1, Home: 0, End: tabs.length - 1 }[e.key];
        if (n === undefined) return;
        e.preventDefault(); const nt = tabs[(n + tabs.length) % tabs.length]; pick(nt); nt.focus();
      });
    });
  }

  /* ── 4c. Rail arrows (desktop; phones just swipe) ── */
  function rails() {
    $$('.rail-nav button').forEach(b => b.addEventListener('click', () => {
      const r = d.getElementById(b.dataset.rail), step = Math.max(240, r.clientWidth * 0.7);
      r.scrollBy({ left: step * Number(b.dataset.dir), behavior: reduce ? 'auto' : 'smooth' });
    }));
  }

  /* ── 5. Voices ── */
  function voices() {
    const list = $('#slates'), cards = $$('.clip', list);
    const W = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten'];
    // slate numbers, card count and the intro line follow whatever clips are on the page
    cards.forEach((c, k) => { const n = $('.num', c); if (n) n.textContent = String(k + 1).padStart(2, '0'); });
    list.style.setProperty('--n', cards.length);
    const langs = new Set(cards.map(c => c.dataset.lang));
    if (W[cards.length] && W[langs.size]) {
      $('#lede').textContent = W[cards.length] + ' takes. ' + W[langs.size] + (langs.size === 1 ? ' language. ' : ' languages. ') + 'One voice.';
    }

    let current = null;                          // only one clip at a time
    const stop = card => {
      if (!card) return;
      const f = $('.frame', card);
      const v = $('video', f);
      if (v) { v.pause(); v.currentTime = 0; const c = $('.ctrl', f); c && c.remove(); }
      const fr = $('iframe', f); fr && fr.remove();
      f.classList.remove('live');
    };
    const startDrive = card => {
      const f = $('.frame', card), ifr = d.createElement('iframe');
      ifr.src = 'https://drive.google.com/file/d/' + card.dataset.drive + '/preview';
      ifr.title = card.dataset.title + ' (video)';
      ifr.allow = 'autoplay; fullscreen'; ifr.allowFullscreen = true;
      ifr.referrerPolicy = 'no-referrer';
      f.appendChild(ifr); f.classList.add('live');
    };
    const ICON = {
      play: '<svg class="ic-play" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l11-6.5z"/></svg><svg class="ic-pause" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h3.6v14H7zM13.4 5H17v14h-3.6z"/></svg>',
      vol: '<svg class="ic-vol" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5v5h3.6L12 18.5v-13L7.6 9.5zM14.5 8.6a4.6 4.6 0 0 1 0 6.8l-1.2-1.2a2.9 2.9 0 0 0 0-4.4zM17 6.2a8 8 0 0 1 0 11.6l-1.2-1.2a6.3 6.3 0 0 0 0-9.2z"/></svg><svg class="ic-mute" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5v5h3.6L12 18.5v-13L7.6 9.5zM15 9.4l1.4-1.4 2.1 2.1 2.1-2.1L22 9.4l-2.1 2.1 2.1 2.1-1.4 1.4-2.1-2.1-2.1 2.1-1.4-1.4 2.1-2.1z"/></svg>'
    };
    const startLocal = card => {
      const f = $('.frame', card), v = $('video', f);
      const ctrl = d.createElement('div'); ctrl.className = 'ctrl';
      ctrl.innerHTML =
        '<button type="button" class="pp is-playing" aria-label="Pause">' + ICON.play + '</button>' +
        '<input class="seek" type="range" min="0" max="1000" value="0" step="1" aria-label="Seek">' +
        '<button type="button" class="mute" aria-pressed="false" aria-label="Mute">' + ICON.vol + '</button>';
      f.appendChild(ctrl); f.classList.add('live');
      const pp = $('.pp', ctrl), seek = $('.seek', ctrl), mute = $('.mute', ctrl);
      v.muted = false; v.controls = false;
      pp.addEventListener('click', () => { v.paused ? v.play() : v.pause(); });
      v.addEventListener('play', () => { pp.classList.add('is-playing'); pp.setAttribute('aria-label', 'Pause'); });
      v.addEventListener('pause', () => { pp.classList.remove('is-playing'); pp.setAttribute('aria-label', 'Play'); });
      v.addEventListener('timeupdate', () => { if (v.duration) seek.value = Math.round(v.currentTime / v.duration * 1000); });
      v.addEventListener('ended', () => { if (current === card) { stop(card); current = null; } });
      seek.addEventListener('input', () => { if (v.duration) v.currentTime = seek.value / 1000 * v.duration; });
      mute.addEventListener('click', () => {
        v.muted = !v.muted; mute.setAttribute('aria-pressed', String(v.muted)); mute.setAttribute('aria-label', v.muted ? 'Unmute' : 'Mute');
      });
      v.play().catch(() => { pp.classList.remove('is-playing'); });
      pp.focus({ preventScroll: true });
    };
    list.addEventListener('click', e => {
      const btn = e.target.closest('.play'); if (!btn) return;
      const card = btn.closest('.clip');
      if (current && current !== card) stop(current);
      current = card;
      card.dataset.kind === 'drive' ? startDrive(card) : startLocal(card);
    });
  }

  /* ── 6. Copy email ── */
  function copy() {
    const btn = $('#copy'), status = $('#copy-status'), email = $('#email').textContent.trim();
    let t;
    const done = () => {
      btn.textContent = 'COPIED'; btn.classList.add('done'); status.textContent = 'Email address copied';
      clearTimeout(t); t = setTimeout(() => { btn.textContent = 'Copy email'; btn.classList.remove('done'); status.textContent = ''; }, 2200);
    };
    btn.addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(email); done(); }
      catch {
        const ta = d.createElement('textarea'); ta.value = email; ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;opacity:0;top:0'; d.body.appendChild(ta); ta.select();
        try { d.execCommand('copy'); done(); } catch { /* user can still tap the address */ }
        ta.remove();
      }
    });
  }

  /* Once the page has finished loading, fetch the sideways-slider photos too, so none is left blank on tablets */
  addEventListener('load', () => setTimeout(() => $$('.rail img[loading="lazy"]').forEach(i => { i.loading = 'eager'; }), 400));

  titleSequence(); reveals(); nav(); lightbox(); tabs(); rails(); voices(); copy();
})();
