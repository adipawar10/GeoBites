"""
Download NYC DOHMH restaurant inspection records (public SODA API).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from load_config import load_config


def fetch_inspections_page(url: str, params: dict[str, Any]) -> list[dict]:
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def acquire_raw(out_path: Path) -> Path:
    cfg = load_config()
    url = cfg["nyc_inspections"]["base_url"]
    limit = int(cfg["nyc_inspections"]["page_limit"])
    bbox = cfg["bbox"]

    where = (
        "latitude IS NOT NULL AND longitude IS NOT NULL AND "
        f"latitude between {bbox['lat_min']} and {bbox['lat_max']} AND "
        f"longitude between {bbox['lon_min']} and {bbox['lon_max']}"
    )
    all_rows: list[dict] = []
    try:
        offset = 0
        while True:
            params = {"$where": where, "$limit": limit, "$offset": offset}
            batch = fetch_inspections_page(url, params)
            if not batch:
                break
            all_rows.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
    except Exception as exc:  # noqa: BLE001 — network / proxy / air-gapped lab
        print(f"[acquire] Live download failed ({exc!r}). Using offline synthetic inspections.")
        from fallback_data import write_fallback

        return write_fallback(out_path)

    if len(all_rows) < 500:
        print("[acquire] Very few rows returned — using offline synthetic inspections.")
        from fallback_data import write_fallback

        return write_fallback(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(all_rows, f)
    return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    p = acquire_raw(root / "data" / "raw" / "inspections_manhattan_brooklyn.json")
    print(f"Wrote {p} ({p.stat().st_size // 1024} KB)")
