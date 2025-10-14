import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scripts.metrics import compute_metrics, calibration_by_bin


def synth_outcomes_from_prob(df, prob_col='Projection', seed=42):
    rng = np.random.default_rng(seed)
    p = df[prob_col].fillna(0.5).values
    outcomes = rng.binomial(1, p)
    return outcomes


def plot_calibration(y, p, out_path: Path, n_bins=10):
    cb = calibration_by_bin(y, p, n_bins=n_bins, strategy='quantile')
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(cb['p_mean'], cb['y_mean'], marker='o')
    ax.plot([0,1],[0,1], linestyle='--', color='gray')
    ax.set_xlabel('Mean predicted probability')
    ax.set_ylabel('Observed frequency')
    ax.set_title('Calibration plot (odds-derived)')
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main(norm_csv='data/cache/provider/theoddsapi_normalized.csv'):
    p = Path(norm_csv)
    if not p.exists():
        raise FileNotFoundError('Normalized odds CSV not found: ' + norm_csv)
    df = pd.read_csv(p, parse_dates=['Date'])
    # Use Projection as implied probability for synthetic outcomes
    if 'Projection' not in df.columns:
        raise KeyError('Projection column not found in normalized CSV')

    # synthesize outcomes
    y = synth_outcomes_from_prob(df, 'Projection')
    p_hat = df['Projection'].fillna(0.5).values

    metrics = compute_metrics(y, p_hat)

    out_dir = Path('data/cache/provider')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / 'theoddsapi_metrics.json'
    with open(out_json, 'w', encoding='utf8') as f:
        json.dump(metrics, f, indent=2)

    plot_calibration(y, p_hat, out_dir / 'theoddsapi_calibration.png')
    print('Wrote metrics JSON and calibration plot to', out_dir)


if __name__ == '__main__':
    main()
