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
