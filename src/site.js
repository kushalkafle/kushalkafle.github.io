// Research tabs (deep-linkable as #research/<tab>, papers as #pub-<bibkey>) and the mobile nav toggle.
(function () {
  const buttons = document.querySelectorAll('.tabs [role="tab"]');

  function show(id, updateHash) {
    const btn = document.getElementById('tab-' + id);
    if (!btn) return false;
    buttons.forEach(b => {
      const on = b === btn;
      b.setAttribute('aria-selected', on);
      document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
    });
    if (updateHash) history.replaceState(null, '', '#research/' + id);
    return true;
  }

  buttons.forEach(b => b.addEventListener('click', () => show(b.dataset.tab, true)));

  function fromHash() {
    const m = location.hash.match(/^#research\/(\w+)/);
    if (m && show(m[1], false)) document.getElementById('research').scrollIntoView();
    const p = location.hash.match(/^#pub-([\w-]+)/);
    if (p) {
      const el = document.getElementById('pub-' + p[1]);
      if (!el) return;
      show('all', false);
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.remove('flash');
      void el.offsetWidth;
      el.classList.add('flash');
    }
  }
  window.addEventListener('hashchange', fromHash);
  fromHash();

  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  toggle.addEventListener('click', () => {
    const open = links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });
  links.addEventListener('click', e => {
    if (e.target.tagName === 'A') links.classList.remove('open');
  });

  // Highlight the nav link for the section currently in view.
  const navLinks = [...document.querySelectorAll('.nav-links a[href^="#"]')];
  const sections = navLinks.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  const spy = () => {
    const y = window.scrollY + 120;
    let current = null;
    sections.forEach(sec => { if (sec.offsetTop <= y) current = sec.id; });
    navLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + current));
  };
  window.addEventListener('scroll', spy, { passive: true });
  spy();
  // External links written inline in data files (news, transfers) open in a new tab.
  document.querySelectorAll('a[href^="http"]:not([target])').forEach(a => {
    a.target = '_blank';
    a.rel = 'noopener';
  });
})();
