# 🏈 PrizePicks Correlation ML

**Author:** Archange Kra-Bassa, Natesan Rajesh 
**Course:** CS 4220 / 6235 – High-Performance Computing / RTES @ Georgia Tech  
**Semester:** Fall 2025  

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-yellow)
![Status](https://img.shields.io/badge/Project--Status-Active-brightgreen)

---

## 📘 Overview

**PrizePicks Correlation ML** is a data-driven sports-analytics pipeline that studies **statistical dependencies between player performances** to improve prediction accuracy for daily-fantasy and prop-betting entries.  

It builds a **machine-learning correlation engine** that measures how one player’s output (e.g., a QB’s passing yards) affects another’s (e.g., a WR’s receiving yards).  
By quantifying these links, the system generates smarter pick combinations and runs simulations to maximize expected value.

---

## 🎯 Project Objectives

1. **Correlation Engine** – Compute covariance / correlation between player outcomes across teams & seasons.  
2. **Data Pipeline** – Scrape + pre-process historical player stats and PrizePicks projections.  
3. **Modeling Framework** – Implement baseline + ML-based estimators (Pearson, Spearman, Ridge Regression, Multivariate Regression).  
4. **Simulation Layer** – Evaluate entry performance under varying correlation thresholds.  
5. **Visualization Suite** – Heatmaps, regression plots, calibration curves, and model diagnostics.

---

## 🧩 Repository Structure
prizepicks-correlation-ml/
│

├── data/

│ ├── samples/ # Demo datasets (team, QB, WR logs)

│ └── mapping/ # Player ID mappings (future expansion)

│
├── scripts/

│ ├── fetch_pfr_nfl.py # Fetch team/player data from PFR

│ ├── build_datasets_nfl.py # Clean + merge data into features

│ ├── model_baseline.py # Correlation + Ridge Regression model

│ ├── metrics.py # Calibration + evaluation utilities

│ └── plots_report.py # Generates all visualizations

│
├── requirements.txt # Python dependencies

├── checkpoint1_summary.md # Project progress report

└── README.md # You’re here
---

## ⚙️ Setup & Usage

### Installation & Setup

Use the provided Makefile commands to get started:

```bash
# Install dependencies
make install

# Run tests
make test

# Run a small backtest (for testing)
make backtest-tiny

# Run full NFL backtest
make backtest-nfl
```

### Manual Commands

```bash
# 1. Fetch and build data
python -m scripts.fetch_pfr_nfl
python -m scripts.build_datasets_nfl

# 2. Train baseline model
python -m scripts.model_baseline

# 3. Run backtests with specific parameters
python -m scripts.backtest_nfl --start 2024-09-01 --end 2024-12-31
python -m scripts.backtest_nfl --start 2024-09-01 --end 2024-12-31 --market passing_yards
```

### Backtest Output

Backtests generate several artifacts in `data/cache/backtests/`:
- `{date_range}_{market}.csv` - Raw backtest data (predictions, outcomes, probabilities)
- `{date_range}_{market}.json` - Results summary with metrics (MAE, RMSE, Brier, EV, etc.)
- `{date_range}_{market}_calibration.png` - Calibration curve (predicted vs observed frequency)
- `{date_range}_{market}_roc.png` - ROC curve (True Positive Rate vs False Positive Rate)
- `{date_range}_{market}_provider_calibration.png` - Provider comparison calibration curves
- `{date_range}_{market}_provider_brier_scores.png` - Provider Brier scores bar chart
- `{date_range}_{market}_provider_metrics.json` - Detailed per-provider calibration bins
- `{date_range}_summary.json` - Overall backtest summary across all markets

### Sample Data

A small reproducible dataset is included for quick testing:
- **Location:** `data/samples/nfl_sample.csv`
- **Size:** 5 NFL prop lines (Nov 2024)
- **Fields:** Date, Team, Player, QB_PassYds, QB_PassYds_actual, WR_RecYds, WR_RecYds_actual, provider
- **Usage:** Run `python -m scripts.run_baseline` to execute baseline backtest on sample

### Baseline Metrics (Weeks 7–8)

Baseline backtest on sample data (Nov 2024, 5 props, passing_yards market):

| Metric | Value |
|--------|-------|
| MAE | 0.6084 |
| RMSE | 0.6835 |
| Brier Score | 0.4671 |
| Log Loss | 1.3310 |
| Total EV | +0.1049 (+2.1% ROI) |
| Provider Best | PointsBet (Brier: 0.0025) |

Artifacts → `data/cache/backtests/baseline_sample_passing_yards_*`

Reports → `reports/baseline_metrics.md`, `reports/training_metrics_2025-11-11.md`

Outputs →
data/samples/nfl_features.csv – merged dataset
data/cache/plots/ – correlation heatmap, residual histogram, calibration curve
Console metrics: MAE / R² / sample predictions

📚 Data Sources
Pro-Football-Reference
Basketball-Reference
SportsData.io API (NFL/NBA)
FBRef (Soccer)
Sports-Reference CFB

🧠 Skills & Learning
Domain	Key Takeaways
Data Engineering	Automated HTML table parsing (pandas.read_html, BeautifulSoup).
Statistical Modeling	Pearson/Spearman correlations and Ridge Regression models.
Sports Analytics	Feature engineering for player synergies and game context.
Visualization	Clear interpretation through Matplotlib & Seaborn plots.



