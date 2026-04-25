# Phase 1 — Project Proposal (GeoBites)

**Course:** CSC 4740/6740 Data Mining  
**Team:** GeoBites  
**Author:** Adi Pawar  
**Title:** The “Ghost Kitchen” Takeover — Delivery Apps vs. Local Ecosystems (NYC)

---

## 1. Introduction

The U.S. restaurant sector underwent a structural shock during the COVID-19 pandemic as third-party delivery platforms scaled nationally. A parallel organizational form—the **ghost kitchen** (delivery-only production without a traditional storefront)—allows operators to launch multiple **virtual brands** from shared commissary space. In dense markets such as New York City, digital listings, inspection registries, and street-level dining overlap in space even when they diverge in consumer perception.

This project studies the **spatial interplay** between digitally organized delivery supply (virtual brands concentrated at hubs) and **traditional** brick-and-mortar restaurants, using geospatial data mining. The analytic geography focuses on **Manhattan and Brooklyn**, where restaurant counts and platform activity are both high enough to support robust spatial statistics.

---

## 2. Motivation

**Personal and technical goals:** Build fluency in end-to-end spatial pipelines: acquisition, cleaning, clustering, exposure metrics, and communication-grade visualization.

**Research context:** Industry and press accounts document ghost kitchens and virtual brands; academic work often emphasizes platform economics or operational efficiency. Less work operationalizes **neighborhood-scale externalities**—whether concentrated delivery-only capacity correlates with measurable differences for nearby traditional establishments.

**Gap addressed:** We combine (i) authoritative public health inspection geography for “physical” restaurants with (ii) a **delivery-listing layer** that can be populated from APIs/scrapes in a production setting, and in this repository defaults to a **documented synthetic layer** for reproducibility. The gap we target is methodological: a transparent, repeatable **hub → exposure → outcome** framework rather than a proprietary black-box dashboard.

---

## 3. Problem Statement

**Formal goal:** Let \(P=\{p_i\}\) denote geolocated traditional establishments and \(L=\{\ell_j\}\) denote delivery listings (virtual brands). We seek hub set \(H\) such that each \(h\in H\) aggregates many \(\ell_j\) within a small spatial tolerance (DBSCAN in meters under a local projection). For each \(p_i\), define **exposure** \(E_i\) as distance to nearest hub and/or hub count within radius \(r\) (e.g., 400 m). **Outcomes** \(Y_i\) include mean DOHMH inspection score (higher indicates more violations) as a public, longitudinal proxy for operational stress; Yelp rating / closure would be extensions.

**Methods:** NYC SODA API (or offline fallback), pandas cleaning, synthetic delivery generation seeded from empirical coordinates, DBSCAN hub detection, buffer-based exposure, Welch \(t\)-tests and Spearman correlations, sensitivity analysis over DBSCAN \(\varepsilon\).

**Metrics:** Hub count, listings per hub, fraction of establishments exposed, difference in mean scores (exposed vs. control), correlation of scores with distance and hub density, stability curve \(|\hat{H}(\varepsilon)|\).

**Limitations:** Delivery listings in the public repository are **synthetic** unless you plug in your own scraped/API feed under platform ToS. Causal identification is **not** claimed without stronger instruments or panel methods.

---

## 4. Schedule (Spring 2026)

| Week (approx.) | Milestone |
|----------------|-----------|
| Feb 1–6 | Phase 0 sign-up |
| Feb 7–28 | Finalize NYC bbox, SODA queries, cleaning spec, ethics checklist |
| Mar 1 | **Phase 1 due** — proposal PDF |
| Mar 2–20 | Implement DBSCAN + exposure; first maps; draft evaluation |
| Mar 21–27 | **Phase 2 due** — mid-project write-up + screenshots |
| Mar 28–Apr 18 | Sensitivity analysis, polish figures, rehearse demo |
| Apr 19–24 | **Phase 3 due** — IEEE-style report, Sources zip, demo link |

---

## 5. System architecture (preview)

1. **Acquisition:** DOHMH inspections JSON (paginated SODA).  
2. **Cleaning:** Deduplicate to latest row per `CAMIS`, retain lat/lon/score.  
3. **Delivery layer:** Synthetic jittered listings around hub seeds (replaceable with UberEats/DoorDash exports).  
4. **Mining:** DBSCAN on projected meters; summarize centroids.  
5. **Evaluation:** Spatial joins in numpy; classical tests + sensitivity.  
6. **Visualization:** Matplotlib + Folium heatmap with hub markers.

---

## 6. Demo scenario (Phase 3)

Presenter runs `python Sources/run_pipeline.py`, opens `figures/map_hubs.html`, and walks through `evaluation_summary.json` while narrating assumptions and limitations.
