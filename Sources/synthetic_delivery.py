"""
Synthetic delivery-app listing layer for reproducible demos.

Real DoorDash/UberEats listings require credentials and change frequently. This module
plants virtual brands at hub locations drawn from the empirical spatial distribution
of DOHMH establishments (stratified by borough), then adds tight jitter so DBSCAN
recovers hubs — matching the qualitative phenomenon described in Phase 1/2 docs.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from load_config import load_config


def _meters_to_lat_lon_delta(m_lat: float, m_lon: float, ref_lat: float) -> tuple[float, float]:
    dlat = m_lat / 110_540.0
    dlon = m_lon / (111_320.0 * np.cos(np.radians(ref_lat)))
    return dlat, dlon


def generate_delivery_listings(establishments: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    cfg = load_config()
    syn = cfg["synthetic"]
    n_hubs = int(syn["num_hubs"])
    bmin, bmax = int(syn["brands_per_hub_min"]), int(syn["brands_per_hub_max"])
    jitter = float(syn["hub_jitter_meters"])

    pool = establishments.dropna(subset=["lat", "lon"])
    if len(pool) < n_hubs:
        raise ValueError("Not enough establishments to seed hubs")

    hub_idx = rng.choice(pool.index.to_numpy(), size=n_hubs, replace=False)
    hubs = pool.loc[hub_idx, ["lat", "lon"]].reset_index(drop=True)

    brands = []
    hid = 0
    for _, row in hubs.iterrows():
        base_lat, base_lon = float(row["lat"]), float(row["lon"])
        # Synthetic hub "opening" date for before/after analyses.
        open_year = int(rng.integers(2020, 2026))
        open_month = int(rng.integers(1, 13))
        open_day = int(rng.integers(1, 29))
        hub_open_date = f"{open_year}-{open_month:02d}-{open_day:02d}"
        k = int(rng.integers(bmin, bmax + 1))
        for j in range(k):
            jx, jy = rng.normal(0, jitter), rng.normal(0, jitter)
            dlat, dlon = _meters_to_lat_lon_delta(jx, jy, base_lat)
            brands.append(
                {
                    "virtual_brand_id": f"V_{hid}_{j}",
                    "hub_id": hid,
                    "listing_name": f"Virtual Brand {hid}-{j}",
                    "lat": base_lat + dlat,
                    "lon": base_lon + dlon,
                    "hub_open_date": hub_open_date,
                }
            )
        hid += 1
    return pd.DataFrame(brands)


def run_synthetic(est_path: Path, out_path: Path) -> Path:
    cfg = load_config()
    seed = int(cfg["synthetic"]["seed"])
    rng = np.random.default_rng(seed)
    est = pd.read_csv(est_path)
    df = generate_delivery_listings(est, rng)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    run_synthetic(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "processed" / "delivery_listings_synthetic.csv",
    )
    print("Wrote delivery_listings_synthetic.csv")
