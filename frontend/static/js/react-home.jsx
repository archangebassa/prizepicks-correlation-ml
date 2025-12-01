function Input({label, id, value, onChange, type='text', placeholder='', error}){
  return (
    <div className="mb-3">
      <label htmlFor={id} className="block text-sm font-medium text-slate-200 mb-1">{label}</label>
      <input id={id} name={id} type={type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder}
        className={"w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100 border "+(error? 'border-rose-500 ring-2 ring-rose-500/20':'border-transparent focus:ring-2 focus:ring-cyan-400/30')}/>
      {error && <p className="mt-1 text-rose-400 text-sm">{error}</p>}
    </div>
  );
}

function LegRow({index, leg, onChange, onRemove}){
  return (
    <div className="grid grid-cols-12 gap-3 items-end">
      <div className="col-span-5">
        <label className="block text-sm text-slate-200 mb-1">Player</label>
        <input value={leg.player} onChange={e=>onChange(index,{...leg, player:e.target.value})} className="w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100" placeholder="Player name"/>
      </div>
      <div className="col-span-3">
        <label className="block text-sm text-slate-200 mb-1">Market</label>
        <select value={leg.market} onChange={e=>onChange(index,{...leg, market:e.target.value})} className="w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100">
          <option value="passing_yards">Passing</option>
          <option value="receiving_yards">Receiving</option>
          <option value="rushing_yards">Rushing</option>
        </select>
      </div>
      <div className="col-span-2">
        <label className="block text-sm text-slate-200 mb-1">p_hit</label>
        <input value={leg.p_hit} onChange={e=>onChange(index,{...leg, p_hit:e.target.value})} className="w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100" placeholder="0.65"/>
      </div>
      <div className="col-span-1">
        <label className="block text-sm text-slate-200 mb-1">Odds</label>
        <input value={leg.odds} onChange={e=>onChange(index,{...leg, odds:e.target.value})} className="w-full rounded-lg px-2 py-2 bg-slate-800 text-slate-100" placeholder="-110"/>
      </div>
      <div className="col-span-1">
        <button type="button" onClick={()=>onRemove(index)} className="text-rose-400 hover:text-rose-300">✕</button>
      </div>
    </div>
  );
}

function Summary({result, isParlay}){
  if(!result) return (<div className="text-slate-400">No calculation yet — fill and submit.</div>);
  if(isParlay){
    const jp = result.joint_probability_independent ?? result.joint_probability ?? null;
    const ev = result.combined_ev ?? result.combined_ev ?? null;
    return (
      <div className="space-y-3">
        <div className="text-slate-300 text-sm">Joint Probability</div>
        <div className="text-2xl font-extrabold text-white">{jp!==null? (jp*100).toFixed(1)+'%':'N/A'}</div>
        <div className="text-sm text-slate-400">Combined EV: {ev!==null? (ev>=0? '+':'')+Number(ev).toFixed(3) : 'N/A'}</div>
      </div>
    );
  }
  // single
  const p = Number(result.p_hit ?? result.probability ?? NaN);
  const implied = Number(result.implied_prob ?? result.implied_probability ?? NaN);
  const ev = Number(result.ev ?? NaN);
  const k = Number(result.kelly_fraction ?? result.kelly ?? 0);
  return (
    <div className="space-y-3">
      <div className="text-slate-300 text-sm">Probability</div>
      <div className="text-3xl font-extrabold text-white">{isNaN(p)? 'N/A' : (p*100).toFixed(1)+'%'} <span className="text-sm font-medium text-slate-400">(implied {isNaN(implied)? 'N/A' : (implied*100).toFixed(1)+'%'})</span></div>
      <div className="pt-2 border-t border-white/6"></div>
      <div className="flex justify-between items-center">
        <div>
          <div className="text-sm text-slate-400">Expected Value</div>
          <div className="text-lg font-semibold text-white">{isNaN(ev)? 'N/A' : (ev>=0? '+':'')+ev.toFixed(3)}</div>
        </div>
        <div>
          <div className="text-sm text-slate-400">Kelly</div>
          <div className="text-lg font-semibold text-white">{isNaN(k)? 'N/A' : k.toFixed(3)}</div>
        </div>
      </div>
    </div>
  );
}

