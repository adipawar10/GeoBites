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

## Course deliverables checklist

- **Phase 1 proposal** → `reports/Phase1_Proposal_GeoBites.pdf` (compile from `.tex` or use the `.md` source).
- **Phase 2 mid-project** → `reports/Phase2_MidProject_GeoBites.md`.
- **Phase 3 report** → `reports/Final_Report_GeoBites.tex` (+ PDF after `pdflatex`).
- **Demo video** → record locally; upload to Google Drive; paste link in the final report’s demo section (template included).
- **iCollege naming** → rename final PDF per instructor rule `Team_<number>.pdf` once you know your team ID.

## Demo video outline (~15–20 min)

1. Show repository layout and `Sources/README.md`.
2. Run `python Sources/run_pipeline.py`; narrate each stage (acquire/clean/synthetic/DBSCAN/eval/sensitivity).
3. Open `figures/map_hubs.html` in a browser (heat layer + hub markers).
4. Discuss `evaluation_summary.json` and limitations (synthetic delivery layer vs. production APIs).
