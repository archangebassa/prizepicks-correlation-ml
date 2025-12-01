// modern-home.js
// Renders a premium-looking homepage component using Preact + htm (loaded via CDN in index.html)
(function(){
  if (!window.preact || !window.htm) return;
  const { h, render, Component } = window.preact;
  const html = window.htm.bind(h);

  const IconShield = () => html`<svg class="w-10 h-10 text-cyan-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2l7 4v6c0 5-7 9-7 9s-7-4-7-9V6l7-4z"/></svg>`;
  const IconParlay = () => html`<svg class="w-10 h-10 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 7h6l3 5 4-8 5 10"/></svg>`;
  const IconCal = () => html`<svg class="w-10 h-10 text-rose-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3"/></svg>`;

  class ModernHome extends Component {
    componentDidMount(){
      // small entrance animation for cards
      const cards = document.querySelectorAll('.mh-card');
      cards.forEach((c,i)=> setTimeout(()=> c.classList.add('mh-show'), 150 + i*120));
    }

    render(){
      return html`
        <div class="w-full max-w-7xl mx-auto px-6 lg:px-8">
          <section class="relative overflow-hidden pt-12 pb-16">
            <div class="absolute inset-0 -z-10 bg-gradient-to-br from-indigo-900 via-slate-900 to-slate-800 opacity-95" style="background-size:200% 200%; animation: bgShift 12s ease-in-out infinite;"></div>

            <div class="text-center">
              <h1 class="text-white font-extrabold leading-tight text-3xl md:text-5xl lg:text-[3.5rem]">Insightful Bets, Smarter Decisions</h1>
              <p class="mt-4 text-slate-300 max-w-2xl mx-auto">Data-driven probabilities with calibration-adjusted confidence — optimized for quick, confident decisions.</p>

              <div class="mt-8 flex items-center justify-center gap-4">
                <a class="inline-flex items-center gap-3 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-400 text-white font-semibold shadow-xl transform transition hover:-translate-y-1 hover:shadow-2xl" href="/">Try Demo</a>
              </div>
            </div>

            <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div class="mh-card rounded-2xl bg-white/4 backdrop-blur-md p-6 shadow-lg border border-white/6 transform transition duration-700 opacity-0">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-white/6">${IconShield()}</div>
                  <div>
                    <h3 class="text-white font-semibold">Single Bet Analysis</h3>
                    <p class="text-slate-300 mt-1">Instant probability, EV, and Kelly recommendations.</p>
                  </div>
                </div>
              </div>

              <div class="mh-card rounded-2xl bg-white/4 backdrop-blur-md p-6 shadow-lg border border-white/6 transform transition duration-700 opacity-0">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-white/6">${IconParlay()}</div>
                  <div>
                    <h3 class="text-white font-semibold">Parlay Support</h3>
                    <p class="text-slate-300 mt-1">Combine legs,<br/>see joint probability and combined EV.</p>
                  </div>
                </div>
              </div>

              <div class="mh-card rounded-2xl bg-white/4 backdrop-blur-md p-6 shadow-lg border border-white/6 transform transition duration-700 opacity-0">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-white/6">${IconCal()}</div>
                  <div>
                    <h3 class="text-white font-semibold">Provider Calibration</h3>
                    <p class="text-slate-300 mt-1">Adjust model confidence using provider Brier scores.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      `;
    }
  }

  // mount
  const mount = document.getElementById('app-root');
  if (mount) render(html`<${ModernHome}/>`, mount);

  // small CSS keyframes injected for gradient
  const style = document.createElement('style');
  style.innerHTML = `@keyframes bgShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}} .mh-show{opacity:1; transform:translateY(0) scale(1)} .mh-card{transform:translateY(10px) scale(.995)}`;
  document.head.appendChild(style);
})();
