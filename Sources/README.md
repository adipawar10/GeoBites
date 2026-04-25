# GeoBites — Ghost Kitchen Spatial Mining (Sources)

This folder holds all runnable code for the CSC 4740/6740 project **The “Ghost Kitchen” Takeover – Delivery Apps vs. Local Ecosystems**.

## Required environment

- **Python** 3.10 or newer (tested on 3.12).
- **OS**: macOS, Linux, or Windows.
- Create a virtual environment (recommended on macOS Homebrew Python):

```bash
cd /path/to/CSC4740_GeoBites_GhostKitchen
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Headless servers should set a non-interactive matplotlib backend (the scripts already call `matplotlib.use("Agg")` where needed; you can also `export MPLBACKEND=Agg`).

## How to run (step by step)

1. From the **project root** (parent of `Sources/`):

```bash
source .venv/bin/activate
python Sources/run_pipeline.py
```

2. Outputs:
   - `data/raw/inspections_manhattan_brooklyn.json` — live NYC Open Data **or** offline synthetic fallback if download fails.
   - `data/processed/establishments.csv` — one row per CAMIS.
   - `data/processed/delivery_listings_synthetic.csv` — reproducible “virtual brand” listings for methodology demos.
   - `data/processed/delivery_listings_labeled.csv` — listings with `dbscan_cluster`.
   - `data/processed/ghost_hubs.csv` — hub centroids and listing counts.
   - `data/processed/establishments_with_exposure.csv` — traditional sites + distance / hub-count exposure fields.
   - `data/processed/evaluation_summary.json` — test statistics.
   - `data/processed/sensitivity_eps.csv` — DBSCAN eps sweep.
   - `figures/*.png`, `figures/map_hubs.html` — maps and charts.

3. Optional: run modules individually from project root with `PYTHONPATH=Sources`:

```bash
PYTHONPATH=Sources python Sources/fallback_data.py
PYTHONPATH=Sources python Sources/acquire.py
PYTHONPATH=Sources python Sources/clean.py
# …etc.
```

## Live NYC data

`acquire.py` queries the public Socrata endpoint for dataset `43nn-pn8j` (DOHMH restaurant inspections). If your network blocks `data.cityofnewyork.us`, the pipeline automatically switches to **offline synthetic inspections** with identical schema so graders can still execute everything.

## Ethics / scope

Delivery-platform scrapes and Yelp content are **not** bundled (ToS / credentialing). The **synthetic delivery layer** documents how proprietary listings would plug into the same DBSCAN + exposure machinery described in the written report.
