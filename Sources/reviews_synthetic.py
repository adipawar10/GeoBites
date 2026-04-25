"""
Synthetic review generator (fallback).

Purpose: allow "sentiment change after hub opening" analysis to run even when
review data cannot be fetched (Yelp/Google ToS, credentials, network blocks).

If you have real reviews, you should provide a CSV with columns:
- camis (string)
- review_date (YYYY-MM-DD)
- rating (optional numeric)
- review_text (string)
and skip this generator.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


POS_PHRASES = [
    "great food",
    "friendly staff",
    "fast service",
    "loved it",
    "would come back",
    "excellent",
    "amazing",
    "fresh",
    "tasty",
]
NEG_PHRASES = [
    "terrible service",
    "cold food",
    "overpriced",
    "never again",
    "rude staff",
    "disappointed",
    "bad experience",
    "slow",
]
NEU_PHRASES = [
    "it was okay",
    "average",
    "nothing special",
    "fine",
    "decent",
    "as expected",
]


def generate_reviews(
    establishments: pd.DataFrame,
    rng: np.random.Generator,
    mean_reviews_per_restaurant: float = 4.0,
) -> pd.DataFrame:
    camis = establishments["camis"].astype(str).to_numpy()
    n = len(camis)

    # Poisson number of reviews per restaurant
    k = rng.poisson(lam=mean_reviews_per_restaurant, size=n)

    rows = []
    for i, c in enumerate(camis):
        for _ in range(int(k[i])):
            year = int(rng.integers(2020, 2026))
            month = int(rng.integers(1, 13))
            day = int(rng.integers(1, 29))
            review_date = f"{year}-{month:02d}-{day:02d}"

            # sentiment mixture
            r = rng.random()
            if r < 0.55:
                txt = rng.choice(POS_PHRASES)
                rating = int(rng.choice([4, 5], p=[0.45, 0.55]))
            elif r < 0.80:
                txt = rng.choice(NEU_PHRASES)
                rating = int(rng.choice([3, 4], p=[0.75, 0.25]))
            else:
                txt = rng.choice(NEG_PHRASES)
                rating = int(rng.choice([1, 2, 3], p=[0.45, 0.40, 0.15]))

            rows.append(
                {
                    "camis": c,
                    "review_date": review_date,
                    "rating": rating,
                    "review_text": str(txt),
                    "source": "synthetic",
                }
            )

    return pd.DataFrame(rows)


def run_synthetic_reviews(est_path: Path, out_path: Path, seed: int = 123) -> Path:
    est = pd.read_csv(est_path)
    rng = np.random.default_rng(seed)
    df = generate_reviews(est, rng)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    p = run_synthetic_reviews(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "processed" / "reviews.csv",
    )
    print("Wrote", p)

