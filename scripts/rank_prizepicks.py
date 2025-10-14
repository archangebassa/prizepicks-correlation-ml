import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from sklearn.linear_model import LinearRegression
from math import erf, sqrt

"""Rank PrizePicks-like props using a simple regression projection + normal residuals.

Usage example:
  python scripts/rank_prizepicks.py --features data/samples/features.csv --line 55.5

This will print P(hit_over) and a simple EV assuming even-money payout (1:1 net).
"""


def normal_cdf(x):
    # standard normal CDF using erf
    return 0.5 * (1 + erf(x / sqrt(2)))


def estimate_projection(df, x_col='QB_PassYds', y_col='WR_RecYds'):
    X = df[[x_col]].dropna().values.reshape(-1, 1)
    y = df[y_col].dropna().values
    if len(X) < 2:
        raise RuntimeError('Not enough data to fit regression')
    model = LinearRegression().fit(X, y)
    preds = model.predict(X)
    residuals = y - preds
    sigma = np.std(residuals, ddof=1)
    return model, sigma


def compute_p_hit(proj_mean, sigma, line):
    # P(WR >= line) assuming normal(proj_mean, sigma)
    if sigma == 0 or np.isnan(sigma):
        return 1.0 if proj_mean >= line else 0.0
    z = (line - proj_mean) / sigma
    return 1 - normal_cdf(z)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--features', required=True)
    parser.add_argument('--line', required=True, type=float, help='PrizePicks line to evaluate (e.g., 55.5)')
    parser.add_argument('--payout', default=2.0, type=float, help='Total payout multiplier (default=2.0 -> even-money)')
    args = parser.parse_args()

    p = Path(args.features)
    if not p.exists():
        raise FileNotFoundError(args.features)
    df = pd.read_csv(p)

    # fit regression on the historical rows available
    model, sigma = estimate_projection(df)
    print('Regression coef (slope,intercept):', model.coef_[0], model.intercept_)
    print('Residual sigma (std):', sigma)

    # compute projection for each row and P(hit) for the provided line
    df['proj'] = model.predict(df[['QB_PassYds']].fillna(0).values.reshape(-1, 1))
    df['p_hit'] = df['proj'].apply(lambda m: compute_p_hit(m, sigma, args.line))

    # EV assuming stake=1 and payout multiplier
    R = args.payout
    df['ev'] = df['p_hit'] * (R - 1) - (1 - df['p_hit'])

    # show top candidates
    out = df[['Date','Week','Opp','QB_PassYds','WR_RecYds','proj','p_hit','ev']].sort_values('ev', ascending=False)
    print('\nTop candidate rows by EV:')
    print(out.head(10).to_string(index=False))


if __name__ == '__main__':
    main()
