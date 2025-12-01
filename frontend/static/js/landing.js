// landing.js
document.addEventListener('DOMContentLoaded', () => {
  // Theme toggle
  const btn = document.getElementById('theme-toggle');
  function applyTheme(name){
    document.documentElement.classList.remove('theme-dark','theme-light','theme-system');
    if (name === 'dark') document.documentElement.classList.add('theme-dark');
    if (name === 'light') document.documentElement.classList.add('theme-light');
    localStorage.setItem('pp-theme', name);
  }
  btn?.addEventListener('click', ()=> {
    const cur = localStorage.getItem('pp-theme') || 'system';
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  });
  // Restore theme
  const stored = localStorage.getItem('pp-theme');
  if(stored) applyTheme(stored);

  // scroll animations
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting) e.target.classList.add('show');
    });
  }, {threshold: 0.15});
  document.querySelectorAll('[data-animate]').forEach(n => io.observe(n));
});
