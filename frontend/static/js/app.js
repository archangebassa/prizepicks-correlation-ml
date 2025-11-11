// PrizePicks Correlation ML - Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
    const singleBetForm = document.getElementById('singleBetForm');
    const addLegBtn = document.getElementById('addLegBtn');
    const analyzeMultiBtn = document.getElementById('analyzeMultiBtn');

    // Single Bet Form Submission
    singleBetForm.addEventListener('submit', (e) => {
        e.preventDefault();
        analyzeSingleBet();
    });

    // Multi-Leg Buttons
    addLegBtn.addEventListener('click', addLeg);
    analyzeMultiBtn.addEventListener('click', analyzeMultiLeg);

    // Initialize
    updateAnalyzeMultiButtonVisibility();
});

/**
 * Analyze a single bet
 */
async function analyzeSingleBet() {
    const form = document.getElementById('singleBetForm');
    const resultDiv = document.getElementById('singleResult');
    const errorDiv = document.getElementById('singleError');

    // Clear previous results
    resultDiv.style.display = 'none';
    errorDiv.style.display = 'none';

    // Collect form data
    const data = {
        sportsbook: document.getElementById('sportsbook').value,
        market: document.getElementById('market').value,
        player: document.getElementById('player').value,
        projection: parseFloat(document.getElementById('projection').value),
        actual_or_estimate: parseFloat(document.getElementById('actual').value),
        odds: parseFloat(document.getElementById('odds').value),
        correlations: [],
    };

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        const result = await response.json();

        if (!result.success) {
            showError(errorDiv, result.error);
            return;
        }

        // Display results
        const pred = result.prediction;
        const val = result.valuation;
        const conf = result.confidence;

        document.getElementById('resultPHit').textContent = pred.p_hit.toFixed(4);
        document.getElementById('resultPHitPct').textContent = `(${pred.p_hit_pct.toFixed(2)}%)`;
        
        document.getElementById('resultImplied').textContent = val.implied_prob.toFixed(4);
        document.getElementById('resultImpliedPct').textContent = `(${val.implied_prob_pct.toFixed(2)}%)`;
        
        document.getElementById('resultEV').textContent = val.ev.toFixed(4);
        document.getElementById('resultEVPct').textContent = `${val.ev_pct > 0 ? '+' : ''}${val.ev_pct.toFixed(2)}%`;
        
        document.getElementById('resultKelly').textContent = val.kelly_fraction.toFixed(4);
        document.getElementById('resultKellyPct').textContent = `${val.kelly_pct.toFixed(2)}% of bankroll`;

        // Generate recommendation
        const recommendation = generateRecommendation(pred, val, conf);
        const recDiv = document.querySelector('.recommendation');
        recDiv.innerHTML = recommendation;
        recDiv.className = 'recommendation ' + (val.ev > 0 ? 'positive' : val.ev < 0 ? 'negative' : 'neutral');

        resultDiv.style.display = 'block';
        window.scrollTo({ top: resultDiv.offsetTop - 100, behavior: 'smooth' });
    } catch (error) {
        showError(errorDiv, `Error: ${error.message}`);
    }
}

/**
 * Generate recommendation text
 */
function generateRecommendation(pred, val, conf) {
    const pHit = pred.p_hit;
    const implied = val.implied_prob;
    const ev = val.ev;
    const kelly = val.kelly_pct;

    let recommendation = '';
    let icon = '';

    if (ev > 0.05) {
        icon = '✅';
        recommendation = `<strong>${icon} Strong Value</strong><br>Your model predicts ${(pHit * 100).toFixed(1)}% probability, but the sportsbook only prices this at ${(implied * 100).toFixed(1)}%. This is a profitable bet with positive EV of ${val.ev_pct.toFixed(2)}%.`;
        if (kelly > 0) {
            recommendation += `<br><br>Recommended bet size: <strong>${kelly.toFixed(1)}% of your bankroll</strong> (Kelly Criterion).`;
        }
    } else if (ev > 0) {
        icon = '✔️';
        recommendation = `<strong>${icon} Slight Positive Value</strong><br>Small edge detected. EV of ${val.ev_pct.toFixed(2)}% suggests a marginal profit opportunity, but consider your confidence level before betting.`;
    } else if (ev > -0.05) {
        icon = '⚠️';
        recommendation = `<strong>${icon} Close Call</strong><br>Near break-even. Probability match: ${(pHit * 100).toFixed(1)}% vs ${(implied * 100).toFixed(1)}%. Unless you're very confident in your model, skip this one.`;
    } else {
        icon = '❌';
        recommendation = `<strong>${icon} Avoid - Negative EV</strong><br>The sportsbook has priced this better than your model predicts. Negative EV of ${val.ev_pct.toFixed(2)}% will lose money long-term.`;
    }

    return recommendation;
}

