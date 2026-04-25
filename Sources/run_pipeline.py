#!/usr/bin/env python3
"""
End-to-end pipeline: acquire → clean → synthetic listings → DBSCAN → evaluate → figures.
Run from project root:  python Sources/run_pipeline.py
Or from Sources:       python run_pipeline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    here = Path(__file__).resolve().parent
    root = here.parent
    sys.path.insert(0, str(here))

    from acquire import acquire_raw
    from clean import run_clean
    from cluster_hubs import run_cluster
    from evaluate import run_evaluation
    from synthetic_delivery import run_synthetic
    from visualize import run_all as viz_all
    from closure_opening_analysis import run_opening_analysis
    from reviews_synthetic import run_synthetic_reviews
    from sentiment_opening_analysis import run_sentiment_opening_analysis
    from yelp_reviews_ingest import run_yelp_ingest
    from tripadvisor_ingest import run_tripadvisor_ingest

    raw = root / "data" / "raw" / "inspections_manhattan_brooklyn.json"
    est_csv = root / "data" / "processed" / "establishments.csv"
    deliv = root / "data" / "processed" / "delivery_listings_synthetic.csv"
    labeled = root / "data" / "processed" / "delivery_listings_labeled.csv"
    hubs_csv = root / "data" / "processed" / "ghost_hubs.csv"
    reviews_csv = root / "data" / "processed" / "reviews.csv"
    yelp_business_json = root / "data" / "raw" / "Yelp JSON" / "yelp_academic_dataset_business.json"
    yelp_review_json = root / "data" / "raw" / "Yelp JSON" / "yelp_academic_dataset_review.json"
    tripadvisor_csv = root / "data" / "raw" / "trip advisor restaurents  10k - trip_rest_neywork_1.csv"

    print("[1/7] Acquiring NYC DOHMH inspections …")
    acquire_raw(raw)
    print("[2/7] Cleaning …")
    run_clean(raw, est_csv)
    print("[3/7] Synthetic delivery listings …")
    run_synthetic(est_csv, deliv)
    print("[4/7] DBSCAN hub detection …")
    run_cluster(deliv, labeled, hubs_csv)
    print("[5/7] Evaluation …")
    summary = run_evaluation(est_csv, hubs_csv, root / "data" / "processed")
    print(json.dumps(summary, indent=2))
    print("[6/7] Visualizations …")
    viz_all(root)
    print("[6.5/7] Closures vs hub openings (proxy) …")
    run_opening_analysis(est_csv, hubs_csv, labeled, root / "data" / "processed")
    print("[6.7/7] Review sentiment change (proxy) …")
    # Prefer real NYC reviews: TripAdvisor CSV first, then Yelp if available; else synthetic.
    if tripadvisor_csv.exists():
        ta_summary = run_tripadvisor_ingest(
            est_csv,
            tripadvisor_csv,
            reviews_csv,
            root / "data" / "processed" / "tripadvisor_match_summary.json",
        )
        if int(ta_summary.get("n_matched_rows", 0)) == 0:
            run_synthetic_reviews(est_csv, reviews_csv)
    # Yelp open dataset fallback (often not NYC-focused depending on release slice).
    elif yelp_business_json.exists() and yelp_review_json.exists():
        yelp_summary = run_yelp_ingest(
            est_csv,
            yelp_business_json,
            yelp_review_json,
            reviews_csv,
            root / "data" / "processed" / "yelp_match_summary.json",
            max_match_dist_m=80.0,
        )
        if not yelp_summary.get("available", False) or int(yelp_summary.get("n_reviews_mapped", 0)) == 0:
            run_synthetic_reviews(est_csv, reviews_csv)
    elif not reviews_csv.exists():
        run_synthetic_reviews(est_csv, reviews_csv)
    run_sentiment_opening_analysis(est_csv, hubs_csv, labeled, reviews_csv, root / "data" / "processed")
    print("[7/7] DBSCAN eps sensitivity …")
    from sensitivity import run_sensitivity

    run_sensitivity(root, eps_grid=np.linspace(40, 160, 25))
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
