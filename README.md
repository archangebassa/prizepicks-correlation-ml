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

### 1️⃣ Install dependencies
```bash
python -m pip install -r requirements.txt
```

2️⃣ Fetch + build demo data
python -m scripts.fetch_pfr_nfl
python -m scripts.build_datasets_nfl

3️⃣ Train baseline model + generate plots
python -m scripts.model_baseline

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



