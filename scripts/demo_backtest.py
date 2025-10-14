import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

from scripts.metrics import compute_metrics, calibration_by_bin
from scripts.backtest import run_backtest


def synth_data(n=200, seed=42):
    rng = np.random.default_rng(seed)
    # create a simple latent feature x and map to true probability
    x = rng.normal(loc=0.0, scale=1.0, size=n)
    # logistic mapping to [0,1]
    true_p = 1 / (1 + np.exp(- (0.5 * x)))
    # predicted p is noisy estimate of true_p
    pred_noise = rng.normal(0, 0.08, size=n)
    p_hat = np.clip(true_p + pred_noise, 0.001, 0.999)
    outcomes = rng.binomial(1, true_p)
    dates = pd.date_range('2023-09-01', periods=n, freq='D')
    df = pd.DataFrame({'Date': dates, 'p_hit': p_hat, 'outcome': outcomes})
    return df


def plot_calibration(df, out_path: Path, n_bins=10):
    cb = calibration_by_bin(df['outcome'], df['p_hit'], n_bins=n_bins, strategy='quantile')
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(cb['p_mean'], cb['y_mean'], marker='o')
    ax.plot([0,1],[0,1], linestyle='--', color='gray')
    ax.set_xlabel('Mean predicted probability')
    ax.set_ylabel('Observed frequency')
    ax.set_title('Calibration plot')
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_roc(df, out_path: Path):
    fpr, tpr, _ = roc_curve(df['outcome'], df['p_hit'])
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot(fpr, tpr, label=f'AUC = {roc_auc:.3f}')
    ax.plot([0,1],[0,1], linestyle='--', color='gray')
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title('ROC Curve')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main():
    out_dir = Path('data/cache')
    out_dir.mkdir(parents=True, exist_ok=True)

    df = synth_data(n=200)
    csv_path = out_dir / 'demo_backtest.csv'
    df.to_csv(csv_path, index=False)

    # compute metrics and run backtest
    metrics = compute_metrics(df['outcome'], df['p_hit'])
    bt = run_backtest(str(csv_path), p_col='p_hit', outcome_col='outcome', payout=2.0, n_bootstrap=500)

    # save metrics + backtest summary
    out_json = out_dir / 'demo_backtest_metrics.json'
    combined = {'metrics': metrics, 'backtest': bt}
    with open(out_json, 'w', encoding='utf8') as f:
        json.dump(combined, f, indent=2)

    # plots
    cal_png = out_dir / 'demo_backtest_calibration.png'
    roc_png = out_dir / 'demo_backtest_roc.png'
    plot_calibration(df, cal_png, n_bins=10)
    plot_roc(df, roc_png)

    print('Wrote demo CSV, metrics JSON and plots to', out_dir)


if __name__ == '__main__':
    main()
