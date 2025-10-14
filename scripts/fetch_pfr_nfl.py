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
    # First attempt: direct parse
    try:
        tables = pd.read_html(StringIO(html), header=header)
        if tables:
            return tables
    except Exception:
        # fall through to comment-handling
        pass

    # Fallback: sports-reference sites often include tables inside HTML comments
    # to avoid simple scraping. Use BeautifulSoup to extract commented sections
    # that contain <table> and parse them with pandas.
    try:
        from bs4 import BeautifulSoup, Comment
    except Exception:
        raise

    soup = BeautifulSoup(html, "html.parser")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    tables = []
    for c in comments:
        if "<table" in c:
            try:
                found = pd.read_html(StringIO(str(c)), header=header)
                tables.extend(found)
            except Exception:
                continue

    if not tables:
        # Last resort: return empty list which callers should handle
        raise ValueError("No tables found in HTML (including commented sections)")

    return tables


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

    # Find candidate tables that include an Opponent column and at least one
    # plausible score/stat column. PFR team pages use slightly different
    # column names across seasons, so be flexible here.
    def cols(df):
        try:
            return set(df.columns.astype(str))
        except Exception:
            return set()

    score_candidates = {"PF", "PA", "Tm", "Opp.1", "Pts", "Tm.1"}
    candidates = [t for t in tables if ("Opp" in cols(t) or "Opponent" in cols(t)) and cols(t).intersection(score_candidates)]
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
    elif "Opponent" in df.columns:
        pass

    # Normalize score columns: try to find team score (PF) and opponent score (PA)
    if "PF" not in df.columns:
        if "Tm" in df.columns:
            df = df.rename(columns={"Tm": "PF"})
        elif "Tm.1" in df.columns:
            df = df.rename(columns={"Tm.1": "PF"})
    if "PA" not in df.columns:
        if "Opp.1" in df.columns:
            df = df.rename(columns={"Opp.1": "PA"})
        elif "Pts" in df.columns:
            # ambiguous, do not overwrite if PF exists
            if "PF" not in df.columns:
                df = df.rename(columns={"Pts": "PF"})

    # Determine home/away: search for any column with '@' markers in values
    is_away = 0
    for c in df.columns:
        if df[c].astype(str).str.contains("@", na=False).any():
            # create normalized is_away column based on '@' marker
            df["is_away"] = df[c].astype(str).eq("@").astype(int)
            is_away = 1
            break
    if not is_away:
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
    try:
        tables = _read_tables_from_html(html, header=1)
    except Exception:
        # Fallback: try canonical player page (strip 'gamelog/*' to 'players/X/Name.htm')
        if player_id_url.endswith('/'):
            base = player_id_url.rstrip('/')
        else:
            base = player_id_url
        if "/gamelog" in base:
            canonical = base.split('/gamelog')[0] + '.htm'
            html = _fetch_html(canonical)
            tables = _read_tables_from_html(html, header=1)
        else:
            raise

    candidates = [t for t in tables if {"Cmp", "Att", "Yds", "TD"}.issubset(set(t.columns.astype(str)))]
    if not candidates:
        raise RuntimeError("QB game log table not found.")
    df = candidates[0].copy()

    # Keep only real rows (Rk numeric) when available
    if "Rk" in df.columns:
        df = df[pd.to_numeric(df["Rk"], errors="coerce").notna()]

    # Normalize date column
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # flexible column finder (handles duplicates like 'Yds', 'Yds.1', ...)
    def find_col(df, names):
        cols = list(df.columns.astype(str))
        for n in names:
            # exact
            if n in cols:
                return n
        # prefix match (e.g. 'Yds.1')
        for n in names:
            for c in cols:
                if c.startswith(n + ".") or c == n:
                    return c
        return None

    yds_col = find_col(df, ["Yds", "Pass Yds", "PYds"])
    td_col = find_col(df, ["TD", "Pass TD"])
    cmp_col = find_col(df, ["Cmp"])
    att_col = find_col(df, ["Att"])

    if yds_col:
        df = df.rename(columns={yds_col: "QB_PassYds"})
    if td_col:
        df = df.rename(columns={td_col: "QB_PassTD"})

    # Handle alternate game-number columns (G#, Gtm, Gcar, G#)
    possible_game_cols = ["G#", "Gtm", "Gcar", "Gnum", "Gtm#"]
    game_col = next((c for c in possible_game_cols if c in df.columns), None)
    if game_col and game_col != "G#":
        df = df.rename(columns={game_col: "G#"})

    # Normalize opponent column variants
    possible_opp = ["Opp", "Opponent", "Unnamed: 6", "Vis", "HomeAway"]
    opp_col = next((c for c in possible_opp if c in df.columns), None)
    if opp_col and opp_col != "Opp":
        df = df.rename(columns={opp_col: "Opp"})

    # Ensure pass yards/td names exist
    # additional fallbacks already handled by find_col above

    # Pick whatever of the expected columns are present
    desired = ["Date", "G#", "Week", "Opp", "QB_PassYds", "QB_PassTD", cmp_col, att_col]
    keep = [c for c in desired if c in df.columns]
    out = df[keep].reset_index(drop=True)
    return out


