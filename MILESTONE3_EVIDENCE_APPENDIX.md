=== PROJECT MILESTONE 3 — FULL EVIDENCE APPENDIX ===
Project: prizepicks-correlation-ml
Date of evidence capture: 2025-11-11

------------------------
1) Key deliverables implemented
------------------------
- End-to-end backtest pipeline (CLI): `scripts/backtest_nfl.py`
- Provider-level calibration utilities: `scripts/provider_metrics.py`
- Metrics utilities & JSON serialization: `scripts/metrics.py`
- Frontend (Flask) + odds module: `frontend/app.py`, `frontend/odds.py`, `frontend/templates/index.html`, `frontend/static/*`
- Quick start & frontend docs: `FRONTEND_QUICK_START.md`, `frontend/README.md`
- Tests: `tests/test_backtest_nfl.py`, `tests/test_cleaning_and_scaffold.py`, `tests/test_correlation.py`
- Makefile and CI pipeline: `Makefile`, `.github/workflows/tests.yml`
- Tiny backtest outputs (CSV/JSON/PNG) stored under: `data/cache/backtests/`

------------------------
2) Exact quantitative metrics (from baseline run report: `reports/training_metrics_2025-11-11.md`)
------------------------
Model / Dataset: NFL Prop Prediction Baseline — sample (Nov 2024), n = 5

Core metrics:
- MAE (Mean Absolute Error): 0.6084
- RMSE: 0.6835
- Brier Score: 0.4671
- Log Loss: 1.3310
- Pearson Correlation (pred vs actual): -0.3423 (p = 0.5728)
- AUC-ROC: 0.3333 (significantly limited by sample size)

Classification / sample stats:
- Mean prediction: 0.5105
- Mean outcome (true hit rate): 0.6000 (3 of 5)

EV & betting metrics:
- Total EV: +0.1049
- ROI per bet: +2.10%
- Kelly criterion (median): 0.0350 (=> suggest ~3.5% bankroll)
- EV bootstrap (median): 0.0280
- EV bootstrap 95% CI: [-0.6309, 0.6589]  (very wide — small-sample uncertainty)

Provider-level Brier scores (passing_yards sample):
- PointsBet: 0.0025 (n=1)
- DraftKings: 0.4113 (n=2)
- FanDuel: 0.6081 (n=1)
- BetMGM: 0.9025 (n=1)

(Interpretation: positive total EV reported on the tiny sample, but CI and small n make conclusions tentative — see "Limitations" below.)

Source file for metrics: `reports/training_metrics_2025-11-11.md`

------------------------
3) Artifacts generated (committed)
------------------------
All artifacts listed in `MILESTONE3_COMPLETION.md` and produced by `scripts/backtest_nfl.py` (tiny/full modes), examples:
- `data/cache/backtests/baseline_sample_passing_yards.csv`        -- raw predictions & outcomes
- `data/cache/backtests/baseline_sample_passing_yards.json`       -- metrics summary JSON
- `data/cache/backtests/baseline_sample_passing_yards_calibration.png`  -- calibration plot
- `data/cache/backtests/baseline_sample_passing_yards_roc.png`    -- ROC plot
- `data/cache/backtests/baseline_sample_passing_yards_provider_metrics.json`
- Provider calibration and Brier plots for each run

Files added in feature branch and merged to `main`:
- `frontend/app.py`
- `frontend/odds.py`
- `frontend/templates/index.html`
- `frontend/static/css/style.css`
- `frontend/static/js/app.js`
- `frontend/README.md`
- `FRONTEND_QUICK_START.md`

------------------------
4) Test evidence (local runs)
------------------------
A) Pytest (repo root)
- Command run:
  .venv\Scripts\python.exe -m pytest tests/ -q
- Output captured:
  "5 passed in 5.56s"

B) Lightweight Flask test (`test_flask.py`) — uses Flask test client (no network)
- Command run:
  .venv\Scripts\python.exe test_flask.py
- Output captured:
  1. Importing Flask app...
     ✓ App imported successfully

  2. Creating test client...
     ✓ Test client created

  3. Testing /health endpoint...
     Status: 200
     Data: {'service': 'prizepicks-correlation-ml-api', 'status': 'ok'}

  4. Testing /api/autocomplete/players...
     Status: 200
     Data sample: ['Patrick Mahomes', 'Travis Kelce']

  ✓ All tests passed!

C) Notes: These tests confirm programmatic route behavior via Flask's test client. They do not require starting an external server and prove the endpoints return expected JSON shapes and status codes.

