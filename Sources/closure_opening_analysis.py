"""
Opening-style analysis (synthetic by default):

Because public datasets rarely provide "ghost kitchen opening dates" directly, this module
implements the *method* using hub opening dates from the listing layer (synthetic field
`hub_open_date`). If you later provide real hub opening dates, the exact same code works.

What it reports:
- For restaurants near a hub (within exposure buffer), whether their latest status indicates
  "closed" after the hub open date (proxy based on action_last and inspection_date_last).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from load_config import load_config
from spatial_metrics import haversine_m


def _to_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=True)


def nearest_hub_open_date_for_restaurants(est: pd.DataFrame, hubs: pd.DataFrame) -> pd.Series:
    """Return hub_open_date (string) for nearest hub per restaurant, if hubs include it."""
    if "hub_open_date" not in hubs.columns:
        return pd.Series([pd.NA] * len(est), index=est.index, dtype="object")

    lat = est["lat"].to_numpy()
    lon = est["lon"].to_numpy()
    hlat = hubs["centroid_lat"].to_numpy()
    hlon = hubs["centroid_lon"].to_numpy()
    d = haversine_m(lat, lon, hlat, hlon)
    nearest_idx = d.argmin(axis=1)
    return hubs.iloc[nearest_idx]["hub_open_date"].reset_index(drop=True)


def run_opening_analysis(
    est_path: Path,
    hubs_path: Path,
    listings_path: Path,
    out_dir: Path,
) -> dict:
    cfg = load_config()
    buf = float(cfg["exposure"]["buffer_meters"])

    est = pd.read_csv(est_path)
    hubs = pd.read_csv(hubs_path)
    listings = pd.read_csv(listings_path)

    # Attach a hub_open_date to each hub by majority vote from listings.
    if "hub_open_date" in listings.columns and not listings.empty:
        open_by_hub = (
            listings.groupby("hub_id", as_index=False)
            .agg(hub_open_date=("hub_open_date", "first"))
            .rename(columns={"hub_id": "cluster_id"})
        )
        hubs = hubs.merge(open_by_hub, how="left", on="cluster_id")

    # Need closure proxy + dates
    if "action_last" not in est.columns or "inspection_date_last" not in est.columns:
        out = {
            "available": False,
            "reason": "Missing action_last or inspection_date_last in establishments.csv (need clean.py output from inspections with action + inspection_date).",
        }
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "opening_closure_summary.json").open("w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        return out

    act = est["action_last"].astype(str).str.lower()
    est = est.copy()
    est["closed_proxy"] = act.str.contains("closed")

    # Determine nearest hub and distance
    lat = est["lat"].to_numpy()
    lon = est["lon"].to_numpy()
    hlat = hubs["centroid_lat"].to_numpy()
    hlon = hubs["centroid_lon"].to_numpy()
    d = haversine_m(lat, lon, hlat, hlon)
    nearest = d.argmin(axis=1)
    est["min_dist_hub_m"] = d.min(axis=1)
    est["exposed"] = (est["min_dist_hub_m"] <= buf).astype(int)

    est["nearest_hub_open_date"] = hubs.iloc[nearest].get("hub_open_date", pd.Series([pd.NA] * len(est))).reset_index(drop=True)
    est["inspection_date_last_dt"] = _to_dt(est["inspection_date_last"])
    est["hub_open_date_dt"] = _to_dt(est["nearest_hub_open_date"])

    # Opening-style flag: closure observed after hub open date (proxy; assumes last inspection captures closure action)
    after_open = (est["inspection_date_last_dt"].notna()) & (est["hub_open_date_dt"].notna()) & (
        est["inspection_date_last_dt"] >= est["hub_open_date_dt"]
    )
    est["closed_after_opening_proxy"] = est["closed_proxy"] & after_open

    exposed = est[est["exposed"] == 1]
    control = est[est["exposed"] == 0]

    summary = {
        "available": True,
        "buffer_meters": buf,
        "n_establishments": int(len(est)),
        "n_hubs": int(len(hubs)),
        "exposed_n": int(len(exposed)),
        "control_n": int(len(control)),
        "exposed_closed_after_opening": int(exposed["closed_after_opening_proxy"].sum()),
        "control_closed_after_opening": int(control["closed_after_opening_proxy"].sum()),
        "exposed_rate_closed_after_opening": float(exposed["closed_after_opening_proxy"].mean()) if len(exposed) else None,
        "control_rate_closed_after_opening": float(control["closed_after_opening_proxy"].mean()) if len(control) else None,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    est.to_csv(out_dir / "establishments_with_opening_flags.csv", index=False)
    with (out_dir / "opening_closure_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    s = run_opening_analysis(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "processed" / "ghost_hubs.csv",
        root / "data" / "processed" / "delivery_listings_labeled.csv",
        root / "data" / "processed",
    )
    print(json.dumps(s, indent=2))