def fetch_wr_gamelog(player_id_url: str) -> pd.DataFrame:
    """Fetch a WR/receiver game log (receiving stats) from a player gamelog URL.

    Returns a DataFrame with receiving yards and TD columns if available.
    """
    html = _fetch_html(player_id_url)
    try:
        tables = _read_tables_from_html(html, header=1)
    except Exception:
        # Fallback to canonical player page where many tables are embedded in comments
        if player_id_url.endswith('/'):
            base = player_id_url.rstrip('/')
        else:
            base = player_id_url
        if "/gamelog" in base:
            canonical = base.split('/gamelog')[0] + '.htm'
            html = _fetch_html(canonical)
            tables = _read_tables_from_html(html, header=1)
        else:
            raise

    candidates = [t for t in tables if {"Tgt", "Rec", "Yds", "TD"}.issubset(set(t.columns.astype(str)))]
    if not candidates:
        raise RuntimeError("WR game log table not found.")
    df = candidates[0].copy()

    if "Rk" in df.columns:
        df = df[pd.to_numeric(df["Rk"], errors="coerce").notna()]

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # flexible column finder reuse
    def find_col(df, names):
        cols = list(df.columns.astype(str))
        for n in names:
            if n in cols:
                return n
        for n in names:
            for c in cols:
                if c.startswith(n + ".") or c == n:
                    return c
        return None

    yds_col = find_col(df, ["Yds", "Rec Yds", "RecYds"])
    td_col = find_col(df, ["TD", "Rec TD"])
    rec_col = find_col(df, ["Rec"])
    tgt_col = find_col(df, ["Tgt"])

    if yds_col:
        df = df.rename(columns={yds_col: "WR_RecYds"})
    if td_col:
        df = df.rename(columns={td_col: "WR_RecTD"})

    # Normalize game number and opponent like QB parser
    possible_game_cols = ["G#", "Gtm", "Gcar", "Gnum", "Gtm#"]
    game_col = next((c for c in possible_game_cols if c in df.columns), None)
    if game_col and game_col != "G#":
        df = df.rename(columns={game_col: "G#"})

    possible_opp = ["Opp", "Opponent", "Unnamed: 6", "Vis", "HomeAway"]
    opp_col = next((c for c in possible_opp if c in df.columns), None)
    if opp_col and opp_col != "Opp":
        df = df.rename(columns={opp_col: "Opp"})

    desired = ["Date", "G#", "Week", "Opp", "WR_RecYds", "WR_RecTD", rec_col, tgt_col]
    keep = [c for c in desired if c in df.columns]
    out = df[keep].reset_index(drop=True)
    return out


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
