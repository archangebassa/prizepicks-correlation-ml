import os
import json
import time
from pathlib import Path
import logging
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def _write_cache(data: Any, out_dir: Path, name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    path = out_dir / f"{name}.{ts}.json"
    with open(path, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info('Wrote cache to %s', path)
    return path


def fetch_from_provider(provider: str, api_key: str, params: Optional[Dict] = None) -> Dict:
    """Fetch PrizePicks-like projections from a third-party provider API.

    This function is a placeholder showing how to call a provider. Each
    provider will require its own endpoint, parameter mapping, and auth.
    """
    if not api_key:
        raise RuntimeError('Provider API key required')

    # Placeholder provider implementations. Add specific provider logic here.
    if provider.lower() == 'opticodds':
        url = 'https://api.opticodds.com/v1/prizepicks/projections'
        headers = {'Authorization': f'Bearer {api_key}'}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    if provider.lower() == 'betstamp':
        url = 'https://api.betstamp.io/prizepicks'
        headers = {'x-api-key': api_key}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    if provider.lower() in ('theoddsapi', 'theodds'):
        # The Odds API v4/v3 endpoints. Example docs: https://the-odds-api.com/
        # We'll call the odds endpoint for a sport (defaults to NFL) and return JSON.
        sport = (params or {}).get('sport', 'americanfootball_nfl')
        region = (params or {}).get('region', 'us')
        market = (params or {}).get('market', 'totals')
        url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds'
        # The Odds API uses an apiKey query parameter
        query = {'apiKey': api_key, 'regions': region, 'markets': market, 'oddsFormat': 'american'}
        r = requests.get(url, params=query, timeout=15)
        r.raise_for_status()
        return r.json()

    if provider.lower() in ('theoddsapi', 'oddsapi'):
        # The Odds API (https://the-odds-api.com) typically expects the API key as a query param 'apiKey'.
        # We'll default to fetching NFL odds (americanfootball_nfl) unless params override the sport_key.
        sport = (params or {}).get('sport', 'americanfootball_nfl')
        url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/'
        # default params: US region, totals and spreads markets, decimal odds
        default_params = {'regions': 'us', 'markets': 'totals,spreads', 'oddsFormat': 'decimal'}
        req_params = {} if params is None else dict(params)
        for k, v in default_params.items():
            req_params.setdefault(k, v)
        req_params['apiKey'] = api_key
        r = requests.get(url, params=req_params, timeout=15)
        r.raise_for_status()
        return r.json()

    raise NotImplementedError(f'Provider {provider} not implemented')


def normalize_provider_response(provider: str, data: Dict) -> 'pd.DataFrame':
    """Normalize provider JSON into a DataFrame with columns we use downstream.

    Output columns: Date, PlayerName, PlayerID (optional), Team, PropType, Line, Projection
    """
    import pandas as pd

    rows = []
    # Provider-specific mapping attempts
    if provider.lower() in ('theoddsapi', 'theodds'):
        # The Odds API returns a list of games with bookmakers and markets. We'll flatten totals/spreads/moneyline
        # Example item keys: {"id":"...","sport_key":"americanfootball_nfl","home_team":"NE Patriots","away_team":"KC Chiefs","bookmakers": [...]}
        for game in data or []:
            game_time = game.get('commence_time') or game.get('start_time')
            home = game.get('home_team')
            away = game.get('away_team')
            for bm in game.get('bookmakers', [])[:1]:  # pick first bookmaker to keep things simple
                for market in bm.get('markets', []):
                    mkey = market.get('key')
                    # for each outcome in market, create a row
                    for outcome in market.get('outcomes', []):
                        rows.append({
                            'Date': game_time,
                            'PlayerName': None,
                            'PlayerID': None,
                            'Team': home if outcome.get('name') == home else (away if outcome.get('name') == away else None),
                            'PropType': mkey,
                            'Line': outcome.get('point'),
                            # The Odds API uses 'price' as American odds; we convert to implied probability when possible
                            'Projection': None if outcome.get('price') is None else _american_odds_to_prob(outcome.get('price'))
                        })
        df = pd.DataFrame(rows)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    if provider.lower() == 'opticodds':
        # Hypothetical structure: {'projections': [{'player': 'X', 'team':'KC', 'prop':'rec_yds', 'line':55.5, 'projection':54.2, 'ts':'2023-10-01T...'}]}
        projs = data.get('projections') or data.get('data') or []
        for p in projs:
            rows.append({
                'Date': p.get('ts') or p.get('date'),
                'PlayerName': p.get('player') or p.get('name'),
                'PlayerID': p.get('player_id'),
                'Team': p.get('team'),
                'PropType': p.get('prop') or p.get('market'),
                'Line': p.get('line') or p.get('market_line') or p.get('value'),
                'Projection': p.get('projection') or p.get('pred')
            })
    elif provider.lower() == 'betstamp':
        # Hypothetical Betstamp format
        projs = data.get('items') or data.get('projections') or []
        for p in projs:
            rows.append({
                'Date': p.get('timestamp'),
                'PlayerName': p.get('player_name') or p.get('player'),
                'PlayerID': p.get('id'),
                'Team': p.get('team'),
                'PropType': p.get('market') or p.get('prop'),
                'Line': p.get('line'),
                'Projection': p.get('projection')
            })
    elif provider.lower() in ('theoddsapi', 'oddsapi'):
        # The Odds API returns a list of events with markets and bookmakers.
        # We'll flatten totals/spreads markets into rows. We create a human-readable "PlayerName"
        # field as the fixture identifier and use 'Projection' as the implied probability for the
        # relevant outcome (e.g., Over for totals). This is a pragmatic mapping so downstream
        # metrics/backtest code can operate on the data.
        events = data or []
        for ev in events:
            commence = ev.get('commence_time') or ev.get('start_time')
            home = ev.get('home_team') or ev.get('home')
            away = ev.get('away_team') or ev.get('away')
            fixture = f"{away} @ {home}" if home and away else ev.get('id') or ''
            # Some providers include multiple bookmakers; prefer the first/bookmaker with markets
            bookmakers = ev.get('bookmakers') or []
            for bm in bookmakers:
                for market in bm.get('markets', []):
                    mkey = market.get('key') or market.get('market_key')
                    outcomes = market.get('outcomes') or []
                    # totals: outcomes often have a 'point' field and 'name' = 'Over'/'Under'
                    if mkey == 'totals':
                        for o in outcomes:
                            name = o.get('name')
                            point = o.get('point') or o.get('price') or market.get('point')
                            price = o.get('price')
                            try:
                                proj = float(price)
                                # If price looks like decimal odds, convert to implied prob
                                implied = 1.0 / proj if proj > 0 else None
                            except Exception:
                                implied = None
                            rows.append({
                                'Date': commence,
                                'PlayerName': fixture,
                                'PlayerID': None,
                                'Team': None,
                                'PropType': f'game_total_{name.lower()}',
                                'Line': point,
                                'Projection': implied
                            })
                    elif mkey == 'spreads':
                        for o in outcomes:
                            name = o.get('name')
                            point = o.get('point')
                            price = o.get('price')
                            try:
                                proj = float(price)
                                implied = 1.0 / proj if proj > 0 else None
                            except Exception:
                                implied = None
                            rows.append({
                                'Date': commence,
                                'PlayerName': fixture,
                                'PlayerID': None,
                                'Team': name,
                                'PropType': 'spread',
                                'Line': point,
                                'Projection': implied
                            })
    else:
        # Generic attempt: search for list entries with common keys
        items = None
        for k in ('projections', 'data', 'items', 'results'):
            if k in data:
                items = data[k]
                break
        if items is None and isinstance(data, list):
            items = data
        items = items or []
        for p in items:
            rows.append({
                'Date': p.get('date') or p.get('ts'),
                'PlayerName': p.get('player_name') or p.get('player') or p.get('name'),
                'PlayerID': p.get('player_id') or p.get('id'),
                'Team': p.get('team'),
                'PropType': p.get('prop') or p.get('market'),
                'Line': p.get('line') or p.get('value'),
                'Projection': p.get('projection') or p.get('pred')
            })

    df = pd.DataFrame(rows)
    # Basic normalization
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df


def _american_odds_to_prob(odds: int) -> float:
    """Convert American odds to implied probability (0-1)."""
    try:
        o = int(odds)
    except Exception:
        return None
    if o > 0:
        return 100 / (o + 100)
    else:
        return -o / (-o + 100)


def _synthetic_provider_response(provider: str, n: int = 100):
    """Generate a synthetic provider response to test the adapter when network is not available."""
    import random, time
    items = []
    names = ['Player A','Player B','Player C','Player D']
    teams = ['KC','NE','DAL','NYJ']
    props = ['rec_yds','pass_yds','rush_yds']
    ts = int(time.time())
    for i in range(n):
        items.append({
            'ts': None,
            'date': None,
            'player': random.choice(names),
            'player_id': None,
            'team': random.choice(teams),
            'prop': random.choice(props),
            'line': round(random.uniform(10, 150), 1),
            'projection': round(random.uniform(5, 140), 1),
        })
    return {'projections': items}


def fetch_unofficial_prizepicks(projections_endpoint: str = 'https://api.prizepicks.com/projections') -> Dict:
    """Fetch from the (unofficial) PrizePicks endpoint.

    WARNING: This is an internal endpoint and may require special headers
    or session cookies. Using it in production/research carries risk and may
    violate PrizePicks' terms of service. Use with caution.
    """
    headers = {
        'User-Agent': 'python-requests/2.x',
        'Accept': 'application/json',
    }
    r = requests.get(projections_endpoint, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_by_scrape(url: str) -> Dict:
    """Fallback web-scraping approach: GET a page and extract lines.

    This is intentionally minimal: real scraping requires parsing JS-rendered
    content or using a headless browser, and must respect robots.txt and ToS.
    """
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return {'html': r.text}


def main(mode: str = 'unofficial', provider: Optional[str] = None, out_dir: str = 'data/samples/prizepicks', api_key: Optional[str] = None):
    out = Path(out_dir)
    if mode == 'provider':
        # prefer explicit api_key argument, fall back to environment variable
        api_key = api_key or os.environ.get('PRIZEPICKS_PROVIDER_KEY')
        if not provider:
            raise RuntimeError('Provider name required when mode=provider')
        if not api_key:
            raise RuntimeError('Provider API key required (set PRIZEPICKS_PROVIDER_KEY or pass --api-key)')
        logger.info('Fetching from provider %s', provider)
        data = fetch_from_provider(provider, api_key)
        _write_cache(data, out, f'provider_{provider}')
        return data

    if mode == 'unofficial':
        logger.info('Fetching from unofficial PrizePicks endpoint (may be unstable)')
        data = fetch_unofficial_prizepicks()
        _write_cache(data, out, 'prizepicks_unofficial')
        return data

    if mode == 'scrape':
        logger.info('Fetching by scraping (single URL placeholder)')
        data = fetch_by_scrape('https://app.prizepicks.com')
        _write_cache(data, out, 'prizepicks_scrape')
        return data

    raise RuntimeError('Unknown mode: ' + mode)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fetch PrizePicks projection/lines from provider/unofficial/scrape')
    parser.add_argument('--mode', choices=['provider', 'unofficial', 'scrape'], default='unofficial')
    parser.add_argument('--provider', help='Provider short name when mode=provider')
    parser.add_argument('--out', default='data/samples/prizepicks')
    parser.add_argument('--simulate', action='store_true', help='Generate synthetic provider response and normalize to CSV')
    parser.add_argument('--api-key', dest='api_key', help='Provider API key (optional; falls back to PRIZEPICKS_PROVIDER_KEY env var)')
    args = parser.parse_args()

    try:
        # allow a simulate flag via environment variable for dev
        if args.simulate:
            data = _synthetic_provider_response(args.provider or 'generic', n=200)
            df = normalize_provider_response(args.provider or 'generic', data)
            outdir = Path(args.out)
            outdir.mkdir(parents=True, exist_ok=True)
            outpath = outdir / f'prizepicks_{args.provider or "synthetic"}.csv'
            df.to_csv(outpath, index=False)
            print('Wrote synthetic provider CSV to', outpath)
        else:
            main(mode=args.mode, provider=args.provider, out_dir=args.out, api_key=args.api_key)
    except Exception as e:
        logger.exception('Fetch failed: %s', e)
