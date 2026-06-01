# Data sources & extension roadmap

## Resuming with network access (read this first if you're a new session)
Earlier sessions ran under the **Trusted** network policy, so government data
hosts (`cercind.gov.in`, `coal.gov.in`, `cea.nic.in`, `grid-india.in`, MERIT)
returned HTTP 403 and real ECR could not be fetched. The environment is now set
to **Full** access (applies to NEW sessions only). If you are that session:
1. Verify access: `curl -s -o /dev/null -w '%{http_code}\n' https://cercind.gov.in`
   → expect 200, not 403 (also try the other hosts in #1 below).
2. **Vintage rule:** the performance data is FY2022-23, so every ECR you collect
   must be FY2022-23 — do NOT use current-year prices (coal prices swung hugely;
   mixing vintages would invalidate the cost↔PLF comparison).
3. Collect ECR per the ranked sources in #1; complete the parser TODOs in
   `analysis/07_fetch_ecr.py` (it refuses to emit fake data — keep it that way).
4. Run `python3 analysis/07_fetch_ecr.py` → writes `data/raw/plant_ecr.csv`.
5. Run `python3 analysis/06_apply_ecr.py` → real-coverage override + counterfactual.
6. Update REPORT.md coverage; commit; push to `claude/keen-newton-P0cFA` (PR #1).


## Current dataset (in repo)
- `data/raw/CSE_subcritical_coal_plants_CEA_2022-23.xlsx` — CSE's analysis of
  **CEA's CO₂ database, 2022-23, version 19**, *Table 1: Performance of
  Subcritical units*. 455 subcritical units.
- **Scope caveat:** subcritical units only. Supercritical / ultra-supercritical
  (USC) plants — India's most efficient — are **not** here. The vintage is
  **2022-23**, not 2024.

## What each extension needs that the file lacks

### #1 Variable cost (₹/kWh) — *grade-aware model + ECR override layer done*
The model is grade-aware (official G1–G17 GCV slabs) and `06_apply_ecr.py` ingests
real per-station ECR from `data/raw/plant_ecr.csv` (copy `plant_ecr_template.csv`).
**All ECR must be FY2022-23** to match the performance data.

Sources, ranked. (Wayback is deliberately NOT used: MERIT served its numbers
dynamically so archived snapshots don't capture the data, and the dated documents
below are both vintage-correct and more authoritative.)
1. **CERC FY2022-23 tariff orders** (`cercind.gov.in`) — authoritative regulated
   ECR for central / ISGS stations (NTPC, DVC, NLC). Date-stamped, still live;
   per-petition PDFs → map order to station by petition title.
2. **Grid-India FY2022-23 SCED statements / RLDC reports** (`grid-india.in`,
   `posoco.in`, eLibrary `hrd.posoco.in/elibrary`, RLDCs nrldc/wrldc/srldc/erldc/
   nerldc) — per-generator variable cost for all interstate stations; best for the
   large central units (the highest-PLF ones in our data).
3. **State SLDC daily Merit-Order-Despatch stacks** — most granular per-station
   ₹/kWh (SLDCs must publish daily), but ~30 heterogeneous sites; covers state
   gencos. e.g. Odisha SLDC `Merit_Order` page, plus MSLDC / KSLDC / GSLDC.
4. **Coal India 2022-23 grade-wise notified prices** (`coal.gov.in`) × plant SHR
   + freight → universal fallback so every unit gets a period-correct modelled ECR
   even where 1–3 have no entry (also improves 02's domestic price).
5. **MERIT / NPP mirror — last resort.** MERIT (`meritindia.in`) is an INTERACTIVE
   MAP: its data loads via background XHR/JSON, so inspect the network calls for
   the station/variable-cost endpoint rather than scraping HTML — and it is
   flaky/semi-defunct. NPP mirror: `npp.gov.in/dashBoard/gc-map-dashboard-meritchart`.
6. **Cross-checks:** Prayas (Energy Group) MOD analyses, NITI Aayog ICED
   (`iced.niti.gov.in`), CEA operation reports, Ember.

Tag each row's `source`; `06_apply_ecr.py` reports the real-vs-modelled coverage
split and flags every unit via the `vc_source` column.

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
