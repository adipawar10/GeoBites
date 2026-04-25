# Phase 2 — Mid-Project Report (GeoBites)

**Course:** CSC 4740/6740 Data Mining  
**Team:** GeoBites  
**Author:** Adi Pawar  
**Title:** The “Ghost Kitchen” Takeover — Delivery Apps vs. Local Ecosystems

---

## 1. Project update

We completed the **data acquisition and integration skeleton** for Manhattan/Brooklyn. Live pulls target NYC Open Data dataset `43nn-pn8j` (DOHMH restaurant inspections). Because delivery APIs require credentials and scrapes are brittle, the repository ships a **reproducible synthetic delivery listing generator** that seeds hubs from the empirical spatial distribution of inspected establishments—this preserves realistic geography while remaining gradable offline.

**Clustering:** DBSCAN on a local tangent-plane projection (meters) recovers 8–14 virtual brands per hub, consistent with the qualitative phenomenon of many brands at one commissary address.

**EDA:** Folium heatmaps overlay traditional establishment density with hub markers; Matplotlib charts summarize hub-size distribution and score–distance scatter.

---

## 2. Results obtained

- **Hub detection:** For the default configuration (`eps = 80` m, `min_samples = 3`), the pipeline detects on the order of **20+ hubs** from the synthetic listing layer, each aggregating many listings (exact counts depend on random seed and live vs. synthetic inspections).  
- **Spatial overlap:** Hub seeds inherit the geographic concentration of the underlying inspection points; visually, exposure is not confined to industrial peripheries in the synthetic instantiation—hubs appear across high-density restaurant neighborhoods in the bbox.

**Statistical snapshot (illustrative offline run):** Welch tests comparing mean inspection scores for establishments within 400 m of any hub vs. farther establishments are typically **not significant** under the synthetic null (scores are not mechanically linked to hub placement). The value is methodological: the pipeline quantifies what would change once real delivery feeds replace the synthetic layer.

---

## 3. Progress vs. Phase 1 milestones

| Planned (Phase 1) | Status |
|---------------------|--------|
| SODA acquisition | Implemented + offline fallback |
| Address cleaning / dedupe | Implemented per CAMIS |
| DBSCAN hubs | Implemented (projected meters) |
| Heatmaps | Implemented (`map_hubs.html`) |
| Yelp survival / ratings | Deferred (API ToS); inspection scores used as public proxy |

---

## 4. Future work (toward Phase 3)

1. Swap synthetic listings for **credentialized** delivery exports; re-run clustering weekly for panel exposure.  
2. Add **DiD / event-study** specs if hub openings can be dated.  
3. Calibrate \(\varepsilon\) using sensitivity curves + manual validation on known commissary addresses.  
4. Package a one-command **Docker** image for reproducibility on graders’ machines.
