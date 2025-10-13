# scripts/fetch_pfr_nfl.py
"""Utilities to fetch Pro-Football-Reference (PFR) game logs.

This module keeps external dependencies minimal: it uses the Python stdlib
for HTTP requests and pandas for HTML table parsing (already present in
`requirements.txt`). The functions intentionally accept PFR-style URLs for
player game logs and a small team-code mapping for team pages.

Notes / constraints:
- PFR may change page structure; functions try to be defensive but will
  raise clear errors when expected tables aren't found.
- No automatic player-name -> player-url resolver is provided here. You can
  add a simple lookup CSV (data/mapping/player_ids.csv) mapping player names
  to PFR URL suffixes if you want programmatic fetching by name.
"""

from pathlib import Path
import pandas as pd
import time
import random
import logging
import urllib.request
import urllib.error
from io import StringIO

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

PFR_TEAM_CODES = {
    # Extend this map as needed. Keys are common 2-3 letter team abbreviations
    # used elsewhere in the project; values are the PFR team slug used in URLs.
    "KC": "kan",  # Kansas City Chiefs
    "PHI": "phi",
    "DAL": "dal",
}


def _fetch_html(url: str, retries: int = 3, backoff: float = 1.0, timeout: int = 20) -> str:
    """Fetch HTML from a URL with a browser-like User-Agent and retry logic.

    Uses urllib from the stdlib so we don't add new pip dependencies.
    Returns the decoded HTML string on success or raises an informative error.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0 Safari/537.36"
        )
    }

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read()
                # Try to decode using resp headers if available
                encoding = resp.headers.get_content_charset(failobj="utf-8")
                html = content.decode(encoding, errors="replace")
                return html
        except urllib.error.HTTPError as e:
            last_exc = e
            logger.warning("HTTPError %s for %s (attempt %d)", e.code, url, attempt)
            if 400 <= e.code < 500:
                # client errors unlikely to be fixed by retrying
                break
        except Exception as e:
            last_exc = e
            logger.warning("Error fetching %s: %s (attempt %d)", url, e, attempt)

        # backoff with jitter
        sleep = backoff * (2 ** (attempt - 1)) + random.random() * 0.5
        time.sleep(sleep)

    raise RuntimeError(f"Failed to fetch {url}") from last_exc


def _read_tables_from_html(html: str, header: int = 1):
    """Helper: parse HTML into a list of DataFrames using pandas.read_html.

    Wraps the HTML string in a StringIO so pandas reads it as if it were a file.
    """
    return pd.read_html(StringIO(html), header=header)


def fetch_team_offense_gamelog(team_abbr: str, year: int) -> pd.DataFrame:
    """Fetch a team's game log page and return a cleaned offense game-log DataFrame.

    team_abbr should be a key in PFR_TEAM_CODES. The function looks for a
    table that contains at least the columns 'Opp', 'PF', and 'PA' and will
    return a narrowed, cleaned DataFrame with standard columns.
    """
    if team_abbr not in PFR_TEAM_CODES:
        raise KeyError(f"Unknown team abbreviation: {team_abbr}. Update PFR_TEAM_CODES.")

    code = PFR_TEAM_CODES[team_abbr]
    url = f"https://www.pro-football-reference.com/teams/{code}/{year}.htm"
    html = _fetch_html(url)
    tables = _read_tables_from_html(html, header=1)

    # Find candidate tables that include columns we expect
    def cols(df):
        try:
            return set(df.columns.astype(str))
        except Exception:
            return set()

    candidates = [t for t in tables if {"Opp", "PF", "PA"}.issubset(cols(t))]
    if not candidates:
        raise RuntimeError("Team game log table not found; site layout may have changed.")

    df = candidates[0].copy()

    # Some PFR tables include header rows inside the table; attempt to drop such rows
    if "Week" in df.columns:
        df = df.loc[~df["Week"].astype(str).str.contains("Week", na=False)]
        df = df[~df["Week"].isna()]

    df["Season"] = year

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Normalize opponent column name
    if "Opp" in df.columns:
        df = df.rename(columns={"Opp": "Opponent"})

    # Determine home/away if present in an 'Unnamed' column or 'Home/Away'
    home_cols = [c for c in df.columns if "Home" in str(c) or "Away" in str(c) or "Unnamed" in str(c)]
    if home_cols:
        # look for a column containing '@' markers
        col = home_cols[0]
        df["is_away"] = df[col].astype(str).eq("@").astype(int)
    else:
        df["is_away"] = 0

    # Select keep columns where available
    keep = [c for c in ["Season", "Week", "Date", "Opponent", "is_away", "PF", "PA"] if c in df.columns]
    out = df[keep].reset_index(drop=True)
    return out


def fetch_qb_gamelog(player_id_url: str) -> pd.DataFrame:
    """Fetch a QB game log from a player gamelog URL (PFR player gamelog page).

    Example URL: https://www.pro-football-reference.com/players/M/MahoPa00/gamelog/2023/
    Returns a DataFrame with renamed columns for passing yards/TDs.
    """
    html = _fetch_html(player_id_url)
    tables = _read_tables_from_html(html, header=1)

    candidates = [t for t in tables if {"Cmp", "Att", "Yds", "TD"}.issubset(set(t.columns.astype(str)))]
    if not candidates:
        raise RuntimeError("QB game log table not found.")
    df = candidates[0].copy()

    # Keep only real rows (Rk numeric)
    if "Rk" in df.columns:
        df = df[df["Rk"].apply(lambda x: str(x).isdigit())]

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # defensive rename if present
    if "Yds" in df.columns:
        df = df.rename(columns={"Yds": "QB_PassYds"})
    if "TD" in df.columns:
        df = df.rename(columns={"TD": "QB_PassTD"})

    keep = [c for c in ["Date", "G#", "Week", "Opp", "QB_PassYds", "QB_PassTD"] if c in df.columns]
    return df[keep].reset_index(drop=True)


def fetch_wr_gamelog(player_id_url: str) -> pd.DataFrame:
    """Fetch a WR/receiver game log (receiving stats) from a player gamelog URL.

    Returns a DataFrame with receiving yards and TD columns if available.
    """
    html = _fetch_html(player_id_url)
    tables = _read_tables_from_html(html, header=1)

    candidates = [t for t in tables if {"Tgt", "Rec", "Yds", "TD"}.issubset(set(t.columns.astype(str)))]
    if not candidates:
        raise RuntimeError("WR game log table not found.")
    df = candidates[0].copy()

    if "Rk" in df.columns:
        df = df[df["Rk"].apply(lambda x: str(x).isdigit())]

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    if "Yds" in df.columns:
        df = df.rename(columns={"Yds": "WR_RecYds"})
    if "TD" in df.columns:
        df = df.rename(columns={"TD": "WR_RecTD"})

    keep = [c for c in ["Date", "G#", "Week", "Opp", "WR_RecYds", "WR_RecTD"] if c in df.columns]
    return df[keep].reset_index(drop=True)


def save_csv(df: pd.DataFrame, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch PFR NFL game logs (demo).")
    parser.add_argument("--demo", action="store_true", help="Run the small demo fetch and save sample CSVs.")
    parser.add_argument("--out", default="data/samples", help="Output directory for demo CSV files.")
    args = parser.parse_args()

    if args.demo:
        outdir = Path(args.out)
        outdir.mkdir(parents=True, exist_ok=True)

        team_df = fetch_team_offense_gamelog("KC", 2023)
        save_csv(team_df, outdir / "nfl_kc_2023_team.csv")

        mahomes_2023 = "https://www.pro-football-reference.com/players/M/MahoPa00/gamelog/2023/"
        qb_df = fetch_qb_gamelog(mahomes_2023)
        save_csv(qb_df, outdir / "nfl_kc_mahomes_2023.csv")

        rice_2023 = "https://www.pro-football-reference.com/players/R/RiceRa00/gamelog/2023/"
        wr_df = fetch_wr_gamelog(rice_2023)
        save_csv(wr_df, outdir / "nfl_kc_rashee_rice_2023.csv")
    else:
        print("No action taken. Run with --demo to fetch example gamelogs and save CSVs.")
