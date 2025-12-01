# PrizePicks Correlation ML - Setup & Running Guide

This guide will help you get the application running locally for grading and evaluation.

## Prerequisites

- **Python 3.8+** installed on your system
- **Git** installed (to clone the repository)
- **PowerShell** (Windows) or Terminal (macOS/Linux)

## Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/prizepicks-correlation-ml-1.git
cd prizepicks-correlation-ml-1
```

*(Replace `YOUR_USERNAME` with the actual GitHub username/org)*

## Step 2: Create and Activate Python Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Note:** If you encounter a PowerShell execution policy error on Windows, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required Python packages including:
- Flask (web framework)
- NumPy, Pandas (data processing)
- Scikit-learn (machine learning)
- Pytest (testing)

## Step 4: Verify Installation with Tests

Run the test suite to ensure everything is set up correctly:

```bash
pytest -q
```

You should see output like:
```
.....                                                                    [100%]
5 passed in X.XXs
```

All 5 tests should pass. If any fail, check that dependencies installed correctly.

## Step 5: Start the Flask Development Server

From the project root directory:

```bash
python frontend/app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

## Step 6: Access the Application

Open your web browser and navigate to:

**Main Application (React UI):**
```
http://127.0.0.1:5000/
```

**Alternative Landing Page:**
```
http://127.0.0.1:5000/modern
```

**Health Check Endpoint:**
```
http://127.0.0.1:5000/health
```

## Using the Application

### Single Bet Analysis

1. Select a **Sportsbook** (DraftKings, FanDuel, etc.)
2. Fill in the bet details:
   - **Player**: e.g., "Patrick Mahomes"
   - **Market**: Select from dropdown (Passing Yards, Receiving Yards, Rushing Yards)
   - **Odds**: e.g., "-110" (American format) or "1.91" (decimal)
   - **Projection**: Your model's forecast (e.g., "320" yards)
   - **Actual/Line**: The sportsbook line (e.g., "335" yards)
3. Click **Analyze Bet**
4. View results in the Summary panel:
   - **Probability**: Model's predicted hit rate
   - **Expected Value (EV)**: Average profit per $1 wagered
   - **Kelly Fraction**: Recommended bet size as % of bankroll

### Parlay Analysis

1. Check the **Parlay** checkbox in the top-right
2. Fill in details for the first leg
3. Click **Add Leg** to add more legs (minimum 2 for parlay)
4. Fill in all legs with player, market, projection, line, and odds
5. Click **Analyze Parlay**
6. View combined results:
   - **Joint Probability**: Combined probability of all legs hitting
   - **Combined EV**: Expected value for the parlay
   - **Combined Odds**: Parlay payout multiplier

### Advanced Features

- **Show Raw Response**: Click this button to see the full JSON returned by the API
- **Copy JSON**: Copy the response to clipboard for debugging
- **Reset**: Clear the form and start over

## API Endpoints (for Testing)

You can test the API directly using `curl` or PowerShell:

### Health Check
```bash
curl http://127.0.0.1:5000/health
```

### Single Bet Prediction
**PowerShell:**
```powershell
$body = @{
    sportsbook='draftkings'
    market='passing_yards'
    player='Patrick Mahomes'
    projection=320
    actual_or_estimate=335
    odds=-110
    correlations=@{}
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/predict' -Method Post -Body $body -ContentType 'application/json'
```

**curl:**
```bash
curl -X POST http://127.0.0.1:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sportsbook": "draftkings",
    "market": "passing_yards",
    "player": "Patrick Mahomes",
    "projection": 320,
    "actual_or_estimate": 335,
    "odds": -110,
    "correlations": {}
  }'
```

### Multi-Leg Parlay
**PowerShell:**
```powershell
$body = @{
    legs=@(
        @{player='Patrick Mahomes'; market='passing_yards'; projection=320; actual_or_estimate=335; odds=-110},
        @{player='Travis Kelce'; market='receiving_yards'; projection=85; actual_or_estimate=90; odds=-110}
    )
    correlation_matrix=$null
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/multi-leg' -Method Post -Body $body -ContentType 'application/json'
```

## Project Structure

```
prizepicks-correlation-ml-1/
├── frontend/
│   ├── app.py                      # Flask application (main entry point)
│   ├── templates/
│   │   ├── index_modern.html       # Main React UI template
│   │   └── modern.html             # Alternative landing page
│   └── static/
│       ├── js/
│       │   ├── react-home.jsx      # Main React application
│       │   └── modern-home.js      # Landing page component
│       └── css/
│           └── modern-demo.css     # Global styles
├── backend/
│   └── (model logic, calibration, prediction engines)
├── tests/
│   └── test_*.py                   # Test files
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## Troubleshooting

### Port 5000 Already in Use
If you see an error that port 5000 is already in use:

**Windows:**
```powershell
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -ti:5000 | xargs kill -9
```

Or change the port in `frontend/app.py`:
```python
app.run(debug=True, port=5001)  # Use port 5001 instead
```

### Virtual Environment Not Activating (Windows)
If `.venv\Scripts\Activate.ps1` fails with a security error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Module Not Found Errors
If you see `ModuleNotFoundError`:
```bash
pip install -r requirements.txt --force-reinstall
```

### Browser Shows Old Version
Hard refresh your browser:
- **Windows/Linux**: `Ctrl + Shift + R`
- **macOS**: `Cmd + Shift + R`

## Features Demonstrated

### Model Capabilities
- ✅ Single bet probability prediction using projection vs. sportsbook line
- ✅ Expected value (EV) calculation
- ✅ Kelly criterion bet sizing
- ✅ Multi-leg parlay analysis with joint probability
- ✅ Confidence metrics based on historical calibration
- ✅ Support for multiple markets (passing, receiving, rushing yards)

### UI/UX
- ✅ Modern React + Tailwind CSS interface
- ✅ Responsive design (mobile-friendly)
- ✅ Real-time probability calculation display
- ✅ Form validation with error messages
- ✅ Debug tools (raw JSON viewer)
- ✅ Sportsbook selection (tracking)

### Backend
- ✅ RESTful API endpoints
- ✅ JSON request/response format
- ✅ Comprehensive test coverage (pytest)
- ✅ Health check endpoint for monitoring

## Contact & Support

For questions or issues during grading, please contact:
- **GitHub Issues**: [Create an issue](https://github.com/YOUR_USERNAME/prizepicks-correlation-ml-1/issues)
- **Email**: 02archange@gmail.com

---

**Last Updated**: November 30, 2025
