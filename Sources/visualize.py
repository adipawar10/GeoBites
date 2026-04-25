"""
Static figures + optional Folium HTML map.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

try:
    import folium
    from folium.plugins import HeatMap
except ImportError:  # pragma: no cover
    folium = None


def plot_score_vs_distance(scored_path: Path, fig_path: Path) -> Path:
    df = pd.read_csv(scored_path)
    if "min_dist_hub_m" not in df.columns or "score_mean" not in df.columns:
        raise KeyError("Expected establishments_with_exposure.csv from evaluate.py")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(
        data=df.sample(min(8000, len(df)), random_state=0),
        x="min_dist_hub_m",
        y="score_mean",
        hue="exposed",
        alpha=0.35,
        s=12,
    )
    plt.xlabel("Distance to nearest ghost hub (m)")
    plt.ylabel("Mean inspection score (DOHMH)")
    plt.title("Traditional establishments vs. ghost-kitchen hub proximity")
    plt.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=160)
    plt.close()
    return fig_path


def plot_hub_histogram(hubs_path: Path, fig_path: Path) -> Path:
    hubs = pd.read_csv(hubs_path)
    plt.figure(figsize=(7, 4))
    sns.histplot(hubs["n_listings"], bins=20, kde=True, color="#2c7fb8")
    plt.xlabel("Virtual listings per DBSCAN cluster (hub)")
    plt.ylabel("Count")
    plt.title("Distribution of hub sizes (synthetic delivery layer)")
    plt.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=160)
    plt.close()
    return fig_path


def write_folium_map(est_path: Path, hubs_path: Path, html_path: Path) -> Path | None:
    if folium is None:
        return None
    est = pd.read_csv(est_path)
    hubs = pd.read_csv(hubs_path)
    center_lat = float(est["lat"].median())
    center_lon = float(est["lon"].median())
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    heat_data = est[["lat", "lon"]].dropna().values.tolist()
    HeatMap(heat_data, radius=10, blur=14, max_zoom=13).add_to(m)

    for _, r in hubs.iterrows():
        folium.CircleMarker(
            location=[r["centroid_lat"], r["centroid_lon"]],
            radius=max(4, min(18, int(r["n_listings"]) // 2)),
            color="#d62728",
            fill=True,
            fill_opacity=0.55,
            popup=f"Hub cluster {int(r['cluster_id'])}: {int(r['n_listings'])} listings",
        ).add_to(m)

    html_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(html_path))
    return html_path


def run_all(project_root: Path) -> None:
    proc = project_root / "data" / "processed"
    figs = project_root / "figures"
    plot_score_vs_distance(proc / "establishments_with_exposure.csv", figs / "score_vs_distance.png")
    plot_hub_histogram(proc / "ghost_hubs.csv", figs / "hub_size_distribution.png")
    p = write_folium_map(proc / "establishments_with_exposure.csv", proc / "ghost_hubs.csv", figs / "map_hubs.html")
    print("Wrote figures:", figs)
    if p:
        print("Map:", p)


if __name__ == "__main__":
    run_all(Path(__file__).resolve().parents[1])
