# scripts/build_dataset_nfl.py
import pandas as pd
from pathlib import Path
from scripts.utils.normalize import join_qb_wr, clean_numeric

def build():
    team = pd.read_csv("data/cache/nfl_kc_2023_team.csv", parse_dates=['Date'])
    qb   = pd.read_csv("data/cache/nfl_kc_mahomes_2023.csv", parse_dates=['Date'])
    wr   = pd.read_csv("data/cache/nfl_kc_rashee_rice_2023.csv", parse_dates=['Date'])

    df = join_qb_wr(team, qb, wr)
    df = clean_numeric(df)

    Path("data/cache").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/cache/nfl_features.csv", index=False)
    print("Wrote data/samples/nfl_features.csv")
    print(df.head())

if __name__ == "__main__":
    build()
