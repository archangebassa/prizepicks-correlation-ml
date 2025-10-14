import pandas as pd

def canonicalize_opp(col):
    return col

def join_qb_wr(team_df, qb_df, wr_df):
    base = team_df[['Date','Season','Week','Opponent','is_away']].dropna()
    out = base.merge(qb_df[['Date','QB_PassYds','QB_PassTD']], on='Date', how='left')
    out = out.merge(wr_df[['Date','WR_RecYds','WR_RecTD']], on='Date', how='left')
    out = out.dropna(subset=['QB_PassYds','WR_RecYds'])
    out['Diff_PF_PA'] = out['PF'] - out['PA'] if 'PF' in out.columns and 'PA' in out.columns else 0
    return out

def clean_numeric(df):
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = pd.to_numeric(df[c], errors='ignore')
    return df
