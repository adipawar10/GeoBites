"""
Sentiment change analysis around hub opening dates (proxy).

Inputs:
- establishments.csv (needs lat/lon)
- ghost_hubs.csv
- delivery_listings_labeled.csv (contains hub_id and hub_open_date)
- reviews.csv (real or synthetic)

Outputs:
- data/processed/reviews_with_sentiment.csv
- data/processed/sentiment_opening_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from load_config import load_config
from sentiment import add_sentiment
from spatial_metrics import haversine_m


def _to_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce", utc=True)


def _attach_hub_open_dates(hubs: pd.DataFrame, listings: pd.DataFrame) -> pd.DataFrame:
    if "hub_open_date" not in listings.columns or listings.empty:
        hubs = hubs.copy()
        hubs["hub_open_date"] = pd.NA
        return hubs
    open_by_hub = (
        listings.groupby("hub_id", as_index=False)
        .agg(hub_open_date=("hub_open_date", "first"))
        .rename(columns={"hub_id": "cluster_id"})
    )
    return hubs.merge(open_by_hub, how="left", on="cluster_id")


def _nearest_hub_fields(est: pd.DataFrame, hubs: pd.DataFrame, buffer_m: float) -> pd.DataFrame:
    lat = est["lat"].to_numpy()
    lon = est["lon"].to_numpy()
    hlat = hubs["centroid_lat"].to_numpy()
    hlon = hubs["centroid_lon"].to_numpy()
    d = haversine_m(lat, lon, hlat, hlon)
    nearest = d.argmin(axis=1)
    out = est.copy()
    out["min_dist_hub_m"] = d.min(axis=1)
    out["exposed"] = (out["min_dist_hub_m"] <= buffer_m).astype(int)
    out["nearest_cluster_id"] = hubs.iloc[nearest]["cluster_id"].reset_index(drop=True).to_numpy()
    out["nearest_hub_open_date"] = hubs.iloc[nearest]["hub_open_date"].reset_index(drop=True).to_numpy()
    return out


def run_sentiment_opening_analysis(
    est_path: Path,
    hubs_path: Path,
    listings_path: Path,
    reviews_path: Path,
    out_dir: Path,
) -> dict:
    cfg = load_config()
    buf = float(cfg["exposure"]["buffer_meters"])

    est = pd.read_csv(est_path)
    hubs = pd.read_csv(hubs_path)
    listings = pd.read_csv(listings_path)
    reviews = pd.read_csv(reviews_path)

    hubs = _attach_hub_open_dates(hubs, listings)
    est2 = _nearest_hub_fields(est, hubs, buf)

    # Join reviews to establishments -> nearest hub open date
    reviews["camis"] = reviews["camis"].astype(str)
    est2["camis"] = est2["camis"].astype(str)
    r = reviews.merge(est2[["camis", "exposed", "nearest_hub_open_date"]], on="camis", how="left")

    r["review_date_dt"] = _to_dt(r.get("review_date", pd.Series([pd.NA] * len(r))))
    r["hub_open_date_dt"] = _to_dt(r.get("nearest_hub_open_date", pd.Series([pd.NA] * len(r))))
    r = add_sentiment(r, text_col="review_text")

    # Determine pre/post relative to hub opening
    r["is_post_opening"] = (r["review_date_dt"].notna()) & (r["hub_open_date_dt"].notna()) & (r["review_date_dt"] >= r["hub_open_date_dt"])

    # Aggregate: mean sentiment pre vs post, exposed vs control
    def _mean(x: pd.Series) -> float | None:
        x = pd.to_numeric(x, errors="coerce")
        return float(x.mean()) if x.notna().any() else None

    groups = []
    for exposed_val, name in [(1, "exposed"), (0, "control")]:
        sub = r[r["exposed"] == exposed_val]
        pre = sub[sub["is_post_opening"] == False]  # noqa: E712
        post = sub[sub["is_post_opening"] == True]  # noqa: E712
        groups.append(
            {
                "group": name,
                "n_reviews": int(len(sub)),
                "n_pre": int(len(pre)),
                "n_post": int(len(post)),
                "mean_sentiment_pre": _mean(pre["sentiment_score"]),
                "mean_sentiment_post": _mean(post["sentiment_score"]),
                "delta_post_minus_pre": (
                    (_mean(post["sentiment_score"]) - _mean(pre["sentiment_score"]))
                    if _mean(post["sentiment_score"]) is not None and _mean(pre["sentiment_score"]) is not None
                    else None
                ),
                "share_positive": float((sub["sentiment_label"] == "positive").mean()) if len(sub) else None,
                "share_negative": float((sub["sentiment_label"] == "negative").mean()) if len(sub) else None,
            }
        )

    has_temporal_signal = bool(r["review_date_dt"].notna().any() and r["hub_open_date_dt"].notna().any())
    cross_sectional = []
    for exposed_val, name in [(1, "exposed"), (0, "control")]:
        sub = r[r["exposed"] == exposed_val]
        cross_sectional.append(
            {
                "group": name,
                "n_reviews": int(len(sub)),
                "mean_sentiment": _mean(sub["sentiment_score"]),
                "share_positive": float((sub["sentiment_label"] == "positive").mean()) if len(sub) else None,
                "share_negative": float((sub["sentiment_label"] == "negative").mean()) if len(sub) else None,
            }
        )

    summary = {
        "available": True,
        "has_temporal_review_dates": bool(r["review_date_dt"].notna().any()),
        "has_hub_open_dates": bool(r["hub_open_date_dt"].notna().any()),
        "temporal_before_after_identifiable": has_temporal_signal,
        "buffer_meters": buf,
        "n_reviews_total": int(len(r)),
        "n_reviews_with_join": int(r["exposed"].notna().sum()),
        "groups": groups,
        "cross_sectional_groups": cross_sectional,
        "interpretation": "If delta_post_minus_pre < 0, sentiment became more negative after nearby hub opening; if > 0, more positive.",
    }
    if not has_temporal_signal:
        summary["note"] = (
            "Temporal before/after opening effect is not identifiable because review_date is missing or hub_open_date is missing "
            "for most rows. Use cross_sectional_groups for near-vs-far sentiment comparison."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    r.to_csv(out_dir / "reviews_with_sentiment.csv", index=False)
    with (out_dir / "sentiment_opening_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    s = run_sentiment_opening_analysis(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "processed" / "ghost_hubs.csv",
        root / "data" / "processed" / "delivery_listings_labeled.csv",
        root / "data" / "processed" / "reviews.csv",
        root / "data" / "processed",
    )
    print(json.dumps(s, indent=2))

