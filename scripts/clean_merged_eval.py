import argparse
from pathlib import Path
import pandas as pd

"""Clean merged evaluation CSVs by removing season-aggregate / implausible rows.

This script applies conservative filters to drop rows that look like season totals
or otherwise unrealistic per-game values (very large yardage, target counts, etc.).

Usage:
  python scripts/clean_merged_eval.py --in data/samples/merged_eval.csv --out data/samples/merged_eval_clean.csv
"""


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    # Coerce common numeric columns
    num_cols = ['QB_PassYds', 'WR_RecYds', 'Rec', 'Tgt', 'PF', 'PA']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    # Start with all rows marked as good
    keep = pd.Series(True, index=df.index)

    # Heuristic: some scraped tables are season-to-date (cumulative) rather than
    # per-game. Detect cumulative patterns for receiving columns and convert to
    # per-game by differencing where appropriate.
    def detect_and_diff(col_name: str, max_threshold: float = 200.0):
        """If the series looks monotonic non-decreasing and has a large max,
        convert it to per-game diffs (first value kept as-is). Returns True if
        conversion was applied."""
        if col_name not in df.columns:
            return False
        s = df[col_name].ffill()
        # require at least 3 non-null values to consider conversion
        if s.dropna().shape[0] < 3:
            return False
        is_mono = s.dropna().is_monotonic_increasing
        # also convert if the median increment is meaningfully positive
        inc = s.diff().dropna()
        median_inc = inc.median() if not inc.empty else 0
        if is_mono and (s.max() > max_threshold or median_inc > 1):
            # convert to per-game: first value as-is, then differences
            diff = s.diff().fillna(s)
            # If differencing produced negative values (unlikely for cumulative), abort
            if (diff < 0).any():
                return False
            df[col_name] = diff
            return True
        return False

    # Try detect/convert for usual cumulative columns
    converted_any = False
    for c in ['WR_RecYds', 'Rec', 'Tgt']:
        try:
            if detect_and_diff(c, max_threshold=300.0):
                converted_any = True
        except Exception:
            continue

    # Rule 1: drop rows where WR receiving yards are implausibly large for a single game
    if 'WR_RecYds' in df.columns:
        # after conversion, 400+ yards is still unrealistic; before conversion we
        # allowed larger values because they may be cumulative.
        keep &= ~(df['WR_RecYds'] > 500)
        keep &= ~(df['WR_RecYds'] < 0)

    # Rule 2: drop rows with implausible target/rec counts
    if 'Rec' in df.columns:
        keep &= ~(df['Rec'] > 20)
        keep &= ~(df['Rec'] < 0)
    if 'Tgt' in df.columns:
        keep &= ~(df['Tgt'] > 40)
        keep &= ~(df['Tgt'] < 0)

    # Rule 3: drop rows where WR yards massively exceed QB yards times a factor
    if 'QB_PassYds' in df.columns and 'WR_RecYds' in df.columns:
        qb = df['QB_PassYds'].fillna(0).abs()
        keep &= ~((df['WR_RecYds'] > qb * 10) & (qb > 0))

    # Rule 4: drop rows missing all date columns (often aggregate rows have no date)
    date_cols_present = [c for c in ['Date_qb', 'Date_team', 'Date'] if c in df.columns]
    if date_cols_present:
        # keep rows where at least one date column is present
        any_date = ~df[date_cols_present].isna().all(axis=1)
        keep &= any_date

    cleaned = df[keep].copy()
    return cleaned


def main(in_path: str, out_path: str):
    p = Path(in_path)
    if not p.exists():
        raise FileNotFoundError(in_path)

    df = pd.read_csv(p)
    before = len(df)
    cleaned = clean_df(df)
    after = len(cleaned)

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(outp, index=False)

    print(f'Cleaned {in_path}: {before} -> {after} rows (removed {before-after})')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_path', required=True)
    parser.add_argument('--out', dest='out_path', required=True)
    args = parser.parse_args()
    main(args.in_path, args.out_path)
