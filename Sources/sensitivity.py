"""
Sensitivity of hub counts to DBSCAN eps (spatial stability curve).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from cluster_hubs import latlon_to_xy_m
from load_config import load_config


def dbscan_labels_xy(xy: np.ndarray, eps_m: float, min_samples: int) -> np.ndarray:
    return DBSCAN(eps=eps_m, min_samples=min_samples, metric="euclidean").fit_predict(xy)


def run_sensitivity(project_root: Path, eps_grid: np.ndarray | None = None) -> Path:
    listings = pd.read_csv(project_root / "data" / "processed" / "delivery_listings_synthetic.csv")
    coords = listings[["lat", "lon"]].to_numpy(dtype=float)
    xy = latlon_to_xy_m(coords[:, 0], coords[:, 1])

    cfg = load_config(project_root / "Sources" / "config.yaml")
    ms = int(cfg["dbscan"]["min_samples"])

    if eps_grid is None:
        eps_grid = np.linspace(40, 160, 25)

    rows = []
    for eps in eps_grid:
        lab = dbscan_labels_xy(xy, float(eps), ms)
        n_clusters = len(set(lab.tolist()) - {-1})
        n_noise = int((lab == -1).sum())
        rows.append({"eps_meters": float(eps), "n_hubs": n_clusters, "n_noise": n_noise})

    df = pd.DataFrame(rows)
    out_csv = project_root / "data" / "processed" / "sensitivity_eps.csv"
    df.to_csv(out_csv, index=False)

    plt.figure(figsize=(7, 4))
    plt.plot(df["eps_meters"], df["n_hubs"], marker="o")
    plt.xlabel("DBSCAN eps (meters)")
    plt.ylabel("Detected hubs (clusters)")
    plt.title("Sensitivity of hub detection to spatial radius")
    plt.grid(True, alpha=0.3)
    fig_path = project_root / "figures" / "sensitivity_eps.png"
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=160)
    plt.close()
    return out_csv


if __name__ == "__main__":
    run_sensitivity(Path(__file__).resolve().parents[1])
    print("Wrote sensitivity_eps.csv and sensitivity_eps.png")