------------------------
5) Git evidence (recent commits & merge)
------------------------
Recent commits (HEAD of `main` / merged feature branch):
- a963a9f — fix: resolve Flask app crashes - fix Ja'Marr Chase syntax error and move scipy import to module level
- c6433c5 — docs: Add frontend quick start guide
- 1489ff9 — feat(frontend): Add professional Flask web UI for bet analysis
- 2be6268 — Complete Weeks 7-10: Add concrete metrics, baseline artifacts, and comprehensive documentation

(You can cite these hashes to reference the exact changes and merges. `git log --oneline -n 6` captured them.)

------------------------
6) Reproducible commands & how-to (PowerShell / Windows)
------------------------
(From repo root `prizepicks-correlation-ml-1`)

1. Create venv & install deps:
```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

2. Run tests:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
# Expected: "5 passed in X.XXs"
```

3. Run tiny backtest (example):
```powershell
python -m scripts.backtest_nfl --tiny --start 2024-12-01 --end 2024-12-31
# Output files written to: data/cache/backtests/
```

4. Run frontend Flask app (local dev):
```powershell
# From repo root:
.\.venv\Scripts\python.exe frontend\app.py
# Then open: http://127.0.0.1:5000
```

5. Quick programmatic tests (no server):
```powershell
.\.venv\Scripts\python.exe test_flask.py
# Test client confirms /health and /api/autocomplete/players
```

------------------------
7) Limitations and mitigations (explicit)
------------------------
- Limitation: Baseline metrics computed on a tiny sample (n = 5). Consequence: very wide bootstrap CIs (EV CI: [-0.6309, 0.6589]); AUC and p-values not reliable.
  - Mitigation: Run full backtests (100+ lines) using `scripts/backtest_nfl.py` (Weeks 9–10 plan). Use bootstrap and binning to obtain stable ECE and provider-level metrics.

- Limitation: Mock/synthetic provider assignments and mocked odds (frontend initially includes `MockOddsProvider`).
  - Mitigation: `frontend/odds.py` contains a `TheOddsAPIProvider` stub; integrate an API key and implement provider-specific parsing for live odds when available.

- Limitation: Frontend dev server ran in debug mode during development; some runs saw reloads. Use production WSGI or run with `debug=False` and `use_reloader=False` for stable local testing.

------------------------
8) Recommended next steps (short)
------------------------
- Expand backtest dataset to month(s) of real data (100+ lines). Recompute metrics and calibration per provider.
- Replace synthetic p_hit with production model predictions; re-run calibration pipeline.
- Implement correlation-aware simulation to quantify EV differences vs independence assumption.
- Plug in a real odds provider API client in `frontend/odds.py` and validate odds parsing for DraftKings / FanDuel / BetMGM / PointsBet.
- Add a smoke integration job in CI that runs `test_flask.py` (or containerized Flask) to assert basic API health on push.

------------------------
9) Files to point graders / reviewers to (quick list)
------------------------
- Metrics & training report: `reports/training_metrics_2025-11-11.md`
- Milestone completion & artifacts: `MILESTONE3_COMPLETION.md`
- Backtest script: `scripts/backtest_nfl.py`
- Provider metrics: `scripts/provider_metrics.py`
- Frontend app: `frontend/app.py`
- Odds module: `frontend/odds.py`
- Tests: `tests/` (three test files)
- Tiny backtest artifacts: `data/cache/backtests/`

------------------------
10) Direct evidence snippets (copy-ready)
------------------------
A) Pytest output:
5 passed in 5.56s

B) test_flask.py output:
1. Importing Flask app...
   ✓ App imported successfully

2. Creating test client...
   ✓ Test client created

3. Testing /health endpoint...
   Status: 200
   Data: {'service': 'prizepicks-correlation-ml-api', 'status': 'ok'}

4. Testing /api/autocomplete/players...
   Status: 200
   Data sample: ['Patrick Mahomes', 'Travis Kelce']

✓ All tests passed!

C) Exact metrics (from `reports/training_metrics_2025-11-11.md`):
- MAE: 0.6084
- RMSE: 0.6835
- Brier Score: 0.4671
- Log Loss: 1.3310
- AUC: 0.3333
- Total EV: +0.1049
- ROI per bet: +2.10%
- Kelly median: 0.0350
- EV bootstrap 95% CI: [-0.6309, 0.6589]

D) Recent commits (from `git log --oneline -n 6`):
- a963a9f — fix: resolve Flask app crashes - fix Ja'Marr Chase syntax error and move scipy import to module level
- c6433c5 — docs: Add frontend quick start guide
- 1489ff9 — feat(frontend): Add professional Flask web UI for bet analysis
- 2be6268 — Complete Weeks 7-10: Add concrete metrics, baseline artifacts, and comprehensive documentation

------------------------
END OF EVIDENCE APPENDIX
------------------------
