# scripts/normalize.py
import pandas as pd

def canonicalize_opp(col):
    # Some tables use '@' markers or different codes; here we just pass through
    return col

def join_qb_wr(team_df, qb_df, wr_df):
    # Join on Date (PFR dates align across logs)
    base = team_df[['Date','Season','Week','Opponent','is_away']].dropna()
    out = base.merge(qb_df[['Date','QB_PassYds','QB_PassTD']], on='Date', how='left')
    out = out.merge(wr_df[['Date','WR_RecYds','WR_RecTD']], on='Date', how='left')

    # Drop rows with missing target stats for the demo
    out = out.dropna(subset=['QB_PassYds','WR_RecYds'])
    # Simple engineered features
    out['Diff_PF_PA'] = out['PF'] - out['PA'] if 'PF' in out.columns and 'PA' in out.columns else 0
    return out

def clean_numeric(df):
    for c in df.columns:
        if df[c].dtype == object:
            # attempt coercion for numeric-like
            df[c] = pd.to_numeric(df[c], errors='ignore')
    return df
