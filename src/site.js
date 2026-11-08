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

// Bio box under About: size the text boxes to fit, and copy with a fallback for older browsers.
const fitBio = () => document.querySelectorAll(".bio-text").forEach((t) => {
  t.style.height = "auto";
  t.style.height = t.scrollHeight + 2 + "px";
});
document.querySelectorAll("details.bio").forEach((d) => d.addEventListener("toggle", fitBio));
window.addEventListener("resize", fitBio);
document.querySelectorAll(".bio-text").forEach((t) => t.addEventListener("focus", () => t.select()));
document.querySelectorAll("button.copy[data-copy]").forEach((b) => b.addEventListener("click", () => {
  const t = document.getElementById(b.dataset.copy);
  const done = () => { b.textContent = "Copied!"; setTimeout(() => { b.textContent = "Copy"; }, 1500); };
  const fallback = () => { t.focus(); t.select(); if (document.execCommand("copy")) done(); };
  if (navigator.clipboard) navigator.clipboard.writeText(t.value).then(done, fallback); else fallback();
}));

// /cv page: switch between the full CV and the resume (#resume in the URL opens the resume).
(() => {
  const versions = document.querySelectorAll(".cv-version");
  if (!versions.length) return;
  const show = (mode) => {
    versions.forEach((v) => { v.hidden = v.dataset.version !== mode; });
    document.querySelectorAll(".cv-toggle button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.mode === mode)));
    const dl = document.querySelector(".cv-download");
    if (dl) { dl.href = dl.dataset[mode]; dl.querySelector("span").textContent = dl.dataset[mode + "Label"]; }
  };
  document.querySelectorAll(".cv-toggle button").forEach((b) => b.addEventListener("click", () => {
    show(b.dataset.mode);
    history.replaceState(null, "", b.dataset.mode === "resume" ? "#resume" : location.pathname);
  }));
  show(location.hash === "#resume" ? "resume" : "cv");
})();
