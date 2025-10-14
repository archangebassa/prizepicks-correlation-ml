import json
from pathlib import Path
from typing import Optional


def get_latest_cache(out_dir: Path, prefix: str) -> Optional[Path]:
    if not out_dir.exists():
        return None
    files = sorted([p for p in out_dir.iterdir() if p.name.startswith(prefix)], key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_json(path: Path):
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)
