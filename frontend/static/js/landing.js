// landing.js
document.addEventListener('DOMContentLoaded', () => {
  // scroll animations (with stagger)
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        const nodes = e.target.querySelectorAll('.feature, .card');
        if(nodes.length){
          nodes.forEach((n,i)=>{ setTimeout(()=> n.classList.add('show'), i*100); });
        } else {
          e.target.classList.add('show');
        }
      }
    });
  }, {threshold: 0.12});
  document.querySelectorAll('[data-animate], .features, .glass-cards').forEach(n => io.observe(n));

  // small hover glow effect for CTA buttons
  document.querySelectorAll('.btn.primary').forEach(btnEl => {
    btnEl.addEventListener('mouseenter', ()=> btnEl.style.boxShadow = '0 18px 60px rgba(6,95,205,0.18)');
    btnEl.addEventListener('mouseleave', ()=> btnEl.style.boxShadow = '');
  });
});
