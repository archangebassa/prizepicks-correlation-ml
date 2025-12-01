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
    React.createElement('div', {className: 'grid grid-cols-12 gap-3 items-end'},
      React.createElement('div', {className: 'col-span-5'},
        React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Player'),
        React.createElement('input', {value: leg.player, onChange: e => onChange(index, {...leg, player: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100', placeholder: 'Player name'})
      ),
      React.createElement('div', {className: 'col-span-3'},
        React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Market'),
        React.createElement('select', {value: leg.market, onChange: e => onChange(index, {...leg, market: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100'},
          React.createElement('option', {value: 'passing_yards'}, 'Passing'),
          React.createElement('option', {value: 'receiving_yards'}, 'Receiving'),
          React.createElement('option', {value: 'rushing_yards'}, 'Rushing')
        )
      ),
      React.createElement('div', {className: 'col-span-2'},
        React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'p_hit'),
        React.createElement('input', {value: leg.p_hit, onChange: e => onChange(index, {...leg, p_hit: e.target.value}), className: 'w-full rounded-lg px-3 py-2 bg-slate-800 text-slate-100', placeholder: '0.65'})
      ),
      React.createElement('div', {className: 'col-span-1'},
        React.createElement('label', {className: 'block text-sm text-slate-200 mb-1'}, 'Odds'),
        React.createElement('input', {value: leg.odds, onChange: e => onChange(index, {...leg, odds: e.target.value}), className: 'w-full rounded-lg px-2 py-2 bg-slate-800 text-slate-100', placeholder: '-110'})
      ),
      React.createElement('div', {className: 'col-span-1'},
        React.createElement('button', {type: 'button', onClick: () => onRemove(index), className: 'text-rose-400 hover:text-rose-300'}, '✕')
      )
    );

  const Summary = ({result, isParlay}) => {
    if(!result) return React.createElement('div', {className: 'text-slate-400'}, 'No calculation yet — fill and submit.');
    if(isParlay){
      const jp = result.joint_probability_independent ?? result.joint_probability ?? null;
      const ev = result.combined_ev ?? null;
      return React.createElement('div', {className: 'space-y-3'},
        React.createElement('div', {className: 'text-slate-300 text-sm'}, 'Joint Probability'),
        React.createElement('div', {className: 'text-2xl font-extrabold text-white'}, jp!==null? (jp*100).toFixed(1)+'%':'N/A'),
        React.createElement('div', {className: 'text-sm text-slate-400'}, 'Combined EV: ' + (ev!==null? (ev>=0? '+':'')+Number(ev).toFixed(3) : 'N/A'))
      );
    }
    const p = Number(result.p_hit ?? result.probability ?? NaN);
    const implied = Number(result.implied_prob ?? result.implied_probability ?? NaN);
    const ev = Number(result.ev ?? NaN);
    const k = Number(result.kelly_fraction ?? result.kelly ?? 0);
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
    const [legs, setLegs] = React.useState([{player:'', market:'passing_yards', p_hit:'', odds:''}]);
    const [errors, setErrors] = React.useState({});
    const [loading, setLoading] = React.useState(false);
    const [result, setResult] = React.useState(null);

    React.useEffect(()=>{ const el = document.querySelector('input'); if(el) el.focus(); },[]);

    function updateLeg(i, next){ setLegs(prev=> prev.map((l,idx)=> idx===i? next: l)); }
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
          const l = legs[0];
          const body = { sportsbook:'demo', market:l.market, player:l.player, projection: l.projection? Number(l.projection): null, odds: Number(l.odds||0), correlations: [] };
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
              React.createElement('button', {type: 'button', onClick: ()=>{ setLegs([{player:'', market:'passing_yards', p_hit:'', odds:''}]); setErrors({}); setResult(null); }, className: 'px-4 py-2 rounded-lg border border-white/8 text-slate-300'}, 'Reset')
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
        )
      )
    );
  }

  ReactDOM.createRoot(document.getElementById('app-root')).render(React.createElement(App));
})();
