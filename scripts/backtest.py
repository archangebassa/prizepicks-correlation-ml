import pandas as pd
import numpy as np
from pathlib import Path
from .metrics import compute_metrics, bootstrap_ci


def ev_and_roi(df: pd.DataFrame, p_col='p_hit', outcome_col='outcome', payout=2.0):
    df = df.copy()
    df = df.dropna(subset=[p_col, outcome_col])
    df['ev'] = df[p_col] * (payout - 1) - (1 - df[p_col])
    total_ev = df['ev'].sum()
    roi = total_ev / len(df) if len(df) > 0 else 0.0
    return {'n': len(df), 'total_ev': float(total_ev), 'roi_per_bet': float(roi)}


def kelly_fraction(p, b):
    b = float(b)
    p = float(p)
    denom = b
    if denom == 0:
        return 0.0
    f = (p * (b + 1) - 1) / denom
    return max(0.0, f)


def simulate_bankroll(df: pd.DataFrame, stake_strategy: str = 'fixed', stake_val: float = 1.0, p_col='p_hit', payout=2.0):
    """Simulate bankroll evolution given a stake strategy.
    stake_strategy: 'fixed' stakes stake_val per bet, 'kelly' stakes fraction of bankroll
    """
    df = df.dropna(subset=[p_col]).copy()
    bankroll = 1.0
    history = []
    for _, row in df.iterrows():
        p = float(row[p_col])
        if stake_strategy == 'fixed':
            stake = stake_val
        elif stake_strategy == 'kelly':
            f = kelly_fraction(p, payout - 1)
            stake = bankroll * f
        else:
            stake = stake_val
        # cap stake to bankroll
        stake = min(stake, bankroll)
        # outcome may be missing in simulation; assume row['outcome'] is 0/1
        outcome = float(row.get('outcome', 0))
        if outcome:
            bankroll = bankroll + stake * (payout - 1)
        else:
            bankroll = bankroll - stake
        history.append(bankroll)
        if bankroll <= 0:
            break
    return history


def run_backtest(data, p_col='p_hit', outcome_col='outcome', payout=2.0, n_bootstrap: int = 500):
    """Run backtest on historical data.
    Args:
        data: Either a path to a CSV file or a pandas DataFrame
        p_col: Column name for predicted probabilities
        outcome_col: Column name for actual outcomes (0/1)
        payout: Payout multiplier (e.g., 2.0 means double)
        n_bootstrap: Number of bootstrap samples for CI
    """
    if isinstance(data, (str, Path)):
        p = Path(data)
        if not p.exists():
            raise FileNotFoundError(data)
        df = pd.read_csv(p)
    else:
        df = data
    metrics = compute_metrics(df[outcome_col], df[p_col])
    ev = ev_and_roi(df, p_col=p_col, outcome_col=outcome_col, payout=payout)
    # kelly suggestion
    df['kelly'] = df[p_col].apply(lambda prob: kelly_fraction(prob, payout - 1))
    # bootstrap CI for ROI (using mean EV per bet)
    def mean_ev(y, p):
        # y here is outcomes, p is predicted probs
        evs = p * (payout - 1) - (1 - p)
        return np.nanmean(evs)

    median, lo, hi = bootstrap_ci(lambda y, p: mean_ev(y, p), df[outcome_col].values, df[p_col].values, n_bootstrap=n_bootstrap)
    return {'metrics': metrics, 'ev_summary': ev, 'kelly_median': float(df['kelly'].median()), 'ev_bootstrap_median': median, 'ev_bootstrap_lo': lo, 'ev_bootstrap_hi': hi}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True)
    parser.add_argument('--pcol', default='p_hit')
    parser.add_argument('--outcome', default='outcome')
    parser.add_argument('--payout', default=2.0, type=float)
    parser.add_argument('--boots', default=500, type=int)
    args = parser.parse_args()
    res = run_backtest(args.csv, p_col=args.pcol, outcome_col=args.outcome, payout=args.payout, n_bootstrap=args.boots)
    print(res)