function App(){
  const [isParlay, setIsParlay] = React.useState(false);
  const [legs, setLegs] = React.useState([{player:'', market:'passing_yards', p_hit:'', odds:''}]);
  const [errors, setErrors] = React.useState({});
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState(null);

  React.useEffect(()=>{ const el = document.querySelector('input'); if(el) el.focus(); },[]);

  function updateLeg(i, next){
    setLegs(prev=> prev.map((l,idx)=> idx===i? next: l));
  }
  function removeLeg(i){ setLegs(prev=> prev.filter((_,idx)=> idx!==i)); }
  function addLeg(){ setLegs(prev=> [...prev, {player:'', market:'passing_yards', p_hit:'', odds:''}]); }

  function validate(){
    const e = {};
    legs.forEach((l,i)=>{
      if(!l.player) e['player'+i] = 'Player required';
      if(isParlay){ if(l.p_hit==='' || isNaN(Number(l.p_hit))) e['ph'+i]='p_hit numeric'; }
      else { if(l.odds==='' || isNaN(Number(l.odds))) e['odds'+i]='Odds numeric'; }
    });
    setErrors(e); return Object.keys(e).length===0;
  }

  async function handleSubmit(ev){
    ev.preventDefault();
    if(!validate()) return;
    setLoading(true); setResult(null);
    try{
      if(isParlay && legs.length>1){
        const body = { legs: legs.map(l=>({player:l.player, market:l.market, p_hit: Number(l.p_hit), odds: Number(l.odds)})), correlation_matrix: null };
        const r = await fetch('/api/multi-leg',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const data = await r.json(); setResult(data);
      } else {
        // single using first leg
        const l = legs[0];
        const body = { sportsbook:'demo', market:l.market, player:l.player, projection: l.projection? Number(l.projection): null, odds: Number(l.odds||0), correlations: [] };
        const r = await fetch('/api/predict',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const data = await r.json(); setResult(data);
      }
    }catch(err){
      console.error(err); setErrors({form:'Network or server error'});
    }finally{ setLoading(false); }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2">
        <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Quick Bet Analyzer</h2>
              <p className="text-slate-400 mt-1">Form with support for single bets and parlays.</p>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-300">Parlay</label>
              <input type="checkbox" checked={isParlay} onChange={e=>setIsParlay(e.target.checked)} className="h-5 w-5"/>
            </div>
          </div>

          <form className="mt-6" onSubmit={handleSubmit}>
            <div className="space-y-3">
              {legs.map((leg, i)=> (
                <div key={i} className="p-3 bg-slate-900/30 rounded-lg border border-white/6">
                  <LegRow index={i} leg={leg} onChange={updateLeg} onRemove={removeLeg} />
                  {errors['player'+i] && <div className="text-rose-400 text-sm mt-1">{errors['player'+i]}</div>}
                  {isParlay && errors['ph'+i] && <div className="text-rose-400 text-sm mt-1">{errors['ph'+i]}</div>}
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3 mt-4">
              <button type="button" onClick={addLeg} className="px-4 py-2 rounded-lg bg-white/6 text-white">Add Leg</button>
              <button type="submit" className="inline-flex items-center gap-3 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-400 text-white font-semibold shadow" disabled={loading}>{loading? 'Working...': (isParlay? 'Analyze Parlay':'Analyze Bet')}</button>
              <button type="button" onClick={()=>{ setLegs([{player:'', market:'passing_yards', p_hit:'', odds:''}]); setErrors({}); setResult(null); }} className="px-4 py-2 rounded-lg border border-white/8 text-slate-300">Reset</button>
            </div>
            {errors.form && <div className="text-rose-400 mt-3">{errors.form}</div>}
          </form>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-800/50 p-4 rounded-lg border border-white/6">
            <h3 className="text-sm text-slate-400">Recent Insights</h3>
            <ul className="mt-2 text-sm text-slate-300 space-y-2">
              <li className="flex justify-between"><span>Calibration updated</span><span className="text-slate-400">2 days</span></li>
              <li className="flex justify-between"><span>New provider weights</span><span className="text-slate-400">1 week</span></li>
            </ul>
          </div>

          <div className="bg-slate-800/50 p-4 rounded-lg border border-white/6">
            <h3 className="text-sm text-slate-400">Tips</h3>
            <p className="text-slate-300 text-sm mt-2">Positive EV indicates a profitable edge over time — consider Kelly fraction to size bets conservatively.</p>
          </div>
        </div>
      </div>

      <aside className="bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg">
        <h4 className="text-slate-400 text-sm">Summary</h4>
        <div className="mt-4">
          <Summary result={result} isParlay={isParlay && legs.length>1}/>
        </div>
      </aside>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('app-root')).render(React.createElement(App));
const { useState, useEffect } = React;

function Input({label, id, value, onChange, type='text', placeholder='', error}){
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-slate-200 mb-1">{label}</label>
      <input id={id} name={id} type={type} value={value} onChange={e=>onChange(e.target.value)} placeholder={placeholder}
        className={"w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100 border "+(error? 'border-rose-500 ring-2 ring-rose-500/20':'border-transparent focus:ring-2 focus:ring-cyan-400/30')}/>
      {error && <p className="mt-1 text-rose-400 text-sm">{error}</p>}
    </div>
  );
}

function Summary({result}){
  if(!result) return (<div className="text-slate-400">No calculation yet — fill and submit.</div>);
  return (
    <div className="space-y-3">
      <div className="text-slate-300 text-sm">Probability</div>
      <div className="text-3xl font-extrabold text-white">{(result.p_hit*100).toFixed(1)}% <span className="text-sm font-medium text-slate-400">(implied {(result.implied_prob*100).toFixed(1)}%)</span></div>
      <div className="pt-2 border-t border-white/6"></div>
      <div className="flex justify-between items-center">
        <div>
          <div className="text-sm text-slate-400">Expected Value</div>
          <div className="text-lg font-semibold text-white">{result.ev >= 0 ? '+' : ''}{result.ev.toFixed(3)}</div>
        </div>
        <div>
          <div className="text-sm text-slate-400">Kelly</div>
          <div className="text-lg font-semibold text-white">{result.kelly_fraction.toFixed(3)}</div>
        </div>
      </div>
    </div>
  );
}

function App(){
  const [player, setPlayer] = useState('');
  const [market, setMarket] = useState('passing_yards');
  const [projection, setProjection] = useState('');
  const [odds, setOdds] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(()=>{
    // micro-interaction: focus player on mount
    const el = document.getElementById('player'); if(el) el.focus();
  },[]);

  function validate(){
    const e = {};
    if(!player) e.player = 'Please enter player name.';
    if(!projection || isNaN(Number(projection))) e.projection = 'Enter a numeric projection.';
    if(!odds || isNaN(Number(odds))) e.odds = 'Enter numeric odds (e.g. -110 or 150).';
    setErrors(e);
    return Object.keys(e).length===0;
  }

  async function handleSubmit(ev){
    ev.preventDefault();
    if(!validate()) return;
    setLoading(true); setResult(null);
    try{
      const body = {sportsbook:'demo', market, player, projection: Number(projection), odds: Number(odds), correlations: []};
      const r = await fetch('/api/predict', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
      const data = await r.json();
      setResult(data);
    }catch(err){
      setErrors({form:'Network or server error.'});
    }finally{setLoading(false)}
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2">
        <div className="bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg">
          <h2 className="text-2xl font-bold text-white">Quick Bet Analyzer</h2>
          <p className="text-slate-400 mt-1">Enter a market to see model probability, EV and suggested stake.</p>

          <form className="mt-6" onSubmit={handleSubmit} noValidate>
            <Input id="player" label="Player" value={player} onChange={setPlayer} error={errors.player} placeholder="e.g. Patrick Mahomes"/>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-1">Market</label>
                <select value={market} onChange={e=>setMarket(e.target.value)} className="w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100">
                  <option value="passing_yards">Passing Yards</option>
                  <option value="receiving_yards">Receiving Yards</option>
                  <option value="rushing_yards">Rushing Yards</option>
                </select>
              </div>
              <div>
                <Input id="projection" label="Projection" value={projection} onChange={setProjection} error={errors.projection} placeholder="e.g. 300"/>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input id="odds" label="Odds" value={odds} onChange={setOdds} error={errors.odds} placeholder="e.g. -110 or 150"/>
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-200 mb-1">Notes (optional)</label>
                <textarea className="w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100 border border-transparent focus:ring-2 focus:ring-cyan-400/30" placeholder="Anything to note..." rows="3"></textarea>
              </div>
            </div>

            {errors.form && <div className="text-rose-400 mb-3">{errors.form}</div>}

            <div className="flex items-center gap-3 mt-4">
              <button type="submit" className="inline-flex items-center gap-3 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-400 text-white font-semibold shadow hover:-translate-y-0.5 transition" disabled={loading}>
                {loading? 'Analyzing...' : 'Analyze Bet'}
              </button>
              <button type="button" onClick={()=>{setPlayer(''); setProjection(''); setOdds(''); setErrors({}); setResult(null);}} className="px-4 py-2 rounded-lg border border-white/8 text-slate-300">Reset</button>
            </div>
          </form>
        </div>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-800/50 p-4 rounded-lg border border-white/6">
            <h3 className="text-sm text-slate-400">Recent Insights</h3>
            <ul className="mt-2 text-sm text-slate-300 space-y-2">
              <li className="flex justify-between"><span>Calibration updated</span><span className="text-slate-400">2 days</span></li>
              <li className="flex justify-between"><span>New provider weights</span><span className="text-slate-400">1 week</span></li>
            </ul>
          </div>

          <div className="bg-slate-800/50 p-4 rounded-lg border border-white/6">
            <h3 className="text-sm text-slate-400">Tips</h3>
            <p className="text-slate-300 text-sm mt-2">Positive EV indicates a profitable edge over time — consider Kelly fraction to size bets conservatively.</p>
          </div>
        </div>
      </div>

      <aside className="bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg">
        <h4 className="text-slate-400 text-sm">Summary</h4>
        <div className="mt-4">
          <Summary result={result}/>
        </div>
      </aside>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('app-root')).render(React.createElement(App));
