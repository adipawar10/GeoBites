"""
Ingest TripAdvisor NYC CSV and map entries to DOHMH establishments by name similarity.

Expected columns in provided Kaggle file:
- Title
- Reveiw Comment (typo in source file)
- Number of review
- Catagory
No timestamp is provided in this dataset.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def _norm_name(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _build_est_name_index(est: pd.DataFrame) -> pd.DataFrame:
    out = est.copy()
    out["name_norm"] = out["dba"].astype(str).map(_norm_name)
    out["name_token_set"] = out["name_norm"].map(lambda x: set(x.split()))
    return out


def _token_jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return float(inter / union) if union else 0.0


def _build_token_index(est_ix: pd.DataFrame) -> dict[str, list[int]]:
    token_map: dict[str, list[int]] = {}
    for idx, toks in est_ix["name_token_set"].items():
        for t in toks:
            token_map.setdefault(t, []).append(idx)
    return token_map


def _match_title_to_camis(
    title: str,
    est_ix: pd.DataFrame,
    token_idx: dict[str, list[int]],
    exact_idx: dict[str, int],
    min_score: float = 0.55,
) -> tuple[str | None, float]:
    t = _norm_name(title)
    t_set = set(t.split())
    if not t_set:
        return None, 0.0

    # Fast exact / near-exact pass
    if t in exact_idx:
        return str(est_ix.loc[exact_idx[t], "camis"]), 1.0

    # Candidate generation from inverted token index (much faster than full scan)
    cand = set()
    for tok in t_set:
        for idx in token_idx.get(tok, []):
            cand.add(idx)
    if not cand:
        return None, 0.0

    # Token-overlap scoring on candidates
    best_idx = None
    best = 0.0
    for idx in cand:
        row = est_ix.loc[idx]
        score = _token_jaccard(t_set, row["name_token_set"])
        if score > best:
            best = score
            best_idx = idx
    if best_idx is None or best < min_score:
        return None, best
    return str(est_ix.loc[best_idx, "camis"]), best


def run_tripadvisor_ingest(
    est_path: Path,
    tripadvisor_csv: Path,
    out_reviews_path: Path,
    out_summary_path: Path,
) -> dict:
    est = pd.read_csv(est_path)
    est = est.dropna(subset=["camis", "dba"]).copy()
    est["camis"] = est["camis"].astype(str)
    est_ix = _build_est_name_index(est)
    token_idx = _build_token_index(est_ix)
    exact_idx = {n: i for i, n in est_ix["name_norm"].items()}

    ta = pd.read_csv(tripadvisor_csv)
    ta = ta.rename(
        columns={
            "Title": "title",
            "Reveiw Comment": "review_text",
            "Number of review": "n_review_site",
            "Catagory": "category",
        }
    )
    for c in ["title", "review_text"]:
        if c not in ta.columns:
            raise KeyError(f"TripAdvisor file missing expected column: {c}")

    rows = []
    matched = 0
    scores = []
    for _, r in ta.iterrows():
        camis, s = _match_title_to_camis(str(r["title"]), est_ix, token_idx, exact_idx)
        if camis is None:
            continue
        matched += 1
        scores.append(s)
        rows.append(
            {
                "camis": camis,
                "review_date": pd.NA,  # not available in this dataset
                "rating": pd.NA,  # not available per-row in this file
                "review_text": r.get("review_text"),
                "source": "tripadvisor_kaggle_nyc_10k",
            }
        )

    out = pd.DataFrame(rows)
    out_reviews_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_reviews_path, index=False)

    summary = {
        "available": True,
        "n_tripadvisor_rows": int(len(ta)),
        "n_matched_rows": int(matched),
        "match_rate": float(matched / len(ta)) if len(ta) else None,
        "mean_name_match_score": float(np.mean(scores)) if scores else None,
        "has_review_date": False,
        "has_review_rating": False,
        "note": "This TripAdvisor file has review text but no per-review date; temporal before/after opening analysis is not identifiable from this file alone.",
    }
    with out_summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    s = run_tripadvisor_ingest(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "raw" / "trip advisor restaurents  10k - trip_rest_neywork_1.csv",
        root / "data" / "processed" / "reviews.csv",
        root / "data" / "processed" / "tripadvisor_match_summary.json",
    )
    print(json.dumps(s, indent=2))

