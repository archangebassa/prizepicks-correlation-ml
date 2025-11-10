"""Tests for NFL backtest pipeline."""
import pytest
from pathlib import Path
import pandas as pd
import scripts.backtest_nfl as bn

def test_load_market_data():
    """Test market data loading with date filtering."""
    # Create tiny test DataFrame
    data = {
        'Date': ['2024-09-01', '2024-09-08', '2024-12-31'],
        'QB_PassYds': [300, 250, 400],
        'QB_PassYds_actual': [280, 260, 390],
        'WR_RecYds': [100, 80, 150],
        'WR_RecYds_actual': [90, 85, 140]
    }
    df = pd.DataFrame(data)
    
    # Save as test CSV
    test_dir = Path('data/cache')
    test_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(test_dir / 'merged_eval.csv', index=False)
    
    # Test date filtering
    result = bn.load_market_data('2024-09-01', '2024-09-08', 'passing_yards')
    assert len(result) == 2  # Should only include first two rows
    
    # Test market column mapping
    assert 'projection' in result.columns
    assert 'actual' in result.columns

def test_run_market_backtest(tmp_path):
    """Test backtest execution and output generation."""
    # Create sample data with both positive and negative examples
    df = pd.DataFrame({
        'Date': ['2024-09-01', '2024-09-08'],
        'p_hit': [0.6, 0.4],
        'outcome': [1, 0],
        'provider': ['DraftKings', 'FanDuel']
    })
    
    # Run backtest
    results = bn.run_market_backtest(
        df,
        market='passing_yards',
        out_dir=tmp_path,
        date_tag='20240901_20240908'
    )
    
    # Check outputs
    assert (tmp_path / '20240901_20240908_passing_yards.json').exists()
    assert (tmp_path / '20240901_20240908_passing_yards_calibration.png').exists()
    assert (tmp_path / '20240901_20240908_passing_yards_roc.png').exists()