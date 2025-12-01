"""
Flask application for PrizePicks Correlation ML frontend.

Provides a web UI for:
- Entering bet parameters (player, projection, odds, sportsbook)
- Computing probability and expected value
- Displaying calibration-adjusted predictions
- Multi-leg entry analysis
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
sys.path.insert(0, str(Path(__file__).parent))  # Add frontend directory for odds module

# Import scipy for normal distribution
from scipy.stats import norm

try:
    from metrics import compute_metrics
except Exception as e:
    print(f"Warning: Could not import metrics: {e}")
    compute_metrics = None

# Import odds module
try:
    from odds import get_best_odds, american_to_decimal, american_to_implied_probability, POPULAR_PLAYERS, MARKETS, SPORTSBOOKS
except Exception as e:
    print(f"Warning: Could not import odds module: {e}")
    get_best_odds = None
    POPULAR_PLAYERS = ['Patrick Mahomes', 'Travis Kelce', 'Isaiah Pacheco']
    MARKETS = ['passing_yards', 'receiving_yards', 'rushing_yards']
    SPORTSBOOKS = ['DraftKings', 'FanDuel', 'BetMGM', 'PointsBet']

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

# Load provider calibration data if available
PROVIDER_DATA = {}
try:
    provider_files = Path('data/cache/backtests').glob('*_provider_metrics.json')
    for pf in provider_files:
        with open(pf, 'r') as f:
            PROVIDER_DATA[pf.stem] = json.load(f)
except Exception as e:
    print(f"Warning: Could not load provider calibration data: {e}")


@app.route('/')
def index():
    """Render the main bet input page."""
    return render_template('index.html')


@app.route('/landing')
def landing():
    """Render the new SaaS-style landing page for demos."""
    return render_template('landing.html')


@app.route('/api/sportsbooks', methods=['GET'])
def get_sportsbooks():
    """Return list of available sportsbooks."""
    sportsbooks = [
        {'name': 'DraftKings', 'id': 'draftkings'},
        {'name': 'FanDuel', 'id': 'fanduel'},
        {'name': 'BetMGM', 'id': 'betmgm'},
        {'name': 'PointsBet', 'id': 'pointsbet'},
    ]
    return jsonify(sportsbooks)


@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Return list of available markets."""
    markets = [
        {'name': 'Passing Yards', 'id': 'passing_yards'},
        {'name': 'Receiving Yards', 'id': 'receiving_yards'},
        {'name': 'Rushing Yards', 'id': 'rushing_yards'},
    ]
    return jsonify(markets)


