# CSC 4740/6740 — GeoBites: Ghost Kitchens vs. Local Restaurant Ecosystems

**Team:** GeoBites  
**Member:** Adi Pawar  

This repository satisfies the course **Sources** requirement: all code lives under `Sources/` with instructions in `Sources/README.md`.

## Quick start

```bash
cd ~/Desktop/CSC4740_GeoBites_GhostKitchen
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python Sources/run_pipeline.py
```

## GitHub-safe repository notes

Large local data files are intentionally excluded from version control:

- `data/raw/Yelp JSON/`
- compressed archives under `data/raw/` (`.tar`, `.zip`)
- generated outputs under `data/processed/` and `figures/`

After cloning on a new machine, place your local datasets back into `data/raw/` and rerun:

```bash
python Sources/run_pipeline.py
```

## Upload to GitHub (first time)

```bash
cd ~/Desktop/CSC4740_GeoBites_GhostKitchen
git init
git add .
git commit -m "Initial commit: CSC4740 GeoBites project"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## Folder layout

| Path | Purpose |
|------|---------|
| `Sources/` | Python modules, `config.yaml`, pipeline entrypoint |
| `data/raw` | Downloaded or fallback inspection JSON |
| `data/processed` | CSV/JSON artifacts |
| `figures/` | Plots + interactive Folium map |
| `reports/` | Phase 1/2 write-ups + final IEEE-style LaTeX |
