// Plain React app wrapped in IIFE to avoid module-level const redeclarations
(function() {
  const Input = ({label, id, value, onChange, type='text', placeholder='', error}) => 
    React.createElement('div', {className: 'mb-3'},
      React.createElement('label', {htmlFor: id, className: 'block text-sm font-medium text-slate-200 mb-1'}, label),
      React.createElement('input', {
        id, name: id, type, value, onChange: e => onChange(e.target.value), placeholder,
        className: 'w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100 border ' + (error ? 'border-rose-500 ring-2 ring-rose-500/20' : 'border-transparent focus:ring-2 focus:ring-cyan-400/30')
      }),
      error && React.createElement('p', {className: 'mt-1 text-rose-400 text-sm'}, error)
    );

  const LegRow = ({index, leg, onChange, onRemove}) =>
    React.createElement('div', {className: 'space-y-3'},
      React.createElement('div', {className: 'grid grid-cols-1 md:grid-cols-3 gap-3'},
        React.createElement('div', {},
          React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Player'),
          React.createElement('input', {value: leg.player, onChange: e => onChange(index, {...leg, player: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100', placeholder: 'e.g. Patrick Mahomes'})
        ),
        React.createElement('div', {},
          React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Market'),
          React.createElement('select', {value: leg.market, onChange: e => onChange(index, {...leg, market: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100'},
            React.createElement('option', {value: 'passing_yards'}, 'Passing Yards'),
            React.createElement('option', {value: 'receiving_yards'}, 'Receiving Yards'),
            React.createElement('option', {value: 'rushing_yards'}, 'Rushing Yards')
          )
        ),
        React.createElement('div', {},
          React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Odds'),
          React.createElement('input', {value: leg.odds, onChange: e => onChange(index, {...leg, odds: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100', placeholder: 'e.g. -110'})
        )
      ),
      React.createElement('div', {className: 'grid grid-cols-1 md:grid-cols-2 gap-3 bg-slate-900/40 p-3 rounded-lg border border-white/3'},
        React.createElement('div', {},
          React.createElement('label', {className: 'block text-xs text-slate-300 mb-1'}, 'Projection'),
          React.createElement('input', {value: leg.projection, onChange: e => onChange(index, {...leg, projection: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100 text-sm', placeholder: 'Model forecast'})
        ),
        React.createElement('div', {},
          React.createElement('label', {className: 'block text-xs text-slate-300 mb-1'}, 'Actual/Line'),
          React.createElement('input', {value: leg.actual_or_estimate, onChange: e => onChange(index, {...leg, actual_or_estimate: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100 text-sm', placeholder: 'Sportsbook line'})
        )
      ),
      React.createElement('div', {className: 'flex items-center justify-between'},
        React.createElement('div', {className: 'text-xs text-slate-400'}, 'Probability: ' + (leg.projection && leg.actual_or_estimate ? ((Number(leg.actual_or_estimate) / (Number(leg.projection) + Number(leg.actual_or_estimate))) * 100).toFixed(1) + '%' : 'N/A')),
        React.createElement('button', {type: 'button', onClick: () => onRemove(index), className: 'text-rose-400 hover:text-rose-300 text-sm'}, '✕ Remove')
      )
    );

  const Summary = ({result, isParlay}) => {
    if(!result) return React.createElement('div', {className: 'text-slate-400'}, 'No calculation yet — fill and submit.');
    // Helper to safely read nested values
    const get = (obj, path, fallback=null) => {
      try{
        return path.split('.').reduce((o,k)=> (o && k in o) ? o[k] : undefined, obj) ?? fallback;
      }catch(e){ return fallback; }
    };

    if(isParlay){
      // API may return combined values under `multi_leg` or at root
      const multi = result.multi_leg ?? result.multiLeg ?? result;
      const jp = get(multi, 'joint_probability_independent', get(multi, 'joint_probability', null));
      const ev = get(multi, 'combined_ev', get(multi, 'combined_ev_pct', null));
      const odds = get(multi, 'combined_decimal_odds', null);
      return React.createElement('div', {className: 'space-y-3'},
        React.createElement('div', {className: 'text-slate-300 text-sm'}, 'Joint Probability'),
        React.createElement('div', {className: 'text-2xl font-extrabold text-white'}, jp!==null? (jp*100).toFixed(1)+'%':'N/A'),
        React.createElement('div', {className: 'text-sm text-slate-400'}, 'Combined EV: ' + (ev!==null? (ev>=0? '+':'')+Number(ev).toFixed(3) : 'N/A')),
        React.createElement('div', {className: 'text-sm text-slate-400'}, 'Combined Odds: ' + (odds!==null? Number(odds).toFixed(2) : 'N/A'))
      );
    }

    // Single bet: prediction fields usually live under result.prediction and valuation under result.valuation
    const pred = result.prediction ?? result;
    const val = result.valuation ?? result;
    const p = Number(get(pred, 'p_hit', get(pred, 'probability', get(result, 'p_hit', NaN))));
    const implied = Number(get(pred, 'implied_prob', get(pred, 'implied_probability', get(result, 'implied_prob', NaN))));
    const ev = Number(get(val, 'ev', get(result, 'ev', NaN)));
    const k = Number(get(val, 'kelly_fraction', get(result, 'kelly_fraction', get(result, 'kelly', 0))));

    return React.createElement('div', {className: 'space-y-3'},
      React.createElement('div', {className: 'text-slate-300 text-sm'}, 'Probability'),
      React.createElement('div', {className: 'text-3xl font-extrabold text-white'}, (isNaN(p)? 'N/A' : (p*100).toFixed(1)+'%') + ' ' + React.createElement('span', {className: 'text-sm font-medium text-slate-400'}, '(implied ' + (isNaN(implied)? 'N/A' : (implied*100).toFixed(1)+'%') + ')')),
      React.createElement('div', {className: 'pt-2 border-t border-white/6'}),
      React.createElement('div', {className: 'flex justify-between items-center'},
        React.createElement('div', {},
          React.createElement('div', {className: 'text-sm text-slate-400'}, 'Expected Value'),
          React.createElement('div', {className: 'text-lg font-semibold text-white'}, isNaN(ev)? 'N/A' : (ev>=0? '+':'')+ev.toFixed(3))
        ),
        React.createElement('div', {},
          React.createElement('div', {className: 'text-sm text-slate-400'}, 'Kelly'),
          React.createElement('div', {className: 'text-lg font-semibold text-white'}, isNaN(k)? 'N/A' : k.toFixed(3))
        )
      )
    );
  };

  function App(){
    const [isParlay, setIsParlay] = React.useState(false);
    const [sportsbook, setSportsbook] = React.useState('draftkings');
    const [legs, setLegs] = React.useState([{player:'', market:'passing_yards', projection:'', actual_or_estimate:'', odds:''}]);
    const [errors, setErrors] = React.useState({});
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(null);

    React.useEffect(()=>{ const el = document.querySelector('input'); if(el) el.focus(); },[]);

    function updateLeg(i, next){ setLegs(prev=> prev.map((l,idx)=> idx===i? next: l)); }
    function removeLeg(i){ setLegs(prev=> prev.filter((_,idx)=> idx!==i)); }
    function addLeg(){ setLegs(prev=> [...prev, {player:'', market:'passing_yards', projection:'', actual_or_estimate:'', odds:''}]); }

    function validate(){
      const e = {};
      legs.forEach((l,i)=>{
        if(!l.player) e['player'+i] = 'Player required';
        if(!l.market) e['market'+i] = 'Market required';
        if(l.projection==='' || isNaN(Number(l.projection))) e['proj'+i]='Projection required';
        if(l.actual_or_estimate==='' || isNaN(Number(l.actual_or_estimate))) e['actual'+i]='Actual/Line required';
        if(l.odds==='' || isNaN(Number(l.odds))) e['odds'+i]='Odds required';
      });
      setErrors(e); return Object.keys(e).length===0;
    }

    async function handleSubmit(ev){
      ev.preventDefault();
      if(!validate()) return;
      setLoading(true); setResult(null);
      try{
        if(isParlay && legs.length>1){
          const body = { 
            legs: legs.map(l=>({
              player:l.player, 
              market:l.market, 
              projection: Number(l.projection),
              actual_or_estimate: Number(l.actual_or_estimate),
              odds: Number(l.odds)
            })), 
            correlation_matrix: null 
          };
          const r = await fetch('/api/multi-leg',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
          const data = await r.json(); setResult(data);
        } else {
          const l = legs[0];
          const body = { sportsbook: sportsbook, market:l.market, player:l.player, projection: Number(l.projection), actual_or_estimate: Number(l.actual_or_estimate), odds: Number(l.odds), correlations: [] };
          const r = await fetch('/api/predict',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
          const data = await r.json(); setResult(data);
        }
      }catch(err){
        console.error(err); setErrors({form:'Network or server error'});
      }finally{ setLoading(false); }
    }

    return React.createElement('div', {className: 'grid grid-cols-1 lg:grid-cols-3 gap-8'},
      React.createElement('div', {className: 'lg:col-span-2'},
        React.createElement('div', {className: 'bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg'},
          React.createElement('div', {className: 'flex items-center justify-between'},
            React.createElement('div', {},
              React.createElement('h2', {className: 'text-2xl font-bold text-white'}, 'Quick Bet Analyzer'),
              React.createElement('p', {className: 'text-slate-400 mt-1'}, 'Form with support for single bets and parlays.')
            ),
            React.createElement('div', {className: 'flex items-center gap-3'},
              React.createElement('label', {className: 'text-sm text-slate-300'}, 'Parlay'),
              React.createElement('input', {type: 'checkbox', checked: isParlay, onChange: e => setIsParlay(e.target.checked), className: 'h-5 w-5'})
            )
          ),
          React.createElement('form', {className: 'mt-6', onSubmit: handleSubmit},
            React.createElement('div', {className: 'mb-6 p-4 bg-cyan-900/30 border border-cyan-500/20 rounded-lg'},
              React.createElement('label', {className: 'block text-sm font-medium text-cyan-300 mb-2'}, 'Sportsbook'),
              React.createElement('select', {value: sportsbook, onChange: e => setSportsbook(e.target.value), className: 'w-full rounded-lg px-4 py-2 bg-slate-800 text-slate-100 border border-cyan-500/20'},
                React.createElement('option', {value: 'draftkings'}, 'DraftKings'),
                React.createElement('option', {value: 'fanduel'}, 'FanDuel'),
                React.createElement('option', {value: 'betmgm'}, 'BetMGM'),
                React.createElement('option', {value: 'caesars'}, 'Caesars'),
                React.createElement('option', {value: 'demo'}, 'Demo (No Real Data)')
              )
            ),
            React.createElement('div', {className: 'space-y-3'},
              legs.map((leg, i)=> 
                React.createElement('div', {key: i, className: 'p-3 bg-slate-900/30 rounded-lg border border-white/6'},
                  LegRow({index: i, leg: leg, onChange: updateLeg, onRemove: removeLeg}),
                  errors['player'+i] && React.createElement('div', {className: 'text-rose-400 text-sm mt-1'}, errors['player'+i]),
                  isParlay && errors['ph'+i] && React.createElement('div', {className: 'text-rose-400 text-sm mt-1'}, errors['ph'+i])
                )
              )
            ),
            React.createElement('div', {className: 'flex items-center gap-3 mt-4'},
              React.createElement('button', {type: 'button', onClick: addLeg, className: 'px-4 py-2 rounded-lg bg-white/6 text-white'}, 'Add Leg'),
              React.createElement('button', {type: 'submit', className: 'inline-flex items-center gap-3 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-400 text-white font-semibold shadow', disabled: loading}, loading? 'Working...': (isParlay? 'Analyze Parlay':'Analyze Bet')),
              React.createElement('button', {type: 'button', onClick: ()=>{ setLegs([{player:'', market:'passing_yards', projection:'', actual_or_estimate:'', odds:''}]); setErrors({}); setResult(null); }, className: 'px-4 py-2 rounded-lg border border-white/8 text-slate-300'}, 'Reset')
            ),
            errors.form && React.createElement('div', {className: 'text-rose-400 mt-3'}, errors.form)
          )
        ),
        React.createElement('div', {className: 'mt-6 grid grid-cols-1 md:grid-cols-2 gap-4'},
          React.createElement('div', {className: 'bg-slate-800/50 p-4 rounded-lg border border-white/6'},
            React.createElement('h3', {className: 'text-sm text-slate-400'}, 'Recent Insights'),
            React.createElement('ul', {className: 'mt-2 text-sm text-slate-300 space-y-2'},
              React.createElement('li', {className: 'flex justify-between'}, React.createElement('span', {}, 'Calibration updated'), React.createElement('span', {className: 'text-slate-400'}, '2 days')),
              React.createElement('li', {className: 'flex justify-between'}, React.createElement('span', {}, 'New provider weights'), React.createElement('span', {className: 'text-slate-400'}, '1 week'))
            )
          ),
          React.createElement('div', {className: 'bg-slate-800/50 p-4 rounded-lg border border-white/6'},
            React.createElement('h3', {className: 'text-sm text-slate-400'}, 'Tips'),
            React.createElement('p', {className: 'text-slate-300 text-sm mt-2'}, 'Positive EV indicates a profitable edge over time — consider Kelly fraction to size bets conservatively.')
          )
        )
      ),
      React.createElement('aside', {className: 'bg-slate-800/60 border border-white/6 rounded-2xl p-6 shadow-lg'},
        React.createElement('h4', {className: 'text-slate-400 text-sm'}, 'Summary'),
        React.createElement('div', {className: 'mt-4'},
          Summary({result: result, isParlay: isParlay && legs.length>1})
        ),
        React.createElement('div', {className: 'mt-6 pt-6 border-t border-white/6 space-y-3'},
          React.createElement('h4', {className: 'text-sm font-semibold text-cyan-300'}, 'How Confidence Works'),
          React.createElement('p', {className: 'text-xs text-slate-300 leading-relaxed'}, 'Confidence measures how certain the model is about a prediction based on historical data and calibration. Higher confidence = model is very certain (whether the bet is good or bad). Lower confidence = model has less certainty in the prediction, which can indicate higher uncertainty and potentially better value if odds are right.')
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById('app-root')).render(React.createElement(App));
})();
