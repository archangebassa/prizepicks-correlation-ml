"""Fetch a small set of 2025 PFR gamelogs for demo/training.

This script calls existing `fetch_qb_gamelog`, `fetch_wr_gamelog`, and
`fetch_team_offense_gamelog` to save sample 2025 CSVs into `data/cache`.
"""
from pathlib import Path
from scripts.fetch_pfr_nfl import fetch_team_offense_gamelog, fetch_qb_gamelog, fetch_wr_gamelog, save_csv


def main(out_dir='data/cache'):
    outdir = Path(out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    team_df = fetch_team_offense_gamelog('KC', 2025)
    save_csv(team_df, outdir / 'nfl_kc_2025_team.csv')

    mahomes_2025 = 'https://www.pro-football-reference.com/players/M/MahoPa00/gamelog/2025/'
    qb_df = fetch_qb_gamelog(mahomes_2025)
    save_csv(qb_df, outdir / 'nfl_kc_mahomes_2025.csv')

    rice_2025 = 'https://www.pro-football-reference.com/players/R/RiceRa00/gamelog/2025/'
    wr_df = fetch_wr_gamelog(rice_2025)
    save_csv(wr_df, outdir / 'nfl_kc_rashee_rice_2025.csv')

    print('Wrote 2025 demo PFR CSVs to', outdir)


if __name__ == '__main__':
    main()
