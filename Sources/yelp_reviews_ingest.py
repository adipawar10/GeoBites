"""
Ingest real Yelp reviews and map them to project restaurants (CAMIS rows) by geospatial matching.

Why this bridge is needed:
- Yelp and DOHMH use different IDs.
- We match each DOHMH establishment to nearest Yelp restaurant business within a distance threshold.

Outputs:
- reviews.csv (camis, review_date, rating, review_text, source)
- yelp_match_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from load_config import load_config
from spatial_metrics import haversine_m


def _iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _load_yelp_businesses_in_bbox(business_json: Path, bbox: dict) -> pd.DataFrame:
    rows = []
    for obj in _iter_jsonl(business_json):
        lat = obj.get("latitude")
        lon = obj.get("longitude")
        if lat is None or lon is None:
            continue
        if not (bbox["lat_min"] <= lat <= bbox["lat_max"] and bbox["lon_min"] <= lon <= bbox["lon_max"]):
            continue
        cats = str(obj.get("categories") or "")
        if "Restaurant" not in cats and "Food" not in cats:
            continue
        rows.append(
            {
                "business_id": obj.get("business_id"),
                "name": obj.get("name"),
                "latitude": float(lat),
                "longitude": float(lon),
                "stars": obj.get("stars"),
                "review_count": obj.get("review_count"),
                "categories": cats,
            }
        )
    return pd.DataFrame(rows)


def _map_camis_to_business(est: pd.DataFrame, biz: pd.DataFrame, max_dist_m: float = 80.0) -> pd.DataFrame:
    if biz.empty or est.empty:
        return pd.DataFrame(columns=["camis", "business_id", "match_dist_m"])
    d = haversine_m(
        est["lat"].to_numpy(dtype=float),
        est["lon"].to_numpy(dtype=float),
        biz["latitude"].to_numpy(dtype=float),
        biz["longitude"].to_numpy(dtype=float),
    )
    nearest_idx = d.argmin(axis=1)
    nearest_dist = d.min(axis=1)
    out = pd.DataFrame(
        {
            "camis": est["camis"].astype(str).to_numpy(),
            "business_id": biz.iloc[nearest_idx]["business_id"].to_numpy(),
            "match_dist_m": nearest_dist,
        }
    )
    out = out[out["match_dist_m"] <= max_dist_m].copy()
    # If multiple CAMIS map to same business_id, keep closest one
    out = out.sort_values("match_dist_m").drop_duplicates(subset=["business_id"], keep="first")
    return out


def run_yelp_ingest(
    est_path: Path,
    yelp_business_json: Path,
    yelp_review_json: Path,
    out_reviews_path: Path,
    out_summary_path: Path,
    max_match_dist_m: float = 80.0,
) -> dict:
    cfg = load_config()
    bbox = cfg["bbox"]

    est = pd.read_csv(est_path)
    est = est.dropna(subset=["camis", "lat", "lon"]).copy()
    est["camis"] = est["camis"].astype(str)

    biz = _load_yelp_businesses_in_bbox(yelp_business_json, bbox)
    mapping = _map_camis_to_business(est, biz, max_dist_m=max_match_dist_m)

    wanted = set(mapping["business_id"].astype(str).tolist())
    if not wanted:
        summary = {
            "available": False,
            "reason": "No Yelp businesses matched within threshold.",
            "n_establishments": int(len(est)),
            "n_yelp_businesses_in_bbox": int(len(biz)),
            "n_matches": 0,
        }
        out_reviews_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["camis", "review_date", "rating", "review_text", "source"]).to_csv(out_reviews_path, index=False)
        with out_summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    map_b2c = dict(zip(mapping["business_id"].astype(str), mapping["camis"].astype(str)))
    rows = []
    for obj in _iter_jsonl(yelp_review_json):
        bid = str(obj.get("business_id"))
        if bid not in wanted:
            continue
        rows.append(
            {
                "camis": map_b2c[bid],
                "review_date": obj.get("date"),
                "rating": obj.get("stars"),
                "review_text": obj.get("text"),
                "source": "yelp_open_dataset",
            }
        )

    reviews = pd.DataFrame(rows)
    out_reviews_path.parent.mkdir(parents=True, exist_ok=True)
    reviews.to_csv(out_reviews_path, index=False)

    summary = {
        "available": True,
        "n_establishments": int(len(est)),
        "n_yelp_businesses_in_bbox": int(len(biz)),
        "n_matches": int(len(mapping)),
        "match_rate_establishments": float(len(mapping) / len(est)) if len(est) else None,
        "mean_match_dist_m": float(mapping["match_dist_m"].mean()) if len(mapping) else None,
        "n_reviews_mapped": int(len(reviews)),
        "max_match_dist_m": float(max_match_dist_m),
    }
    with out_summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    s = run_yelp_ingest(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "raw" / "Yelp JSON" / "yelp_academic_dataset_business.json",
        root / "data" / "raw" / "Yelp JSON" / "yelp_academic_dataset_review.json",
        root / "data" / "processed" / "reviews.csv",
        root / "data" / "processed" / "yelp_match_summary.json",
        max_match_dist_m=80.0,
    )
    print(json.dumps(s, indent=2))

