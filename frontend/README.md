# Frontend: PrizePicks Correlation ML Web UI

A professional Flask-based web interface for analyzing sports bets using data-driven expected value calculations and calibration-adjusted probabilities.

## Features

- **Single Bet Analysis**
  - Input player, market, projection, and odds
  - Get probability of hit vs. implied probability
  - Calculate expected value (EV) and Kelly criterion
  - Recommendations based on edge detection

- **Multi-Leg (Parlay) Analysis**
  - Combine multiple bets
  - Joint probability calculation (independent)
  - Combined EV and Kelly for parlays
  - Optimal bet sizing

- **Provider Calibration**
  - Load sportsbook calibration data
  - Adjust probabilities based on provider Brier scores
  - Confidence metrics based on historical accuracy

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (no frameworks)
- **Data:** JSON artifacts from backtest pipeline
- **Styling:** Dark mode, responsive design

## Running the App

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Flask Server

```bash
cd frontend
python app.py
```

The app will start on `http://127.0.0.1:5000`

### 3. Open in Browser

Navigate to `http://localhost:5000` and start analyzing bets.

## Project Structure

```
frontend/
├── app.py                      # Flask application
├── templates/
│   └── index.html             # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css          # Styling (dark mode, responsive)
│   └── js/
│       └── app.js             # Frontend logic
└── README.md                  # This file
```

## API Endpoints

### POST `/api/predict`

Analyze a single bet.

**Request:**
```json
{
  "sportsbook": "draftkings",
  "market": "passing_yards",
  "player": "Patrick Mahomes",
  "projection": 300,
  "actual_or_estimate": 310,
  "odds": -110,
  "correlations": []
}
```

**Response:**
```json
{
  "success": true,
  "prediction": {
    "player": "Patrick Mahomes",
    "market": "passing_yards",
    "p_hit": 0.65,
    "p_hit_pct": 65.0,
    "implied_prob": 0.5238,
    "implied_prob_pct": 52.38
  },
  "valuation": {
    "odds": -110,
    "decimal_odds": 1.91,
    "ev": 0.1247,
    "ev_pct": 12.47,
    "kelly_fraction": 0.0652,
    "kelly_pct": 6.52
  },
  "confidence": {
    "model_confidence": 0.65,
    "confidence_pct": 65.0
  }
}
```

### POST `/api/multi-leg`

Analyze a multi-leg entry (parlay).

**Request:**
```json
{
  "legs": [
    {"player": "Patrick Mahomes", "market": "passing_yards", "p_hit": 0.65, "odds": -110},
    {"player": "Travis Kelce", "market": "receiving_yards", "p_hit": 0.60, "odds": -110}
  ],
  "correlation_matrix": null
}
```

**Response:**
```json
{
  "success": true,
  "multi_leg": {
    "num_legs": 2,
    "joint_probability_independent": 0.39,
    "joint_probability_pct": 39.0,
    "combined_decimal_odds": 3.64,
    "combined_payout": 2.64,
    "combined_ev": 0.464,
    "combined_ev_pct": 46.4,
    "combined_kelly_fraction": 0.1752,
    "combined_kelly_pct": 17.52
  }
}
```

### GET `/api/calibration`

Retrieve provider calibration data.

**Request:**
```
GET /api/calibration?market=passing_yards
```

**Response:**
```json
{
  "success": true,
  "market": "passing_yards",
  "data": {
    "provider_metrics": {
      "DraftKings": {"brier_score": 0.4113, ...},
      ...
    }
  }
}
```

### GET `/health`

Health check.

## Usage Examples

### Example 1: Single Bet

1. Select "DraftKings" as sportsbook
2. Choose "Passing Yards" market
3. Enter "Patrick Mahomes" as player
4. Projection: 300, Estimated: 310
5. Odds: -110
6. Click "Analyze Bet"

The app will calculate:
- Probability of hit: ~65%
- Implied probability: ~52%
- EV: +12.47%
- Kelly criterion: 6.52% of bankroll

**Recommendation:** ✅ Strong Value – Bet 6.52% of bankroll

### Example 2: Parlay (2-Leg)

1. Add Leg 1: Mahomes O300 passing yards, p_hit 0.65
2. Add Leg 2: Kelce O75 receiving yards, p_hit 0.60
3. Click "Analyze Parlay"

The app will calculate:
- Joint probability (independent): 39%
- Combined decimal odds: 3.64x
- Combined EV: +46.4%
- Combined Kelly: 17.52%

## Calibration Data

The frontend loads provider calibration from backtest artifacts:

```
data/cache/backtests/baseline_sample_{market}_provider_metrics.json
```

Each provider's Brier score is used to adjust confidence in predictions:
- Lower Brier = Better calibration = Higher confidence
- Scores range from 0 (perfect) to 1 (worst)

## Future Enhancements

- [ ] Real-time odds from sportsbook APIs
- [ ] Correlation matrix visualization
- [ ] Historical performance tracking
- [ ] Portfolio analysis (multiple bets)
- [ ] Model comparison (different calibration methods)
- [ ] Mobile app (React Native)

## Testing

```bash
# Test single bet prediction
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"sportsbook":"draftkings","market":"passing_yards","player":"Patrick Mahomes","projection":300,"actual_or_estimate":310,"odds":-110}'

# Test health check
curl http://localhost:5000/health
```

## Notes

- **Educational Purpose:** This is a proof-of-concept for CS 4220 @ Georgia Tech.
- **Data Quality:** Predictions are only as good as the underlying calibration data and model.
- **Always Gamble Responsibly:** Expected value is long-term; variance in short-term results is expected.

## Contributing

Contributions are welcome! Please submit pull requests to `feat/frontend-ui` branch.

## License

This project is part of CS 4220 at Georgia Tech. Use for educational purposes only.
