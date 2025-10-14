import pandas as pd, json
from pathlib import Path
from scripts.metrics import compute_metrics, calibration_by_bin
import numpy as np
import matplotlib.pyplot as plt

p = Path('data/cache/provider/theoddsapi_normalized.csv')
if not p.exists():
    print('Normalized CSV not found at', p)
    raise SystemExit(1)

df = pd.read_csv(p)
print('Rows in normalized CSV:', len(df))
# filter only rows with a Projection

if 'Projection' not in df.columns:
    print('No Projection column in normalized CSV')
    raise SystemExit(1)

sdf = df[df['Projection'].notnull()].copy()
if not sdf.empty:
    sdf['Projection'] = pd.to_numeric(sdf['Projection'], errors='coerce')
    sdf['Projection'] = sdf['Projection'].clip(0,1)

# Synthesize outcomes: Bernoulli(draw) using the projection as p
rng = np.random.default_rng(123)
if not sdf.empty:
    sdf['outcome'] = rng.binomial(1, sdf['Projection'].fillna(0.5))

metrics = compute_metrics(sdf['outcome'], sdf['Projection'])
print('Metrics:', metrics)
out_path = Path('data/cache/provider/metrics_report.json')
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(metrics, f, indent=2)
# calibration plot
if len(sdf) > 0:
    cal = calibration_by_bin(sdf['outcome'], sdf['Projection'], n_bins=10)
    plt.figure()
    plt.plot(cal['p_mean'], cal['y_mean'], marker='o')
    plt.plot([0,1],[0,1], linestyle='--', color='gray')
    plt.xlabel('Predicted prob')
    plt.ylabel('Observed freq')
    plt.title('Calibration (TheOddsAPI synthetic outcomes)')
    plt.savefig('data/cache/provider/calibration.png')
    print('Wrote data/cache/provider/calibration.png and metrics_report.json')
else:
    print('No rows to plot or score')
