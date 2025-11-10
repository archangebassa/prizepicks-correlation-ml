"""Provider-level metrics and calibration analysis.

This module extends the core metrics to handle multiple providers/books,
generating comparative calibration curves and Brier score tables.
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import brier_score_loss
import matplotlib.pyplot as plt
import seaborn as sns

from .metrics import calibration_by_bin
from .demo_backtest import plot_calibration


def compute_provider_metrics(df: pd.DataFrame, provider_col='provider', p_col='p_hit', outcome_col='outcome') -> dict:
    """Compute metrics for each provider."""
    results = {}
    
    for provider in df[provider_col].unique():
        mask = df[provider_col] == provider
        provider_df = df[mask]
        
        # Compute Brier score
        brier = brier_score_loss(provider_df[outcome_col], provider_df[p_col])
        
        # Get calibration bins
        cal_bins = calibration_by_bin(
            provider_df[outcome_col],
            provider_df[p_col],
            n_bins=10,
            strategy='quantile'
        )
        
        # Convert to dict and clean up non-serializable types
        cal_list = []
        for idx, row in cal_bins.iterrows():
            cal_item = {}
            for col in cal_bins.columns:
                val = row[col]
                # Convert Interval to string, handle other types
                if hasattr(val, '__class__') and 'Interval' in val.__class__.__name__:
                    cal_item[col] = str(val)
                elif isinstance(val, (np.integer, np.floating)):
                    cal_item[col] = float(val)
                elif pd.isna(val):
                    cal_item[col] = None
                else:
                    cal_item[col] = val
            cal_list.append(cal_item)
        
        results[provider] = {
            'brier_score': float(brier),
            'n_predictions': len(provider_df),
            'calibration': cal_list
        }
    
    return results


def plot_provider_calibration(
    df: pd.DataFrame,
    out_dir: Path,
    prefix: str = '',
    provider_col='provider',
    p_col='p_hit',
    outcome_col='outcome'
):
    """Generate calibration plots comparing providers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Overall calibration plot with all providers
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for provider in df[provider_col].unique():
        mask = df[provider_col] == provider
        provider_df = df[mask]
        
        # Get calibration curve
        cal = calibration_by_bin(
            provider_df[outcome_col],
            provider_df[p_col],
            n_bins=10,
            strategy='quantile'
        )
        
        # Plot provider curve
        ax.plot(cal['p_mean'], cal['y_mean'], marker='o', label=f'{provider} (n={len(provider_df)})')
    
    # Add diagonal reference line
    ax.plot([0, 1], [0, 1], '--', color='gray', alpha=0.5)
    
    ax.set_xlabel('Predicted probability')
    ax.set_ylabel('Observed frequency')
    ax.set_title('Calibration Curves by Provider')
    ax.legend(title='Provider', bbox_to_anchor=(1.05, 1), loc='upper left')
    
    fig.tight_layout()
    plot_path = out_dir / f'{prefix}provider_calibration.png'
    fig.savefig(plot_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    # Generate Brier score comparison table
    metrics = compute_provider_metrics(df, provider_col, p_col, outcome_col)
    
    # Plot Brier scores as a bar chart
    fig, ax = plt.subplots(figsize=(8, 5))
    providers = list(metrics.keys())
    brier_scores = [m['brier_score'] for m in metrics.values()]
    
    sns.barplot(x=providers, y=brier_scores, ax=ax)
    ax.set_title('Brier Scores by Provider')
    ax.set_ylabel('Brier Score (lower is better)')
    
    # Rotate x-labels if many providers
    if len(providers) > 4:
        plt.xticks(rotation=45, ha='right')
    
    fig.tight_layout()
    brier_path = out_dir / f'{prefix}provider_brier_scores.png'
    fig.savefig(brier_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    # Save metrics as JSON
    metrics_path = out_dir / f'{prefix}provider_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return {
        'calibration_plot': str(plot_path),
        'brier_plot': str(brier_path),
        'metrics_json': str(metrics_path),
        'metrics': metrics
    }