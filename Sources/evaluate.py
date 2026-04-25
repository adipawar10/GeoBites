"""
Spatial exposure metrics and statistical associations.

Outcomes use DOHMH inspection scores (higher = more violations / worse).
Exposure uses distance to nearest detected hub and hub counts within a buffer.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression

from load_config import load_config
from spatial_metrics import haversine_m, min_distance_to_hubs


def hub_counts_within_buffer(
    lat: np.ndarray,
    lon: np.ndarray,
    hub_lat: np.ndarray,
    hub_lon: np.ndarray,
    buffer_m: float,
) -> np.ndarray:
    d = haversine_m(lat, lon, hub_lat, hub_lon)
    return (d <= buffer_m).sum(axis=1)


def run_evaluation(est_path: Path, hubs_path: Path, out_dir: Path) -> dict:
    cfg = load_config()
    buf = float(cfg["exposure"]["buffer_meters"])

    est = pd.read_csv(est_path)
    hubs = pd.read_csv(hubs_path)
    if hubs.empty:
        raise ValueError("No hubs found — relax DBSCAN parameters or check listings.")

    hlat = hubs["centroid_lat"].to_numpy()
    hlon = hubs["centroid_lon"].to_numpy()
    lat = est["lat"].to_numpy()
    lon = est["lon"].to_numpy()

    est = est.copy()
    est["min_dist_hub_m"] = min_distance_to_hubs(lat, lon, hlat, hlon)
    est["hub_count_400m"] = hub_counts_within_buffer(lat, lon, hlat, hlon, buf)
    est["exposed"] = (est["min_dist_hub_m"] <= buf).astype(int)

    # Closure proxy (only if 'action_last' exists, e.g., from live SODA or fallback generator)
    if "action_last" in est.columns:
        act = est["action_last"].astype(str).str.lower()
        est["closed_proxy"] = act.str.contains("closed")
    else:
        est["closed_proxy"] = np.nan

    # Drop rows without scores for inference on inspection outcomes
    scored = est.dropna(subset=["score_mean"]).copy()

    exposed = scored[scored["exposed"] == 1]["score_mean"]
    control = scored[scored["exposed"] == 0]["score_mean"]
    tt = stats.ttest_ind(exposed, control, equal_var=False, nan_policy="omit")

    # Effect size (Cohen's d using pooled std; report even when t-test is NS)
    def _cohens_d(a: np.ndarray, b: np.ndarray) -> float | None:
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        if len(a) < 2 or len(b) < 2:
            return None
        sa = a.std(ddof=1)
        sb = b.std(ddof=1)
        sp = np.sqrt(((len(a) - 1) * sa**2 + (len(b) - 1) * sb**2) / (len(a) + len(b) - 2))
        if sp == 0:
            return None
        return float((a.mean() - b.mean()) / sp)

    d = _cohens_d(exposed.to_numpy(), control.to_numpy())

    # Permutation test on difference in means (robust, distribution-free)
    rng = np.random.default_rng(0)
    y = scored["score_mean"].to_numpy(dtype=float)
    g = scored["exposed"].to_numpy(dtype=int)
    obs = float(y[g == 1].mean() - y[g == 0].mean()) if (g == 1).any() and (g == 0).any() else np.nan
    n_perm = 2000
    perm_stats = []
    for _ in range(n_perm):
        gp = rng.permutation(g)
        perm_stats.append(float(y[gp == 1].mean() - y[gp == 0].mean()))
    perm_stats = np.asarray(perm_stats)
    perm_p = float((np.abs(perm_stats) >= abs(obs)).mean()) if obs == obs else None

    # Simple controlled regression: score_mean ~ exposed + boro + cuisine (+ hub_count)
    # Uses one-hot encoding for categorical columns if present.
    reg_result: dict | None = None
    try:
        cols = ["exposed", "hub_count_400m"]
        cat_cols = []
        for c in ["boro", "cuisine", "zip"]:
            if c in scored.columns:
                cat_cols.append(c)
        X = scored[cols + cat_cols].copy()
        X = pd.get_dummies(X, columns=cat_cols, drop_first=True)
        X = X.replace([np.inf, -np.inf], np.nan).dropna(axis=0)
        y_reg = scored.loc[X.index, "score_mean"].to_numpy(dtype=float)
        model = LinearRegression()
        model.fit(X.to_numpy(), y_reg)
        r2 = float(model.score(X.to_numpy(), y_reg))
        # Pull the exposed coefficient if present (it should be the first column)
        coef = dict(zip(X.columns.tolist(), model.coef_.tolist()))
        reg_result = {
            "n": int(len(X)),
            "r2": r2,
            "coef_exposed": float(coef.get("exposed")) if "exposed" in coef else None,
            "coef_hub_count_400m": float(coef.get("hub_count_400m")) if "hub_count_400m" in coef else None,
        }
    except Exception:
        reg_result = None

    rho_d, p_d = stats.spearmanr(scored["min_dist_hub_m"], scored["score_mean"], nan_policy="omit")
    rho_c, p_c = stats.spearmanr(scored["hub_count_400m"], scored["score_mean"], nan_policy="omit")

    # Closure-rate analysis (if closure proxy exists)
    closure_summary: dict | None = None
    if "closed_proxy" in est.columns and est["closed_proxy"].notna().any():
        cl = est.dropna(subset=["closed_proxy"]).copy()
        cl["closed_proxy"] = cl["closed_proxy"].astype(bool)
        # counts
        exp_closed = int(((cl["exposed"] == 1) & (cl["closed_proxy"])).sum())
        exp_open = int(((cl["exposed"] == 1) & (~cl["closed_proxy"])).sum())
        ctl_closed = int(((cl["exposed"] == 0) & (cl["closed_proxy"])).sum())
        ctl_open = int(((cl["exposed"] == 0) & (~cl["closed_proxy"])).sum())
        # chi-square test on 2x2
        table = np.array([[exp_closed, exp_open], [ctl_closed, ctl_open]], dtype=float)
        chi2, chi_p, _, _ = stats.chi2_contingency(table, correction=False)
        # rates
        exp_rate = exp_closed / max(1, (exp_closed + exp_open))
        ctl_rate = ctl_closed / max(1, (ctl_closed + ctl_open))
        closure_summary = {
            "n_with_action": int(len(cl)),
            "exposed_closed": exp_closed,
            "exposed_total": int(exp_closed + exp_open),
            "control_closed": ctl_closed,
            "control_total": int(ctl_closed + ctl_open),
            "closure_rate_exposed": float(exp_rate),
            "closure_rate_control": float(ctl_rate),
            "diff_rates_exposed_minus_control": float(exp_rate - ctl_rate),
            "chi2_statistic": float(chi2),
            "chi2_pvalue": float(chi_p),
        }

    summary = {
        "n_establishments": int(len(est)),
        "n_hubs": int(len(hubs)),
        "buffer_meters": buf,
        "n_exposed": int(scored["exposed"].sum()),
        "n_control": int((scored["exposed"] == 0).sum()),
        "mean_score_exposed": float(exposed.mean()) if len(exposed) else None,
        "mean_score_control": float(control.mean()) if len(control) else None,
        "diff_means_exposed_minus_control": obs if obs == obs else None,
        "cohens_d_exposed_minus_control": d,
        "welch_t_statistic": float(tt.statistic) if tt.statistic == tt.statistic else None,
        "welch_t_pvalue": float(tt.pvalue) if tt.pvalue == tt.pvalue else None,
        "permutation_test_diff_means": {"n_perm": n_perm, "p_two_sided": perm_p},
        "controlled_regression": reg_result,
        "spearman_score_vs_min_dist": {"rho": float(rho_d), "p": float(p_d)},
        "spearman_score_vs_hub_count": {"rho": float(rho_c), "p": float(p_c)},
        "closures": closure_summary,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    est.to_csv(out_dir / "establishments_with_exposure.csv", index=False)
    with (out_dir / "evaluation_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    s = run_evaluation(
        root / "data" / "processed" / "establishments.csv",
        root / "data" / "processed" / "ghost_hubs.csv",
        root / "data" / "processed",
    )
    print(json.dumps(s, indent=2))
