"""
Generate synthetic DOHMH-style inspection rows when live download is unavailable.

Structure matches NYC SODA JSON enough for clean.py; coordinates are uniformly
sampled inside the project bbox with realistic score noise.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from load_config import load_config


def write_fallback(out_path: Path, n_camis: int = 4500, inspections_per_camis: int = 3) -> Path:
    cfg = load_config()
    bb = cfg["bbox"]
    rng = np.random.default_rng(7)

    rows = []
    camis_ids = [str(40000000 + i) for i in range(n_camis)]
    for camis in camis_ids:
        base_lat = rng.uniform(bb["lat_min"], bb["lat_max"])
        base_lon = rng.uniform(bb["lon_min"], bb["lon_max"])
        dba = f"Synth Eatery {camis[-4:]}"
        for k in range(inspections_per_camis):
            jitter = rng.normal(0, 0.00015, size=2)
            # Some inspections result in closure actions; used as a closure proxy.
            action = rng.choice(
                [
                    "No violations were recorded at the time of this inspection.",
                    "Violations were cited in the following area(s).",
                    "Establishment Closed by DOHMH",
                ],
                p=[0.64, 0.33, 0.03],
            )
            rows.append(
                {
                    "camis": camis,
                    "dba": dba,
                    "boro": rng.choice(["MANHATTAN", "BROOKLYN"]),
                    "zipcode": str(int(rng.integers(10001, 11240))),
                    "cuisine_description": rng.choice(["American", "Chinese", "Pizza", "Cafe"]),
                    "latitude": str(base_lat + jitter[0]),
                    "longitude": str(base_lon + jitter[1]),
                    "score": str(int(np.clip(rng.normal(18, 8), 0, 80))),
                    "grade": rng.choice(["A", "A", "B", "C"], p=[0.7, 0.1, 0.15, 0.05]),
                    "inspection_date": f"202{rng.integers(0, 6)}-{rng.integers(1, 12):02d}-{rng.integers(1, 28):02d}",
                    "action": action,
                }
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f)
    return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    p = write_fallback(root / "data" / "raw" / "inspections_manhattan_brooklyn.json")
    print("Wrote", p)
