import pandas as pd
import numpy as np
from pathlib import Path

def normalize_csv(provider_csv: str, out_csv: str):
    p = Path(provider_csv)
    df = pd.read_csv(p)
    # Heuristic: use Projection as the predicted value; if absent, use Line
    if 'Projection' in df.columns:
        proj = df['Projection'].astype(float)
    elif 'Line' in df.columns:
        proj = df['Line'].astype(float)
    else:
        # fallback: random small numbers
        proj = pd.Series([50.0] * len(df))

    # Convert projection (continuous) to a probability in [0,1] for testing by scaling
    p_hit = (proj - proj.min()) / (proj.max() - proj.min() + 1e-9)
    # Synthetic outcomes: binomial by p_hit
    outcomes = pd.Series(np.random.default_rng(42).binomial(1, p_hit))

    out_df = pd.DataFrame({'Date': df.get('Date'), 'p_hit': p_hit, 'outcome': outcomes})
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_csv, index=False)
    print('Wrote pipeline CSV', out_csv)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_csv', required=True)
    parser.add_argument('--out', dest='out_csv', required=True)
    args = parser.parse_args()
    normalize_csv(args.in_csv, args.out_csv)
