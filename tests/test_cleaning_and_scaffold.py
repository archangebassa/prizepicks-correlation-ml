import importlib.util
from pathlib import Path
import scripts.clean_merged_eval as cleaner
import scripts.fetch_prizepicks as fp


def test_clean_detects_and_diffs():
    # prepare a tiny cumulative-like dataframe
    import pandas as pd
    df = pd.DataFrame({
        'WR_RecYds': [10, 30, 60, 100],
        'Rec': [1, 3, 6, 10],
        'Date_qb': ['2023-09-01', '2023-09-08', '2023-09-15', '2023-09-22']
    })
    cleaned = cleaner.clean_df(df.copy())
    # After differencing, values should be per-game
    assert list(cleaned['WR_RecYds']) == [10, 20, 30, 40]


def test_fetch_prizepicks_scaffold_loading():
    # Ensure the scaffold functions exist and do not perform network on import
    assert hasattr(fp, 'fetch_unofficial_prizepicks')
    assert hasattr(fp, 'fetch_from_provider')
