"""
Clean DOHMH inspection JSON → one row per establishment (CAMIS) with spatial fields.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from load_config import load_config


def inspections_to_establishments(raw_path: Path) -> pd.DataFrame:
    with raw_path.open(encoding="utf-8") as f:
        rows = json.load(f)
    if not rows:
        raise ValueError(f"No rows in {raw_path}")

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(
        columns={
            "latitude": "lat",
            "longitude": "lon",
            "zipcode": "zip",
            "cuisine_description": "cuisine",
        }
    )

    needed = ["camis", "dba", "lat", "lon"]
    for n in needed:
        if n not in df.columns:
            raise KeyError(f"Missing {n}; columns={df.columns.tolist()}")

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["score"] = pd.to_numeric(df.get("score"), errors="coerce")

    df = df.dropna(subset=["camis", "lat", "lon"]).copy()
    df["camis"] = df["camis"].astype(str)

    cfg = load_config()
    bb = cfg["bbox"]
    df = df[
        (df["lat"] >= bb["lat_min"])
        & (df["lat"] <= bb["lat_max"])
        & (df["lon"] >= bb["lon_min"])
        & (df["lon"] <= bb["lon_max"])
    ]

    df["inspection_date"] = df.get("inspection_date", pd.Series("", index=df.index))
    df = df.sort_values(["camis", "inspection_date"])

    agg_map = {
        "dba": ("dba", "last"),
        "lat": ("lat", "last"),
        "lon": ("lon", "last"),
        "score_mean": ("score", "mean"),
        "score_last": ("score", "last"),
        "n_inspections": ("camis", "size"),
        "inspection_date_last": ("inspection_date", "last"),
    }
    if "boro" in df.columns:
        agg_map["boro"] = ("boro", "last")
    if "zip" in df.columns:
        agg_map["zip"] = ("zip", "last")
    if "cuisine" in df.columns:
        agg_map["cuisine"] = ("cuisine", "last")
    if "action" in df.columns:
        agg_map["action_last"] = ("action", "last")

    g = df.groupby("camis", as_index=False).agg(**{k: v for k, v in agg_map.items()})
    return g


def run_clean(raw_path: Path, out_path: Path) -> Path:
    est = inspections_to_establishments(raw_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    est.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    run_clean(
        root / "data" / "raw" / "inspections_manhattan_brooklyn.json",
        root / "data" / "processed" / "establishments.csv",
    )
    print("Wrote establishments.csv")
