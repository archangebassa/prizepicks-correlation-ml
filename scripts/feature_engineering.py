import pandas as pd
from pathlib import Path

"""Compute simple per-game features from merged_eval.csv.

Produces data/samples/features.csv with features used by the ranking model.
"""


def main(in_path: str = 'data/samples/merged_eval.csv', out_path: str = 'data/samples/features.csv'):
    p = Path(in_path)
    if not p.exists():
        raise FileNotFoundError(f"Missing input merged CSV: {in_path}")

    df = pd.read_csv(p)

    # Ensure numeric columns
    for c in ['QB_PassYds', 'WR_RecYds', 'Rec', 'Tgt', 'PF', 'PA']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Rolling features for WR: previous 3-game avg yards and targets (per player/season not available in demo)
    df['WR_RecYds_roll3'] = df['WR_RecYds'].rolling(3, min_periods=1).mean()
    if 'Rec' in df.columns and 'Tgt' in df.columns:
        df['TargetShare'] = df['Rec'] / df['Tgt'].replace({0: pd.NA})
    else:
        df['TargetShare'] = pd.NA

    # Simple interaction: QB*WR coupling feature
    df['QBxWR'] = df['QB_PassYds'] * df['WR_RecYds']

    # Fill or drop na rows conservatively
    features = df[['Date_qb','G#','Week_qb','Opp','QB_PassYds','WR_RecYds','WR_RecYds_roll3','TargetShare','QBxWR']].copy()
    # Normalize column names for downstream scripts
    features = features.rename(columns={'Date_qb':'Date','Week_qb':'Week'})

    features.to_csv(out_path, index=False)
    print(f'Wrote features to {out_path} with {len(features)} rows')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_path', default='data/samples/merged_eval.csv')
    parser.add_argument('--out', dest='out_path', default='data/samples/features.csv')
    args = parser.parse_args()
    main(args.in_path, args.out_path)
