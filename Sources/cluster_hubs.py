"""
DBSCAN on delivery listing coordinates.

Uses a local tangent-plane projection to meters (stable across platforms) instead of
sklearn's haversine + ball_tree path, which has triggered native aborts on some setups.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from load_config import load_config

EARTH_RADIUS_M = 6_371_000.0


def latlon_to_xy_m(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    lat0, lon0 = float(np.mean(lat)), float(np.mean(lon))
    dlat = np.radians(lat - lat0)
    dlon = np.radians(lon - lon0)
    x = dlon * EARTH_RADIUS_M * np.cos(np.radians(lat0))
    y = dlat * EARTH_RADIUS_M
    return np.column_stack([x, y])


def run_dbscan_listings(listings: pd.DataFrame) -> pd.DataFrame:
    cfg = load_config()
    eps_m = float(cfg["dbscan"]["eps_meters"])
    ms = int(cfg["dbscan"]["min_samples"])
    coords = listings[["lat", "lon"]].to_numpy(dtype=float)
    xy = latlon_to_xy_m(coords[:, 0], coords[:, 1])
    labels = DBSCAN(eps=eps_m, min_samples=ms, metric="euclidean").fit_predict(xy)
    out = listings.copy()
    out["dbscan_cluster"] = labels
    return out


def summarize_hubs(labeled: pd.DataFrame) -> pd.DataFrame:
    sub = labeled[labeled["dbscan_cluster"] >= 0].copy()
    if sub.empty:
        return pd.DataFrame(columns=["cluster_id", "n_listings", "centroid_lat", "centroid_lon"])

    hubs = (
        sub.groupby("dbscan_cluster", as_index=False)
        .agg(n_listings=("lat", "size"), centroid_lat=("lat", "mean"), centroid_lon=("lon", "mean"))
        .rename(columns={"dbscan_cluster": "cluster_id"})
    )
    return hubs


def run_cluster(in_path: Path, listings_out: Path, hubs_out: Path) -> tuple[Path, Path]:
    df = pd.read_csv(in_path)
    labeled = run_dbscan_listings(df)
    hubs = summarize_hubs(labeled)
    listings_out.parent.mkdir(parents=True, exist_ok=True)
    labeled.to_csv(listings_out, index=False)
    hubs.to_csv(hubs_out, index=False)
    return listings_out, hubs_out


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    run_cluster(
        root / "data" / "processed" / "delivery_listings_synthetic.csv",
        root / "data" / "processed" / "delivery_listings_labeled.csv",
        root / "data" / "processed" / "ghost_hubs.csv",
    )
    print("Wrote delivery_listings_labeled.csv and ghost_hubs.csv")
