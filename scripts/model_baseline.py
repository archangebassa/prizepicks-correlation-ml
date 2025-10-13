# scripts/model_baseline.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

def load_features(path="data/samples/nfl_features.csv"):
    return pd.read_csv(path, parse_dates=['Date'])

def correlation_heatmap(df, out_path="docs/img/corr_heatmap.png"):
    corr = df[['QB_PassYds','QB_PassTD','WR_RecYds','WR_RecTD','is_away']].corr(method='pearson')
    plt.figure(figsize=(5,4))
    plt.imshow(corr, interpolation='nearest')
    plt.xticks(range(corr.shape[1]), corr.columns, rotation=45, ha='right')
    plt.yticks(range(corr.shape[0]), corr.index)
    plt.colorbar(fraction=0.046, pad=0.04)
    Path("docs/img").mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return corr

def fit_ridge_predict(df):
    # Minimal features for demo
    X = df[['QB_PassYds','QB_PassTD','is_away']].copy()
    # You can add opponent encoding later; for demo we keep it simple
    y = df['WR_RecYds'].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=min(0.3, max(0.3, 1/len(df))), random_state=42)
    model = Ridge(alpha=1.0).fit(X_train, y_train)

    y_pred = model.predict(X_test)
    return {
        "model": model,
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "example_rows": X_test.assign(actual=y_test, pred=y_pred).head(5)
    }

def demo_report(corr_df, metrics, out_path="docs/demo_report.md"):
    Path("docs").mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("# Demo Report (NFL: KC 2023, Mahomes → Rashee Rice)\n\n")
        f.write("## Correlations (Pearson)\n\n")
        f.write(corr_df.to_markdown() + "\n\n")
        f.write("![corr](img/corr_heatmap.png)\n\n")
        f.write("## Ridge Regression: WR_RecYds ~ QB_PassYds + QB_PassTD + is_away\n\n")
        f.write(f"- Train/Test sizes: {metrics['n_train']} / {metrics['n_test']}\n")
        f.write(f"- MAE: {metrics['mae']:.2f}\n")
        f.write(f"- R^2: {metrics['r2']:.3f}\n\n")
        f.write("### Example predictions (head):\n\n")
        f.write(metrics['example_rows'].to_markdown(index=False))
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    df = load_features()
    corr = correlation_heatmap(df)
    met = fit_ridge_predict(df)
    demo_report(corr, met)
    print("Done. See docs/img/corr_heatmap.png and docs/demo_report.md")
