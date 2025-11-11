# 🚀 Quick Start: Frontend Web UI

## Running the Frontend Locally

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Flask Server
```bash
python frontend/app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Step 3: Open in Browser
Navigate to: **http://localhost:5000**

You should see the PrizePicks Correlation ML web UI with:
- **Single Bet Analysis** form (top section)
- **Multi-Leg Entry** builder (middle section)
- **How It Works** info cards (bottom section)

---

## Using the Interface

### Single Bet Analysis

1. **Fill the form:**
   - Sportsbook: Select from DraftKings, FanDuel, BetMGM, PointsBet
   - Market: Choose Passing Yards, Receiving Yards, or Rushing Yards
   - Player: Enter player name (e.g., "Patrick Mahomes")
   - Projection: Expected output from sportsbook
   - Estimated Value: Your estimate of actual output
   - Odds: American odds (e.g., -110, +150)
   - Stake: Optional bet amount (default $100)

2. **Click "Analyze Bet"**

3. **View Results:**
   - **Probability of Hit**: Your model's estimated probability
   - **Implied Probability**: What the sportsbook odds imply
   - **Expected Value**: EV in decimal and percentage
   - **Kelly Criterion**: Recommended bet size as % of bankroll
   - **Recommendation**: Summary with action (Strong Value, Avoid, etc.)

**Example:**
- Player: Patrick Mahomes
- Projection: 300 passing yards
- Estimate: 310
- Odds: -110
- Your p_hit: ~65% | Implied: ~52% | EV: +12.47% ✅ **Strong Value**

---

### Multi-Leg Analysis (Parlay)

1. **Click "+ Add Leg"** to add a bet
2. **Fill in each leg:**
   - Player name
   - p_hit (0.0 - 1.0)
   - Odds
3. **Repeat for multiple legs** (minimum 2)
4. **Click "Analyze Parlay"**

**Results show:**
- Joint probability (independent assumption)
- Combined decimal odds
- Parlay EV and Kelly criterion

**Example 2-Leg Parlay:**
- Leg 1: Mahomes O300 passing (p_hit 0.65)
- Leg 2: Kelce O75 receiving (p_hit 0.60)
- Joint Probability: 39% | EV: +46.4% | Kelly: 17.52%

---

## API Endpoints (for testing)

### Test Single Bet Prediction
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sportsbook": "draftkings",
    "market": "passing_yards",
    "player": "Patrick Mahomes",
    "projection": 300,
    "actual_or_estimate": 310,
    "odds": -110
  }'
```

### Test Health Check
```bash
curl http://localhost:5000/health
```

---

## Understanding the Results

### Expected Value (EV)
- **Positive EV (+)**: Bet has edge; long-term profitable
- **Negative EV (-)**: Avoid; will lose money long-term
- **~0 EV**: Skip unless high confidence

### Kelly Criterion
- **Recommended bet size** to maximize long-term growth
- e.g., Kelly = 5% → bet 5% of bankroll
- **Never bet full Kelly** on single bet; use half-Kelly for safety

### Confidence
- Based on calibration data and sample size
- Higher confidence = more reliable prediction

---

## Troubleshooting

### "Cannot connect to localhost:5000"
- Make sure Flask is running (`python frontend/app.py`)
- Check that no other app is using port 5000
- Try a different port: `app.run(port=5001)`

### "Calibration data not found"
- Backtest artifacts must exist in `data/cache/backtests/`
- Run baseline first: `python -m scripts.run_baseline`
- Or run tiny backtest: `python -m scripts.backtest_nfl --tiny`

### Predictions seem off
- Check that Projection vs Actual values are reasonable
- Verify Odds are in American format (-110, +150, etc.)
- Calibration data comes from sample dataset; larger dataset needed for accuracy

---

## Next Steps

1. **Test the UI** with sample data
2. **Integrate real odds** from sportsbook APIs
3. **Add correlation matrix** visualization for multi-leg
4. **Deploy to cloud** (Heroku, AWS, GCP)
5. **Mobile app** version (React Native)

---

## Documentation

See `frontend/README.md` for full API docs and technical details.

---

**Status:** ✅ Frontend ready for testing  
**Branch:** `feat/frontend-ui`  
**Next:** Review and merge to main