/**
 * Add a leg to the multi-leg entry
 */
function addLeg() {
    const legsList = document.getElementById('legsList');
    const legIndex = legsList.children.length;

    const legCard = document.createElement('div');
    legCard.className = 'leg-card';
    legCard.id = `leg-${legIndex}`;
    legCard.innerHTML = `
        <div style="display: flex; gap: 10px; flex: 1;">
            <input type="text" placeholder="Player" class="leg-player" value="">
            <input type="number" placeholder="p_hit" class="leg-p-hit" min="0" max="1" step="0.01" value="0.5">
            <input type="number" placeholder="Odds" class="leg-odds" value="-110">
        </div>
        <button type="button" class="leg-remove" onclick="removeLeg(${legIndex})">Remove</button>
    `;

    legsList.appendChild(legCard);
    updateAnalyzeMultiButtonVisibility();
}

/**
 * Remove a leg from multi-leg
 */
function removeLeg(index) {
    const leg = document.getElementById(`leg-${index}`);
    if (leg) {
        leg.remove();
    }
    updateAnalyzeMultiButtonVisibility();
}

/**
 * Show/hide analyze multi button based on leg count
 */
function updateAnalyzeMultiButtonVisibility() {
    const legsList = document.getElementById('legsList');
    const analyzeBtn = document.getElementById('analyzeMultiBtn');
    analyzeBtn.style.display = legsList.children.length >= 2 ? 'inline-block' : 'none';
}

/**
 * Analyze multi-leg entry
 */
async function analyzeMultiLeg() {
    const legsList = document.getElementById('legsList');
    const legs = [];

    legsList.querySelectorAll('.leg-card').forEach((card) => {
        const player = card.querySelector('.leg-player').value;
        const pHit = parseFloat(card.querySelector('.leg-p-hit').value) || 0.5;
        const odds = parseFloat(card.querySelector('.leg-odds').value) || -110;

        legs.push({ player, p_hit: pHit, odds });
    });

    if (legs.length < 2) {
        alert('Add at least 2 legs for a parlay');
        return;
    }

    try {
        const response = await fetch('/api/multi-leg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ legs, correlation_matrix: null }),
        });

        const result = await response.json();

        if (!result.success) {
            alert(`Error: ${result.error}`);
            return;
        }

        // Display multi-leg results
        const multi = result.multi_leg;
        document.getElementById('resultJointProb').textContent = multi.joint_probability_independent.toFixed(4);
        document.getElementById('resultJointProbPct').textContent = `(${multi.joint_probability_pct.toFixed(2)}%)`;
        document.getElementById('resultCombinedPayout').textContent = `${multi.combined_decimal_odds.toFixed(2)}x`;
        document.getElementById('resultParleyEV').textContent = multi.combined_ev.toFixed(4);
        document.getElementById('resultParleyEVPct').textContent = `${multi.combined_ev_pct > 0 ? '+' : ''}${multi.combined_ev_pct.toFixed(2)}%`;
        document.getElementById('resultCombinedKelly').textContent = multi.combined_kelly_fraction.toFixed(4);
        document.getElementById('resultCombinedKellyPct').textContent = `${multi.combined_kelly_pct.toFixed(2)}% of bankroll`;

        document.getElementById('multiResult').style.display = 'block';
        window.scrollTo({ top: document.getElementById('multiResult').offsetTop - 100, behavior: 'smooth' });
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

/**
 * Display error message
 */
function showError(errorDiv, message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    window.scrollTo({ top: errorDiv.offsetTop - 100, behavior: 'smooth' });
}

/**
 * Format odds display
 */
function formatOdds(odds) {
    if (odds < 0) {
        return `${odds}`;
    } else {
        return `+${odds}`;
    }
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return `$${amount.toFixed(2)}`;
}
