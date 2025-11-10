"""End-to-end backtest script for NFL player props.

This script implements the backtest pipeline for NFL markets:
1. Loads historical data for the specified date range
2. Runs backtests by market (passing yards, receiving yards, etc.)
3. Generates calibration curves and provider-level metrics
4. Saves results to data/cache/backtests/{YYYY-MM-DD}_{market}.json

Example usage:
    python -m scripts.backtest_nfl --start 2024-09-01 --end 2024-12-31
    python -m scripts.backtest_nfl --start 2024-09-01 --end 2024-12-31 --market passing_yards
    python -m scripts.backtest_nfl --tiny  # runs on small sample for testing
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import pandas as pd

from .backtest import run_backtest
from .metrics import compute_metrics, calibration_by_bin
from .demo_backtest import plot_calibration, plot_roc
from .provider_metrics import compute_provider_metrics, plot_provider_calibration


MARKETS = [
    'passing_yards',
    'receiving_yards',
    'rushing_yards',
    # Add more markets as needed
]

def load_market_data(start_date: str, end_date: str, market: str, data_dir: Path = Path('data/cache')) -> pd.DataFrame:
    """Load and prepare historical data for a specific market and date range."""
    # TODO: Implement data loading from cached CSVs
    # This should use the existing merged_eval.csv format but filter by date range
    df = pd.read_csv(data_dir / 'merged_eval.csv', parse_dates=['Date'])
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    if market == 'passing_yards':
        df['projection'] = df['QB_PassYds']
        df['actual'] = df['QB_PassYds_actual']
    elif market == 'receiving_yards':
        df['projection'] = df['WR_RecYds']
        df['actual'] = df['WR_RecYds_actual']
    else:
        # Default: use first available projection/actual columns
        if 'QB_PassYds' in df.columns:
            df['projection'] = df['QB_PassYds']
            df['actual'] = df['QB_PassYds_actual']
        else:
            raise ValueError(f"No data available for market: {market}")
    
    # Generate synthetic p_hit and outcome if not present
    if 'p_hit' not in df.columns:
        # Simple heuristic: probability based on projection
        std = df['projection'].std() if df['projection'].std() > 0 else 1.0
        df['p_hit'] = 0.5 + (df['projection'] - df['projection'].mean()) / (2 * std + 1e-6)
        df['p_hit'] = df['p_hit'].clip(0.1, 0.9)
    
    # Fill any remaining NaN values
    df['p_hit'] = df['p_hit'].fillna(0.5)
    
    if 'outcome' not in df.columns:
        # Binary outcome: actual >= projection
        df['outcome'] = (df['actual'] >= df['projection']).astype(int)
    
    if 'provider' not in df.columns:
        # Assign fake providers for demo
        providers = ['DraftKings', 'FanDuel', 'BetMGM', 'PointsBet']
        df['provider'] = [providers[i % len(providers)] for i in range(len(df))]
    
    return df

def run_market_backtest(
    df: pd.DataFrame,
    market: str,
    out_dir: Path,
    date_tag: str,
    n_bootstrap: int = 500
) -> dict:
    """Run backtest for a specific market and save results."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Save market data for traceability
    market_csv = out_dir / f'{date_tag}_{market}.csv'
    df.to_csv(market_csv, index=False)
    
    # Run core backtest
    results = run_backtest(
        df,  # Pass DataFrame directly
        p_col='p_hit',  # Probability column
        outcome_col='outcome',  # Binary outcome column
        payout=2.0,  # Standard prize picks payout
        n_bootstrap=n_bootstrap
    )
    
    # Add market-specific calibration plots
    plot_path = out_dir / f'{date_tag}_{market}_calibration.png'
    plot_calibration(df, plot_path)
    
    roc_path = out_dir / f'{date_tag}_{market}_roc.png'
    plot_roc(df, roc_path)
    
    # Generate provider-level metrics and plots
    provider_results = plot_provider_calibration(
        df,
        out_dir=out_dir,
        prefix=f'{date_tag}_{market}_',
        provider_col='provider',
        p_col='p_hit',
        outcome_col='outcome'
    )
    
    # Combine core and provider-specific results
    results.update({
        'provider_metrics': provider_results['metrics'],
        'plots': {
            'calibration': str(plot_path),
            'roc': str(roc_path),
            'provider_calibration': provider_results['calibration_plot'],
            'provider_brier': provider_results['brier_plot']
        }
    })
    
    # Save detailed results
    results_file = out_dir / f'{date_tag}_{market}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main(
    start_date: str,
    end_date: str,
    market: str = None,
    tiny: bool = False,
    out_dir: str = 'data/cache/backtests'
):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # For tiny mode, use a small recent sample
    if tiny:
        start_date = '2024-12-01'
        end_date = '2024-12-31'
    
    date_tag = f"{start_date}_{end_date}"
    markets_to_run = [market] if market else MARKETS
    
    results = {}
    for mkt in markets_to_run:
        print(f"Running backtest for {mkt}")
        df = load_market_data(start_date, end_date, mkt)
        if len(df) == 0:
            print(f"No data found for {mkt} between {start_date} and {end_date}")
            continue
            
        results[mkt] = run_market_backtest(
            df,
            market=mkt,
            out_dir=out_path,
            date_tag=date_tag
        )
    
    # Save combined results
    summary_file = out_path / f"{date_tag}_summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'start_date': start_date,
            'end_date': end_date,
            'tiny_mode': tiny,
            'results': results
        }, f, indent=2)
    
    print(f"Wrote backtest results to {out_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--market', choices=MARKETS, help='Specific market to backtest')
    parser.add_argument('--tiny', action='store_true', help='Run on small sample for testing')
    parser.add_argument('--out', default='data/cache/backtests', help='Output directory')
    
    args = parser.parse_args()
    main(
        start_date=args.start,
        end_date=args.end,
        market=args.market,
        tiny=args.tiny,
        out_dir=args.out
    )