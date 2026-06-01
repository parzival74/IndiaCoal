# Data sources & extension roadmap

## Status after the 2026-06 Full-access session (read this first)
What a Full-access session actually found (probed repeatedly, alternate hosts/UAs):

| Source | Status | Outcome |
|---|---|---|
| `cercind.gov.in` (CERC orders + CIL price archive) | **200** | used (layers a & c below) |
| `coal.gov.in` / `coalindia.in` | **200** (browser UA) | CIL prices also on cercind CPI page |
| `grid-india.in`, POSOCO `hrd.posoco.in`, `meritindia.in`, `npp.gov.in` | **503 / refused** | FY2022-23 metered per-station ECR **NOT** fetchable |

So `analysis/07_fetch_ecr.py` now fetches the two reachable, real inputs and refuses
to fabricate the rest:
- **(a) CIL FY2022-23 grade-wise pithead notified price** → `data/raw/cil_grade_prices_fy2022-23.csv`,
  consumed by `02` to ground the domestic coal price. Correct vintage: CIL notif. 194
  dated 27-11-2020 was in force across all of FY2022-23 (next hike 31-05-2023).
- **(c) CERC per-station ECR for 14 central stations** → `data/raw/plant_ecr_cerc_2018basis.csv`.
  **Vintage caveat:** CERC computes the ECR on the Oct–Dec 2018 landed coal cost
  (2018-19 basis), so it is a **labelled cross-check** (`08_cerc_crosscheck.py`),
  NOT the FY2022-23 headline.
- **(d) FY2022-23 *metered* per-station ECR** (`data/raw/plant_ecr.csv`, consumed by
  `06`) is still **empty** — its feeds were down. This is the remaining task.

**Vintage rule (unchanged):** the performance data is FY2022-23, so any ECR put into
`plant_ecr.csv` must be FY2022-23. Do NOT paste CERC 2018-basis ECR there.

**To finish when the feeds come back up:**
1. Verify: `curl -s -o /dev/null -w '%{http_code}\n' https://grid-india.in` → 200.
2. Implement the SCED/SLDC/MERIT parser in `07_fetch_ecr.py` against the real
   responses (it refuses to emit fake data — keep it that way).
3. Run `python3 analysis/07_fetch_ecr.py` → writes `data/raw/plant_ecr.csv`.
4. Run `python3 analysis/06_apply_ecr.py` → real-coverage override + counterfactual.
5. Update REPORT.md §7 coverage; commit; push to the working branch.


## Current dataset (in repo)
- `data/raw/CSE_subcritical_coal_plants_CEA_2022-23.xlsx` — CSE's analysis of
  **CEA's CO₂ database, 2022-23, version 19**, *Table 1: Performance of
  Subcritical units*. 455 subcritical units.
- **Scope caveat:** subcritical units only. Supercritical / ultra-supercritical
  (USC) plants — India's most efficient — are **not** here. The vintage is
  **2022-23**, not 2024.

## What each extension needs that the file lacks

### #1 Variable cost (₹/kWh) — *domestic price on REAL CIL FY2022-23 prices; CERC cross-check; metered per-station ECR still pending*
Domestic coal is priced from **real CIL FY2022-23 grade-wise pithead notified prices**
(`data/raw/cil_grade_prices_fy2022-23.csv`, via `02`) + published levies + a flagged
freight term. `06_apply_ecr.py` ingests FY2022-23 **metered** per-station ECR from
`data/raw/plant_ecr.csv` (currently empty — feeds down). The CERC 2018-basis ECR for
14 central stations is a labelled cross-check (`08_cerc_crosscheck.py`).
**Anything in `plant_ecr.csv` must be FY2022-23** to match the performance data.

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

> In the 2026-06 Full-access session, grid-india.in / POSOCO returned **HTTP 503 /
> connection-refused** (not 403), so SCED block data still could not be fetched
> in-session. Download locally when the hosts are back up and place under `data/raw/`.

### #4 Re-dispatch counterfactual — *done (stylised)*
Uses extension #1's variable cost. To make it production-grade, add transmission
limits, must-run constraints, and part-load heat-rate curves (the model
currently holds VC and EF fixed and ignores network limits).