@app.route('/api/odds', methods=['GET'])
def get_odds_endpoint():
    """
    Get live or mock odds for a player/market combination.
    
    Query params:
    - player: Player name (e.g., "Patrick Mahomes")
    - market: Market type (e.g., "passing_yards")
    - sportsbook: Optional specific sportsbook
    """
    player = request.args.get('player')
    market = request.args.get('market')
    sportsbook = request.args.get('sportsbook')
    
    if not player or not market:
        return jsonify({'error': 'Missing player or market parameter'}), 400
    
    try:
        if get_best_odds:
            odds = get_best_odds(player, market, sportsbook)
            return jsonify({'success': True, 'data': odds})
        else:
            return jsonify({'success': False, 'error': 'Odds module not available'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/autocomplete/players', methods=['GET'])
def autocomplete_players():
    """Return list of popular players for autocomplete."""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify(POPULAR_PLAYERS[:10])
    
    matches = [p for p in POPULAR_PLAYERS if query in p.lower()]
    return jsonify(matches[:10])


@app.route('/api/autocomplete/markets', methods=['GET'])
def autocomplete_markets():
    """Return list of available markets."""
    return jsonify(MARKETS)


@app.route('/api/autocomplete/sportsbooks', methods=['GET'])
def autocomplete_sportsbooks():
    """Return list of available sportsbooks."""
    return jsonify(SPORTSBOOKS)


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Compute probability, EV, and Kelly criterion for a single bet.
    
    Request JSON:
    {
        "sportsbook": "draftkings",
        "market": "passing_yards",
        "player": "Patrick Mahomes",
        "projection": 300,
        "actual_or_estimate": 300,
        "odds": -110,
        "correlations": [
            {"player": "Travis Kelce", "correlation": 0.65}
        ]
    }
    """
    try:
        data = request.get_json()
        
        # Extract inputs
        sportsbook = data.get('sportsbook', 'draftkings').lower()
        market = data.get('market', 'passing_yards')
        player = data.get('player', 'Unknown')
        projection = float(data.get('projection', 0))
        actual = float(data.get('actual_or_estimate', 0))
        odds = float(data.get('odds', -110))
        correlations = data.get('correlations', [])
        
        # Calculate probability of hitting
        p_hit = 0.5  # Default baseline
        if projection > 0:
            # Simple model: p_hit based on how far actual is from projection
            diff = actual - projection
            std_dev = projection * 0.15  # Assume 15% std deviation
            if std_dev > 0:
                # Simplified: assume normal distribution
                p_hit = 1 - norm.cdf(0, loc=diff, scale=std_dev)
                p_hit = max(0.05, min(0.95, p_hit))  # Clip to [0.05, 0.95]
        
        # Adjust for provider calibration if available
        provider_key = f"baseline_sample_{market}"
        if provider_key in PROVIDER_DATA:
            provider_data = PROVIDER_DATA[provider_key]
            # Simple adjustment: use provider's average Brier to adjust confidence
            if 'provider_metrics' in provider_data and sportsbook.title() in provider_data['provider_metrics']:
                brier = provider_data['provider_metrics'][sportsbook.title()].get('brier_score', 0.5)
                # Lower Brier = better calibration; adjust p_hit slightly
                calibration_factor = 1 - (brier * 0.1)
                p_hit *= calibration_factor
                p_hit = max(0.05, min(0.95, p_hit))
        
        # Convert American odds to implied probability
        if odds < 0:
            implied_prob = abs(odds) / (abs(odds) + 100)
        else:
            implied_prob = 100 / (odds + 100)
        
        # Calculate EV
        decimal_odds = (abs(odds) + 100) / 100 if odds < 0 else odds / 100 + 1
        payout = decimal_odds - 1
        ev = (p_hit * payout) - (1 - p_hit)
        roi_pct = (ev * 100)
        
        # Kelly Criterion: f* = (bp - q) / b where b=payout, p=p_hit, q=1-p_hit
        kelly = (payout * p_hit - (1 - p_hit)) / payout if payout > 0 else 0
        kelly = max(0, kelly)  # Don't suggest negative
        kelly_pct = kelly * 100
        
        # Confidence: based on sample size and calibration
        confidence = min(0.95, p_hit) if p_hit > 0.5 else min(0.95, 1 - p_hit)
        
        response = {
            'success': True,
            'prediction': {
                'player': player,
                'market': market,
                'sportsbook': sportsbook,
                'projection': projection,
                'estimated_value': round(actual, 2),
                'p_hit': round(p_hit, 4),
                'p_hit_pct': round(p_hit * 100, 2),
                'implied_prob': round(implied_prob, 4),
                'implied_prob_pct': round(implied_prob * 100, 2),
            },
            'valuation': {
                'odds': odds,
                'decimal_odds': round(decimal_odds, 2),
                'ev': round(ev, 4),
                'ev_pct': round(roi_pct, 2),
                'kelly_fraction': round(kelly, 4),
                'kelly_pct': round(kelly_pct, 2),
                'recommended_bet_size_pct': round(kelly_pct, 2),
            },
            'confidence': {
                'model_confidence': round(confidence, 2),
                'confidence_pct': round(confidence * 100, 2),
                'note': 'Confidence based on calibration data and sample size',
            },
            'correlations': correlations,
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/multi-leg', methods=['POST'])
def predict_multi_leg():
    """
    Compute joint probability and EV for multi-leg entries.
    
    Request JSON:
    {
        "legs": [
            {
                "player": "Patrick Mahomes",
                "market": "passing_yards",
                "p_hit": 0.65,
                "odds": -110
            },
            ...
        ],
        "correlation_matrix": [[1.0, 0.5], [0.5, 1.0]]  # Optional
    }
    """
    try:
        data = request.get_json()
        legs = data.get('legs', [])
        correlation_matrix = data.get('correlation_matrix', None)
        
        if not legs:
            return jsonify({'success': False, 'error': 'No legs provided'}), 400
        
        # Simple independent probability (no correlation)
        joint_prob = 1.0
        for leg in legs:
            joint_prob *= leg.get('p_hit', 0.5)
        
        # TODO: Apply correlation_matrix adjustment if provided
        # For now, just use independent
        
        # Calculate combined odds and payout
        combined_decimal_odds = 1.0
        for leg in legs:
            odds = leg.get('odds', -110)
            if odds < 0:
                decimal = (abs(odds) + 100) / 100
            else:
                decimal = odds / 100 + 1
            combined_decimal_odds *= decimal
        
        combined_payout = combined_decimal_odds - 1
        
        # EV for multi-leg
        combined_ev = (joint_prob * combined_payout) - (1 - joint_prob)
        combined_roi = combined_ev * 100
        
        # Kelly for multi-leg
        combined_kelly = (combined_payout * joint_prob - (1 - joint_prob)) / combined_payout if combined_payout > 0 else 0
        combined_kelly = max(0, combined_kelly)
        
        response = {
            'success': True,
            'multi_leg': {
                'num_legs': len(legs),
                'joint_probability_independent': round(joint_prob, 4),
                'joint_probability_pct': round(joint_prob * 100, 2),
                'combined_decimal_odds': round(combined_decimal_odds, 2),
                'combined_payout': round(combined_payout, 2),
                'combined_ev': round(combined_ev, 4),
                'combined_ev_pct': round(combined_roi, 2),
                'combined_kelly_fraction': round(combined_kelly, 4),
                'combined_kelly_pct': round(combined_kelly * 100, 2),
            },
            'legs': legs,
            'note': 'Joint probability calculated assuming independence; correlation adjustments coming soon',
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/calibration', methods=['GET'])
def get_calibration():
    """Return provider calibration data."""
    market = request.args.get('market', 'passing_yards')
    provider_key = f"baseline_sample_{market}"
    
    if provider_key in PROVIDER_DATA:
        return jsonify({
            'success': True,
            'market': market,
            'data': PROVIDER_DATA[provider_key]
        })
    else:
        return jsonify({
            'success': False,
            'error': f'No calibration data for market: {market}'
        }), 404


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'service': 'prizepicks-correlation-ml-api'})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
