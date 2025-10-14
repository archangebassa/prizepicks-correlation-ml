import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import roc_curve, auc

from scripts.metrics import calibration_by_bin, compute_metrics


def plot_regression_scatter(df, x_col='QB_PassYds', y_col='WR_RecYds', out_dir=Path('data/cache/plots')):
    out_dir.mkdir(parents=True, exist_ok=True)
    df2 = df[[x_col, y_col]].dropna()
    if df2.empty:
        print('No data for regression scatter')
        return
    x = df2[x_col].astype(float).values
    y = df2[y_col].astype(float).values
    # fit linear regression line
    if len(x) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
    else:
        slope, intercept = np.nan, np.nan
        y_pred = np.full_like(y, np.nan)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(x, y, alpha=0.8)
    if not np.isnan(slope):
        xs = np.linspace(np.min(x), np.max(x), 100)
        ax.plot(xs, slope * xs + intercept, color='red', label=f'line: y={slope:.2f}x+{intercept:.1f}')
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title('Regression: QB -> WR (per-game)')
    ax.legend()
    fig.tight_layout()
    out = out_dir / 'regression_scatter.png'
    fig.savefig(out)
    plt.close(fig)
    print('Wrote', out)


def plot_residuals_hist(df, x_col='QB_PassYds', y_col='WR_RecYds', out_dir=Path('data/cache/plots')):
    out_dir.mkdir(parents=True, exist_ok=True)
    df2 = df[[x_col, y_col]].dropna()
    if df2.empty or len(df2) < 2:
        print('No data for residuals')
        return
    x = df2[x_col].astype(float).values
    y = df2[y_col].astype(float).values
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    fig, ax = plt.subplots(figsize=(6,4))
    ax.hist(resid, bins=10, alpha=0.8)
    ax.set_xlabel('Residual (actual - predicted)')
    ax.set_ylabel('Count')
    ax.set_title('Residuals Histogram')
    fig.tight_layout()
    out = out_dir / 'residuals_hist.png'
    fig.savefig(out)
    plt.close(fig)
    print('Wrote', out)


def plot_odds_roc_and_calibration(norm_csv='data/cache/provider/theoddsapi_normalized.csv', out_dir=Path('data/cache/plots')):
    out_dir.mkdir(parents=True, exist_ok=True)
    p = Path(norm_csv)
    if not p.exists():
        print('No normalized odds CSV found at', norm_csv)
        return
    df = pd.read_csv(p, parse_dates=['Date'])
    if 'Projection' not in df.columns:
        print('No Projection column in normalized odds CSV')
        return
    # synth outcomes from projection
    rng = np.random.default_rng(42)
    p_hat = df['Projection'].fillna(0.5).values
    y = rng.binomial(1, p_hat)

    # ROC
    try:
        fpr, tpr, _ = roc_curve(y, p_hat)
        roc_auc = auc(fpr, tpr)
    except Exception:
        fpr, tpr, roc_auc = None, None, None

    if fpr is not None:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.plot(fpr, tpr, label=f'AUC = {roc_auc:.3f}')
        ax.plot([0,1],[0,1], linestyle='--', color='gray')
        ax.set_xlabel('False Positive Rate')
        ax.set_ylabel('True Positive Rate')
        ax.set_title('ROC Curve (odds-derived, synthetic outcomes)')
        ax.legend(loc='lower right')
        fig.tight_layout()
        out = out_dir / 'odds_roc.png'
        fig.savefig(out)
        plt.close(fig)
        print('Wrote', out)

    # Calibration
    cb = calibration_by_bin(y, p_hat, n_bins=10, strategy='quantile')
    fig, ax = plt.subplots(figsize=(6,4))
    ax.plot(cb['p_mean'], cb['y_mean'], marker='o')
    ax.plot([0,1],[0,1], linestyle='--', color='gray')
    ax.set_xlabel('Mean predicted probability')
    ax.set_ylabel('Observed frequency')
    ax.set_title('Calibration (odds-derived)')
    fig.tight_layout()
    out = out_dir / 'odds_calibration.png'
    fig.savefig(out)
    plt.close(fig)
    print('Wrote', out)


def main():
    # Regression plots based on merged_eval
    merged = Path('data/cache/merged_eval.csv')
    if merged.exists():
        # merged_eval.csv sometimes has Date_qb or Date_team instead of Date
        df = pd.read_csv(merged)
        if 'Date' not in df.columns:
            if 'Date_qb' in df.columns:
                df['Date'] = pd.to_datetime(df['Date_qb'], errors='coerce')
            elif 'Date_team' in df.columns:
                df['Date'] = pd.to_datetime(df['Date_team'], errors='coerce')
            else:
                df['Date'] = pd.NaT
        plot_regression_scatter(df)
        plot_residuals_hist(df)
    else:
        print('No merged_eval.csv found for regression plots')

    # Odds-derived plots
    plot_odds_roc_and_calibration()


if __name__ == '__main__':
    main()
