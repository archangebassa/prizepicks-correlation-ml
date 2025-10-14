"""Find the most recent provider JSON in data/cache/provider and normalize it to a CSV.

Usage: python -m scripts.normalize_cached_provider --provider theoddsapi --in-dir data/cache/provider --out data/cache/provider
"""
from pathlib import Path
import argparse
import json
import pandas as pd
from datetime import datetime

from scripts.fetch_prizepicks import normalize_provider_response


def latest_json(path: Path):
    files = list(path.glob('*.json'))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def main(provider: str, in_dir: str, out_dir: str):
    indir = Path(in_dir)
    outdir = Path(out_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    src = latest_json(indir)
    if not src:
        raise RuntimeError('No cached JSON found in ' + str(indir))
    print('Using cached JSON:', src)
    data = json.loads(src.read_text(encoding='utf8'))
    df = normalize_provider_response(provider, data)
    outpath = outdir / f'{provider}_normalized.csv'
    df.to_csv(outpath, index=False)
    print('Wrote normalized CSV to', outpath)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--provider', required=True)
    p.add_argument('--in-dir', default='data/cache/provider')
    p.add_argument('--out', dest='out_dir', default='data/cache/provider')
    args = p.parse_args()
    main(args.provider, args.in_dir, args.out_dir)
"""Normalize the most recent provider JSON cache into a CSV.

This script looks in data/cache/provider for files named like
provider_<provider>.<ts>.json and runs `normalize_provider_response` from
`scripts.fetch_prizepicks` to convert the JSON into a tabular CSV.

Run as: python -m scripts.normalize_cached_provider
"""
from pathlib import Path
import json
import sys

from scripts.fetch_prizepicks import normalize_provider_response


def main():
    base = Path('data/cache/provider')
    if not base.exists():
        print('No provider cache directory at', base)
        sys.exit(1)

    # find latest provider_theoddsapi.*.json and provider_* files
    files = sorted(base.glob('provider_*.json'), key=lambda f: f.stat().st_mtime)
    if not files:
        print('No provider JSON cache files found in', base)
        sys.exit(1)

    latest = files[-1]
    print('Normalizing', latest)
    with open(latest, 'r', encoding='utf8') as fh:
        data = json.load(fh)

    # guess provider from filename: provider_<provider>.<ts>.json
    name = latest.name.split('.')[0]
    parts = name.split('_', 1)
    provider = parts[1] if len(parts) > 1 else 'generic'

    df = normalize_provider_response(provider, data)
    out = base / f'{provider}_normalized.csv'
    df.to_csv(out, index=False)
    print('Wrote normalized CSV to', out)


if __name__ == '__main__':
    main()
