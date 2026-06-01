# Data sources & extension roadmap

## Current dataset (in repo)
- `data/raw/CSE_subcritical_coal_plants_CEA_2022-23.xlsx` — CSE's analysis of
  **CEA's CO₂ database, 2022-23, version 19**, *Table 1: Performance of
  Subcritical units*. 455 subcritical units.
- **Scope caveat:** subcritical units only. Supercritical / ultra-supercritical
  (USC) plants — India's most efficient — are **not** here. The vintage is
  **2022-23**, not 2024.

## What each extension needs that the file lacks

### #1 Variable cost (₹/kWh) — *grade-aware model + ECR override layer done*
The model is now grade-aware (official G1–G17 GCV slabs) and `06_apply_ecr.py`
ingests real per-station ECR. To raise coverage above the seeded example, fill
`data/raw/plant_ecr.csv` (copy from `plant_ecr_template.csv`) from:
- **CERC / State ERC tariff orders** — regulated Energy Charge Rate (ECR).
- **Grid-India / RLDC Merit-Order-Despatch & ECR sheets**, **MERIT portal
  (meritindia.in)** — per-station ₹/kWh.
- **CEA** coal-source / fuel-cost database — to fix the domestic/imported tag.

> All four host domains return HTTP 403 in this remote environment. Download
> locally (or allow-list them) and place the compiled CSV under `data/raw/`.

### #2 Grid location / load proximity (H2) — *coarse proxy done*
Region is inferred from the company name (state utilities only, ~60% coverage).
For a real proximity test you need, per unit:
- Latitude/longitude or substation / **RLDC bus / load-pocket** identifier.
- Transmission-corridor congestion data (which units are "must-run for grid
  security" at load pockets).
Sources: CEA plant directory (location), Grid-India transmission/congestion
reports, state load-despatch must-run lists.

### #3 Flexibility / fast ramp (H1) — *framework only; needs block-level data*
Annual PLF cannot test H1. Supply block-level generation as
`data/raw/sced_blocks.csv` with columns:
`unit_id, timestamp, mw, capacity_mw` (15-min or hourly), then re-run
`05_flexibility_framework.py`.
Sources:
- **Grid-India / POSOCO Security-Constrained Economic Despatch (SCED)** reports
  and block-wise schedules.
- **RLDC** (NRLDC/WRLDC/SRLDC/ERLDC) revision/SCADA archives.
- **CEA** Daily Generation reports for coarser (daily) ramp proxies.

> The remote execution environment blocks outbound access to grid-india.in and
> cea.nic.in (HTTP 403), so these cannot be fetched in-session. Download locally
> and place under `data/raw/`.

### #4 Re-dispatch counterfactual — *done (stylised)*
Uses extension #1's variable cost. To make it production-grade, add transmission
limits, must-run constraints, and part-load heat-rate curves (the model
currently holds VC and EF fixed and ignores network limits).
