import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score, mean_squared_error, mean_absolute_error
from sklearn.calibration import calibration_curve
from scipy.stats import pearsonr
from typing import Callable, Tuple, Dict


def calibration_by_bin(y_true, p_pred, n_bins=10, strategy='quantile'):
    """Return calibration by bin (count, mean predicted prob, observed freq).

    strategy: 'quantile' (equal-count) or 'uniform' (equal-width)
    """
    df = pd.DataFrame({'y': y_true, 'p': p_pred}).dropna()
    if df.empty:
        return pd.DataFrame(columns=['bin', 'n', 'p_mean', 'y_mean'])
    if strategy == 'quantile':
        df['bin'] = pd.qcut(df['p'], n_bins, duplicates='drop')
    else:
        df['bin'] = pd.cut(df['p'], n_bins)
    res = df.groupby('bin').agg(n=('y', 'size'), p_mean=('p', 'mean'), y_mean=('y', 'mean'))
    return res.reset_index()


def expected_calibration_error(y_true, p_pred, n_bins=10) -> float:
    """Compute a simple ECE (Expected Calibration Error) using equal-width bins."""
    df = calibration_by_bin(y_true, p_pred, n_bins=n_bins, strategy='uniform')
    if df.empty:
        return float('nan')
    total = df['n'].sum()
    ece = (df['n'] / total * (df['p_mean'] - df['y_mean']).abs()).sum()
    return float(ece)


def rmse_mae(y_true, y_pred) -> Dict[str, float]:
    y = np.asarray(y_true)
    p = np.asarray(y_pred)
    mask = ~np.isnan(p)
    if mask.sum() == 0:
        return {'rmse': float('nan'), 'mae': float('nan')}
    rmse = np.sqrt(mean_squared_error(y[mask], p[mask]))
    mae = mean_absolute_error(y[mask], p[mask])
    return {'rmse': float(rmse), 'mae': float(mae)}


def compute_metrics(y_true, p_pred) -> Dict:
    """Compute a set of metrics for binary outcomes and predicted probabilities."""
    y = np.asarray(y_true)
    p = np.asarray(p_pred)
    mask = ~np.isnan(p)
    y = y[mask]
    p = p[mask]
    out = {}
    out['n'] = int(len(y))
    if out['n'] == 0:
        return out
    out['brier'] = float(brier_score_loss(y, p))
    eps = 1e-15
    p_clip = np.clip(p, eps, 1 - eps)
    out['logloss'] = float(log_loss(y, p_clip))
    try:
        out['pearson'], out['pearson_p'] = pearsonr(p, y)
    except Exception:
        out['pearson'], out['pearson_p'] = float('nan'), float('nan')
    out.update(rmse_mae(y, p))
    # AUC only if variability exists
    try:
        out['auc'] = float(roc_auc_score(y, p))
    except Exception:
        out['auc'] = float('nan')
    out['mean_pred'] = float(np.mean(p))
    out['mean_outcome'] = float(np.mean(y))
    out['ece'] = expected_calibration_error(y, p, n_bins=10)
    return out


def bootstrap_ci(metric_fn: Callable[[np.ndarray, np.ndarray], float], y_true: np.ndarray, p_pred: np.ndarray, n_bootstrap: int = 1000, alpha: float = 0.05) -> Tuple[float, float, float]:
    """Bootstrap confidence interval for a scalar metric function(metric_fn(y,p)).

    Returns (median, lower, upper)
    """
    y = np.asarray(y_true)
    p = np.asarray(p_pred)
    mask = ~np.isnan(p)
    y = y[mask]
    p = p[mask]
    n = len(y)
    if n == 0:
        return float('nan'), float('nan'), float('nan')
    stats = []
    rng = np.random.default_rng()
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        try:
            val = float(metric_fn(y[idx], p[idx]))
        except Exception:
            val = float('nan')
        stats.append(val)
    stats = np.array([s for s in stats if not np.isnan(s)])
    if stats.size == 0:
        return float('nan'), float('nan'), float('nan')
    lo = np.percentile(stats, 100 * (alpha / 2))
    hi = np.percentile(stats, 100 * (1 - alpha / 2))
    med = float(np.median(stats))
    return med, float(lo), float(hi)
