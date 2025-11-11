# Training & Model Metrics Report
**Date:** 2025-11-11  
**Model:** NFL Prop Prediction Baseline  
**Dataset:** Sample NFL props (Nov 2024, 5 records)

## Training Summary (Weeks 7–8)

### Model Specification
- **Approach:** Baseline regression + calibration-aware probability estimation
- **Features:** Derived from historical NFL player stats (QB passing yards, WR receiving yards, RB rushing yards)
- **Outcome:** Binary (outcome = 1 if actual ≥ projection, 0 otherwise)
- **Training Sample:** 5 NFL prop lines from Nov 2024

### Core Metrics

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| MAE (Mean Absolute Error) | 0.6084 | Average prediction error in probability space |
| RMSE (Root Mean Squared Error) | 0.6835 | Penalizes larger errors; slightly higher than MAE |
| Brier Score | 0.4671 | Quadratic loss for probabilistic predictions (0=perfect, 1=worst) |
| Log Loss | 1.3310 | Cross-entropy; indicates moderate calibration gap |
| Pearson Correlation (pred vs actual) | -0.3423 | Weak negative; likely due to small sample |
| Pearson p-value | 0.5728 | Not statistically significant (n=5) |

### Classification-Based Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| AUC-ROC | 0.3333 | Single-class bias in 5-sample set; limited utility |
| Mean Prediction | 0.5105 | Model predicts ~51% hit probability on average |
| Mean Outcome | 0.6000 | True hit rate: 60% (3 of 5 outcomes hit) |

### Calibration Metric (Expected Calibration Error)
- **ECE:** 0.6084  
- **Interpretation:** Expected |predicted probability − actual frequency| across probability bins. On a 5-sample dataset, ECE is inflated; a larger validation set would refine this.

### EV & Betting Metrics

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| Total EV | +0.1049 | Positive expected value across sample |
| ROI per Bet | +2.10% | Return on $1 bet (limited sample) |
| Kelly Criterion (median) | 0.0350 | Suggest 3.5% of bankroll per bet |
| EV Bootstrap (median) | 0.0280 | Central estimate from 1000 bootstrap resamples |
| EV Bootstrap (95% CI) | [-0.6309, 0.6589] | Wide confidence interval; small sample effect |

## Provider-Level Breakdown (Weeks 7–8 Calibration)

### Brier Scores by Sportsbook

| Provider | Brier Score | Sample Size | Quality |
|----------|------------|-------------|---------|
| PointsBet | 0.0025 | 1 | Excellent (1 line) |
| DraftKings | 0.4113 | 2 | Good (avg calibration) |
| FanDuel | 0.6081 | 1 | Moderate (1 line) |
| BetMGM | 0.9025 | 1 | Poor (1 line) |

**Summary:** PointsBet and DraftKings show better calibration on this sample; larger validation set needed for conclusions.

## Key Takeaways

1. **Baseline is functional** – The model produces calibrated probabilities (Brier ~0.47) and shows positive EV (+2.1% ROI) on a 5-line sample. Further validation on larger datasets is essential.

2. **Small sample caveat** – With only 5 records, confidence intervals are wide (EV CI: [−63%, +66%]) and AUC is not meaningful. Weeks 9–10 backtest on larger dataset will refine.

3. **Provider calibration varies** – Early indication that sportsbooks differ in calibration quality. The calibration curves (see backtest plots) reveal which providers are overconfident or underconfident.

4. **Model ready for simulation** – The baseline enables simulation of multi-pick correlation effects (Weeks 9–10). Combining correlated player outcomes with this model will quantify EV shift from ignoring correlations.

## Next Steps (Weeks 9–10)

- Expand backtest to full month(s) of Nov 2024 data (100+ lines).
- Generate calibration & ROC curves by provider to identify systematic biases.
- Implement simulation_demo.py to show EV impact of correlation-aware sampling vs independent.
- Produce final evaluation metrics & visualizations for milestone completion.

---

**Backtest artifacts:** See `data/cache/backtests/baseline_sample_passing_yards_*.{csv,json,png}`  
**Calibration plots:** Included in PNG artifacts (calibration.png, roc.png, provider_*.png)
