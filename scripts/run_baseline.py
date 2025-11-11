"""Run a tiny baseline backtest on the sample dataset and produce baseline metrics report.

This script uses the existing `scripts.backtest_nfl` pipeline to run a small baseline
backtest and then writes a short `reports/baseline_metrics.md` file with MAE / R^2 and
qualitative takeaways.
"""
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timezone

import scripts.backtest_nfl as bn


def run_baseline(sample_path: str = 'data/samples/nfl_sample.csv', market: str = 'passing_yards'):
    sample = pd.read_csv(sample_path, parse_dates=['Date'])

    # Use a short date tag for baseline sample
    date_tag = 'baseline_sample'
    out_dir = Path('data/cache/backtests')
    out_dir.mkdir(parents=True, exist_ok=True)

    # Prepare df similar to load_market_data expectations
    df = sample.copy()
    # Ensure projection/actual mapping for market
    if market == 'passing_yards':
        df['projection'] = df['QB_PassYds']
        df['actual'] = df['QB_PassYds_actual']
    elif market == 'receiving_yards':
        df['projection'] = df['WR_RecYds']
        df['actual'] = df['WR_RecYds_actual']
    else:
        df['projection'] = df['QB_PassYds']
        df['actual'] = df['QB_PassYds_actual']

    # Create p_hit and outcome if missing
    if 'p_hit' not in df.columns:
        std = df['projection'].std() if df['projection'].std() > 0 else 1.0
        df['p_hit'] = 0.5 + (df['projection'] - df['projection'].mean()) / (2 * std + 1e-6)
        df['p_hit'] = df['p_hit'].clip(0.05, 0.95).fillna(0.5)
    if 'outcome' not in df.columns:
        df['outcome'] = (df['actual'] >= df['projection']).astype(int)

    # Run the market backtest via existing pipeline which will save CSV/JSON/plots
    results = bn.run_market_backtest(df, market=market, out_dir=out_dir, date_tag=date_tag, n_bootstrap=200)

    # Load the saved metrics JSON for the market
    metrics_path = out_dir / f"{date_tag}_{market}.json"
    metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            try:
                metrics = json.load(f)
            except Exception:
                metrics = {}

    # Create simple baseline report
    reports_dir = Path('reports')
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / 'baseline_metrics.md'

    mae = metrics.get('metrics', {}).get('mae') if isinstance(metrics.get('metrics'), dict) else None
    rmse = metrics.get('metrics', {}).get('rmse') if isinstance(metrics.get('metrics'), dict) else None
    brier = metrics.get('provider_metrics', {}) if isinstance(metrics.get('provider_metrics'), dict) else None

    with open(report_path, 'w') as r:
        r.write(f"# Baseline Metrics Report\n\n")
        r.write(f"**Date:** {datetime.now(timezone.utc).isoformat()}\n\n")
        r.write(f"## Summary (market = {market})\n\n")
        if mae is not None:
            r.write(f"- MAE: {mae}\n")
        if rmse is not None:
            r.write(f"- RMSE: {rmse}\n")
        if brier:
            r.write(f"- Provider-level Brier scores available in backtest JSON outputs.\n")
        r.write("\n## Quick takeaways\n\n")
        r.write("- Baseline shows prediction errors on the order of the MAE/RMSE above.\n")
        r.write("- Correlation-aware simulations (see simulation_demo.py) can shift expected value for multi-pick entries when player outcomes are dependent.\n")

    print(f"Baseline run complete. Artifacts written to {out_dir}. Report: {report_path}")


if __name__ == '__main__':
    run_baseline()
