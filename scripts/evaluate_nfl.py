import pandas as pd
import numpy as np
from pathlib import Path
import sys

"""Simple evaluation script for NFL demo data.

Loads CSVs from data/samples (team, qb, wr), joins on Date, computes:
- Pearson correlation between QB_PassYds and WR_RecYds
- Linear regression (least squares) predicting WR_RecYds from QB_PassYds
  and metrics: slope, intercept, R^2, MAE, RMSE

Usage: run from repo root with the repo venv python. Outputs metrics to stdout
and writes merged CSV to data/samples/merged_eval.csv
"""


def load_csv(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required sample file not found: {path}")
    return pd.read_csv(p)


def merge_dfs(team_csv, qb_csv, wr_csv):
    team = load_csv(team_csv)
    qb = load_csv(qb_csv)
    wr = load_csv(wr_csv)

    # parse dates
    for df in (team, qb, wr):
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Determine best join key: prefer Date, then Week, then G#; otherwise align by position
    def has_col(df, col):
        return col in df.columns

    # prefer Date if all have it
    if has_col(team, 'Date') and has_col(qb, 'Date') and has_col(wr, 'Date'):
        merged = team.merge(qb, on='Date', how='inner', suffixes=('_team', '_qb'))
        merged = merged.merge(wr, on='Date', how='inner', suffixes=('', '_wr'))
        return merged

    # prefer Week
    if has_col(team, 'Week') and has_col(qb, 'Week') and has_col(wr, 'Week'):
        merged = team.merge(qb, on='Week', how='inner', suffixes=('_team', '_qb'))
        merged = merged.merge(wr, on='Week', how='inner', suffixes=('', '_wr'))
        return merged

    # prefer game number
    if has_col(team, 'G#') and has_col(qb, 'G#') and has_col(wr, 'G#'):
        merged = team.merge(qb, on='G#', how='inner', suffixes=('_team', '_qb'))
        merged = merged.merge(wr, on='G#', how='inner', suffixes=('', '_wr'))
        return merged

    # Last resort: align by row order (positional)
    team2 = team.reset_index(drop=True).copy()
    qb2 = qb.reset_index(drop=True).copy()
    wr2 = wr.reset_index(drop=True).copy()
    # trim to shortest length
    n = min(len(team2), len(qb2), len(wr2))
    if n == 0:
        raise RuntimeError('No overlapping rows to merge')
    team2 = team2.head(n).copy()
    qb2 = qb2.head(n).copy()
    wr2 = wr2.head(n).copy()
    # add positional key
    team2['_pos'] = range(n)
    qb2['_pos'] = range(n)
    wr2['_pos'] = range(n)
    merged = team2.merge(qb2, on='_pos', how='inner', suffixes=('_team', '_qb'))
    merged = merged.merge(wr2, on='_pos', how='inner', suffixes=('', '_wr'))
    merged = merged.drop(columns=['_pos'])
    return merged


def compute_metrics(df, x_col='QB_PassYds', y_col='WR_RecYds'):
    if x_col not in df.columns or y_col not in df.columns:
        raise KeyError(f"Columns required for metrics not found: {x_col}, {y_col}")

    sub = df[[x_col, y_col]].dropna()
    x = sub[x_col].astype(float).values
    y = sub[y_col].astype(float).values

    # Pearson correlation
    corr = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan

    # Linear regression (least squares)
    slope, intercept = np.polyfit(x, y, 1) if len(x) > 1 else (np.nan, np.nan)
    y_pred = slope * x + intercept

    # R^2
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2) if len(y) > 0 else np.nan
    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else np.nan

    # MAE and RMSE
    mae = np.mean(np.abs(y - y_pred)) if len(y) > 0 else np.nan
    rmse = np.sqrt(np.mean((y - y_pred) ** 2)) if len(y) > 0 else np.nan

    return {
        'n': len(x),
        'pearson_corr': float(corr) if not np.isnan(corr) else None,
        'slope': float(slope) if not np.isnan(slope) else None,
        'intercept': float(intercept) if not np.isnan(intercept) else None,
        'r2': float(r2) if not np.isnan(r2) else None,
        'mae': float(mae) if not np.isnan(mae) else None,
        'rmse': float(rmse) if not np.isnan(rmse) else None,
    }


def main():
    base = Path('data/samples')
    base = Path('data/cache')
    # Default to 2025 demo files (update as you fetch different players/teams)
    team_csv = base / 'nfl_kc_2025_team.csv'
    qb_csv = base / 'nfl_kc_mahomes_2025.csv'
    wr_csv = base / 'nfl_kc_rashee_rice_2025.csv'

    try:
        merged = merge_dfs(team_csv, qb_csv, wr_csv)
    except Exception as e:
        print('Error merging CSVs:', e)
        sys.exit(1)

    out_path = base / 'merged_eval.csv'
    merged.to_csv(out_path, index=False)
    print(f'Merged {len(merged)} rows written to {out_path}')

    try:
        metrics = compute_metrics(merged)
    except Exception as e:
        print('Error computing metrics:', e)
        sys.exit(1)

    print('\nEvaluation metrics (predict WR_RecYds from QB_PassYds)')
    for k, v in metrics.items():
        print(f'{k}: {v}')


if __name__ == '__main__':
    main()
