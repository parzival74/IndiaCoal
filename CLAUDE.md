# CLAUDE.md — project memory for IndiaCoal

Read this first. It carries everything needed to continue the work without prior
chat context. Active branch: **`claude/keen-newton-P0cFA`** (open as **PR #1**).
The kickoff prompt for the current task is in
[`docs/NEXT_SESSION_PROMPT.md`](docs/NEXT_SESSION_PROMPT.md); the pithead sub-analysis
(does efficiency≈cost at pithead plants?) prompt is in
[`docs/PITHEAD_TEST_PROMPT.md`](docs/PITHEAD_TEST_PROMPT.md) and is now **DONE** —
see REPORT §9 / `analysis/09_pithead_test.py` / `outputs/09_pithead_test.txt`.
A ready-to-run kickoff prompt for fetching the real FY2022-23 metered state/private
per-station ECR (the one remaining gap — needs a network-enabled LOCAL session) is in
[`docs/SCRAPE_ECR_PROMPT.md`](docs/SCRAPE_ECR_PROMPT.md).

## What this project is
Analysis of why thermal **efficiency explains only ~30% of plant load factor
(PLF)** in India's coal fleet, using a CSE/CEA dataset, plus a reproducible
pipeline and several extensions. The headline question: are we failing to follow
merit order, and what would that cost in money and CO₂?

## The data — and two caveats that matter
- Source: `data/raw/CSE_subcritical_coal_plants_CEA_2022-23.xlsx` — CSE's analysis
  of **CEA's CO₂ database, 2022-23 v19**, *Table 1: Performance of Subcritical units*.
- **Caveat 1: SUBCRITICAL units only.** India's supercritical / ultra-supercritical
  (USC) plants — the efficient ones — are NOT in this table. This is why the
  "India 41% vs China 50%" comparison is apples-to-oranges (subcritical vs USC).
- **Caveat 2: vintage is 2022-23, not 2024**, despite the original filename.
- 455 usable units. Fields: name, company, sector (Centre/State/Private), age,
  GCV, fuel (Coal/Lignite), capacity, emission factor, PLF, SHR, efficiency, aux
  consumption, net generation, CO₂.

## Key findings (don't re-derive from scratch; verify via the pipeline)
- Reproduced: Eff↔PLF **R²=22.6%** (all), **r=0.552 / R²=30.5%** (PLF≥20).
- **Efficiency is the wrong axis for merit order**, which dispatches on *variable
  cost* (₹/kWh). Coal price (not in the file) dominates. Imported-coal plants
  (e.g. Mundra, 35% eff) sit idle at ~10% PLF; cheap pithead lignite (29% eff)
  runs at ~83%. The low R² is largely expected, NOT proof merit order is ignored.
- Every measurable plant variable combined explains only **~44%** of PLF.
  **Sector** is the biggest categorical driver: Centre **71%** vs State/Private
  **~58%** PLF. Age has **~0** correlation; bigger plants run *more*.
- Hypotheses: H1 (old/small plants ramp) — undercut (age r≈0) and untestable on
  annual PLF; H2 (load proximity) — region looks coal-proximity driven, needs
  nodal data; H3 (DISCOMs favour own plants) — aggregate runs opposite (state
  plants run least).
- **Re-dispatch counterfactual** (on the real-CIL-grounded cost): as-run dispatch is
  only **~5.5% above cost-optimal** (merit order broadly IS followed). Cost-optimal vs
  carbon-optimal **diverge by ~21 MT CO₂ for ~₹15,300 cr** (implied ~₹7,200/t). So
  "no merit order ⇒ more money AND more CO₂" is wrong — the cheapest coal power
  is also the dirtiest; the two objectives diverge.
- **Pithead sub-analysis (`09`):** at mine-mouth plants (freight≈0) efficiency
  *should* proxy cost. The eff↔PLF "tightening" (R²0.65 vs 0.31) is a **lignite
  artifact** — pithead-*coal*-only R²=0.227 (no better than fleet) and the
  `eff×pithead` OLS interaction is **n.s.** (p=0.31) after sector+size controls. The
  CERC-2018 cost-side test *looked* supportive (eff↔cost R²=0.62 pithead vs ~0.00
  non-pithead, n=7) BUT **`10` shows it does NOT replicate** (see next).
- **Real central ECR cross-check (`10`, data.gov.in):** three Rajya Sabha "Generating
  Station-wise Tariff Statement" datasets (NTPC FY2021-22; NLC/DVC 2021-23) → real ECR
  for **29 ISGS stations / 119 units**. Agrees with CERC-2018 almost perfectly
  (**r=0.99, mean|Δ|=₹0.10**), so it validates the pithead *level* (pithead ~₹1.4-1.6
  vs distant ~₹2.7-3.9). BUT it **tempers `09`**: pithead-coal eff↔ECR is **R²≈0.00**
  here (n=7) vs `09`'s 0.62 — the within-pithead cost-side claim is **not established**
  (thin-sample, sources disagree; pithead coal cost is uniformly low/flat ~₹1.4
  regardless of heat rate). **Robust = the pithead flag predicts cost LEVEL** (location/
  freight, not efficiency). Still ISGS-only + 2021-23, not the FY2022-23 headline.
- **All-fleet landed-cost reconstruction (`11`):** since metered state/private ECR is
  unreachable (and data.gov.in has only ISGS), `11` replaces `02`'s flat ₹900/t freight
  with a **per-plant freight calibrated on the real ISGS ECRs**. Back-out of implied
  freight = real delivered ₹/t − (CIL pithead + levies): pithead **~₹360/t**, distant
  **~₹2,190/t** (IR cross-check ≈1,460 km). Every unit now carries a cost, labelled in
  `vc_source`: real_ISGS_ECR (124u/31s), reconstructed_landed (293u/108s), modelled_anchor
  (38u, lignite/imported). Recon vs real R²=0.72, |Δ|₹0.29 (pithead step |Δ|₹0.26).
  Counterfactual on the all-fleet cost: as-run +6.4% above cost-optimal; cost-vs-carbon
  **+26.5 MT for ~₹16,400 cr**. MODELLED part = the freight *level* (2-step on pithead flag),
  NOT per-plant lead distance. Output: `data/plant_cost_reconstructed.csv`.
- **Domestic coal price is now REAL** (FY2022-23): CIL grade-wise pithead notified
  prices (notif. 194 dated 27-11-2020, in force all of FY2022-23) + published levies
  + flagged flat freight → domestic ≈ ₹2.1/kWh (was a ₹850/Gcal *assumed* anchor).
- **CERC per-station ECR is 2018-19 basis** (working-capital ECR on Oct–Dec 2018 coal
  cost), so it's a **labelled cross-check** (`08`), not the FY2022-23 headline. It
  reveals the real central-station spread ₹1.25→₹3.48/kWh that the flat-freight model
  compresses to ₹1.83–2.08 — i.e. per-plant freight/pithead-distance is the missing axis.
- IPCC does NOT publish fast annual country CO₂; Global Carbon Project / Carbon
  Monitor / IEA do, via high-frequency proxies (nowcasts), revised later.

## Repo layout
```
REPORT.md            the analysis write-up (main deliverable)
README.md            quick start + pipeline table
CLAUDE.md            this file
requirements.txt     pandas, numpy, scipy, openpyxl
data/raw/            source xlsx; cil_grade_prices_fy2022-23.csv (REAL); plant_ecr.csv (REAL FY2022-23 per-station ECR, 77 rows/286 units/62.9%, consumed by 06); plant_tariff_details.csv (rich 25-col per-substation tariff/technical table, superset of plant_ecr.csv; incl. TSGENCO/MPPGCL cross-check rows, flagged); sources/ (archived regulatory PDFs + per-genco staging CSVs); plant_ecr_cerc_2018basis.csv (REAL, cross-check); datagov_tariff_ecr_2021-23.csv (REAL central ECR, 2021-23, cross-check); plant_ecr_template.csv; (drop sced_blocks.csv here)
data/                cse_subcritical_clean.csv, plant_cost_blended.csv, plant_real_ecr_central.csv (10), plant_cost_reconstructed.csv (11)  (generated)
analysis/            common.py + numbered pipeline scripts (01–11) + fetch_datagov_ecr.py + run_all.py
outputs/             *.txt results (committed)
docs/                methodology_variable_cost.md, data_sources.md
.claude/             SessionStart hook (installs deps + runs pipeline on web)
```

## How to run
```bash
pip install -r requirements.txt
python3 analysis/run_all.py      # runs common → 01 → 02 → 03 → 04 → 05 → 06
```
Pipeline scripts:
- `common.py` — clean xlsx → CSV; tags each plant with official Coal India GCV
  grade (G1–G17, real slabs).
- `01_correlations.py` — reproduces stats + multivariate PLF model.
- `02_variable_cost.py` — variable cost ₹/kWh. **Domestic price is REAL**: CIL
  FY2022-23 grade-wise pithead notified price (`data/raw/cil_grade_prices_fy2022-23.csv`)
  + statutory levies + flagged flat freight. Lignite/imported keep modelled anchors.
- `03_regions.py` — grid-region proxy for H2 (~60% coverage, state utilities).
- `04_redispatch.py` — cost-vs-carbon counterfactual on modelled cost.
- `05_flexibility_framework.py` — H1 ramp/cycling metrics framework (needs
  block-level SCED at `data/raw/sced_blocks.csv`; runs on synthetic demo otherwise).
- `06_apply_ecr.py` — FY2022-23 per-station ECR override from
  `data/raw/plant_ecr.csv` (**77 ECR rows → 286 of 455 units = 62.9% real coverage**;
  rest fall back to the real-CIL model). Fuzzy-matches names, reports the
  real-vs-modelled split, re-runs the counterfactual.
- `07_fetch_ecr.py` — **fetches real data** from cercind.gov.in: CIL grade prices
  (→02) + CERC per-station ECR (→08, 2018-basis); probes the FY2022-23 feeds (down).
  Needs network + pdfplumber/pypdfium2. Not in run_all (committed CSVs make it offline).
- `08_cerc_crosscheck.py` — CERC per-station ECR (2018-19 basis) vs the FY2022-23
  model, clearly labelled; 14 central stations; NOT the headline counterfactual.
- `09_pithead_test.py` — SIDE analysis (numbered 09 because 08 was taken): does
  efficiency tighten as a cost/PLF proxy at pithead plants? Curated+lignite pithead
  flag (now in `common.py`, shared with `10`); cost-side test uses REAL ECR only (not
  the SHR-built model). PLF-side tightening is a lignite/size artifact; cost-side is
  thin (n=7) and is NOT confirmed by `10`.
- `fetch_datagov_ecr.py` — fetches real per-station ECR from the data.gov.in tariff
  statements (resource IDs in-file). Needs network + env `DATAGOVIN_API_KEY` (key never
  written to disk/committed). Not in run_all; writes `data/raw/datagov_tariff_ecr_2021-23.csv`.
- `10_datagov_ecr.py` — contemporaneous CENTRAL/ISGS ECR cross-check from data.gov.in
  (2021-22/2021-23). Curated exact-name map (gas/supercritical dropped; DVC paise→Rs);
  coverage, ECR ladder vs model & CERC-2018, the pithead cost-side re-run, illustrative
  re-dispatch. Labelled cross-check, NOT the FY2022-23 headline. Writes
  `data/plant_real_ecr_central.csv` (matched real central ECR, consumed by `11`).
- `11_landed_cost.py` — ALL-FLEET landed-cost reconstruction. Replaces `02`'s flat freight
  with a per-plant freight calibrated on the real ISGS ECRs (pithead ~₹360/t, distant
  ~₹2,190/t; IR-tariff cross-check). Real ECR where available, else reconstructed (domestic)
  or modelled anchor (lignite/imported); all labelled in `vc_source`. Re-runs the
  counterfactual. Writes `data/plant_cost_reconstructed.csv` + `outputs/11_landed_cost.txt`.

## CURRENT TASK — status (2026-06 Full-access session)
Goal: replace modelled coal prices with real published data, FY2022-23 vintage.

**DONE this session** (both layers, as agreed):
- **Domestic coal price → REAL.** Fetched CIL FY2022-23 grade-wise pithead notified
  prices from cercind.gov.in's CPI archive (notif. 194 dated 27-11-2020, in force all
  of FY2022-23) → `data/raw/cil_grade_prices_fy2022-23.csv`; `02` now prices domestic
  coal on it + statutory levies (royalty 14%, GST 5%, cess ₹400/t) + a flagged flat
  freight (₹900/t). Replaces the old assumed ₹850/Gcal anchor.
- **CERC per-station ECR → cross-check (2018-basis).** Parsed 26 CERC 2019-24
  generation-tariff orders → ECR for **14 central stations** → `data/raw/plant_ecr_cerc_2018basis.csv`;
  surfaced by `08_cerc_crosscheck.py`. **Kept OUT of the FY2022-23 headline** because
  CERC's ECR is computed on Oct–Dec 2018 coal cost (2018-19 basis) — vintage rule.
  Explicit curated name aliases (a difflib match wrongly hit "Bhadradri" for Dadri).

**DONE — FY2022-23 per-station ECR harvested to 62.9% coverage (three waves).** The
interactive metered feeds (MERIT TLS-resets; Grid-India SCED / POSOCO 503) stayed down, so
the FY2022-23 per-station energy charge was harvested from **published, date-stamped
regulatory documents** instead → `data/raw/plant_ecr.csv`, **77 ECR rows / 286 of 455 units
= 62.9%**, each with a precise citation, energy-charge only, FY2022-23 vintage.
- *First wave (20 stns / 78 units):* MahaGenco/MSPGCL monthly Energy Bill (7 MH stns + 2 MH
  IPPs), MahaSLDC MOD stack (4 NTPC central subcritical), RERC review order RERC/2031/22
  (4 RRVUNL), HPGCL FY2022-23 petition (3 HPGCL, flagged filed petition).
- *Second wave (parallel-agent harvest, one genco/agent, operator-verified — 35 stns across
  9 gencos):* GSECL (GERC 30.03.2022 Table 6.1), TANGEDCO (TNERC 7/2022 Table 4-47), PSPCL
  (PSERC 68/2021 Table 7.7), DVC (JSERC 30-09-2024 true-up Table 38), CSPGCL (CSERC
  10/2024(T) Final True-Up, actual coal+oil/net-gen), WBPDCL (WBERC TP-95/20-21 via WBSEDCL
  Appendix A1 MFCA notes), UPRVUNL (UPERC 25-05-2023 Table 5-16, flagged filed APR),
  APGENCO (APERC FPPCA O.P.57-68/2024 true-up), NLC (CERC 2019-24 GT orders, lignite).
- *Third wave (2026-06-01, NTPC + private IPPs → +22 rows, 43.3%→62.9%):* NTPC NR/ER via UPERC
  APR FY2022-23 power-purchase table (Rihand 1.754, Singrauli 1.67, Unchahar 4.357, Dadri 4.386,
  Kahalgaon 3.614, Farakka 3.55 — gen-wtd by UP drawal); NTPC SR via APERC FPPCA true-up
  (Ramagundam 4.085, Simhadri 4.451, Vallur 3.478); NTPC-JV Bihar + Barauni via BERC NBPDCL Table
  5.17 (Muzaffarpur 2.92, Nabinagar/BRBCL 2.75, Barauni/BTPS 2.685); Talcher Kaniha MERGED cap-wtd
  Stage I 2.08 (BERC) + Stage II 1.94 (APERC) = 1.987; 8 private IPPs via UPERC (Anapara-C/LANCO
  2.61, KSK/Akaltara 3.38, M.B.Power/Anuppur 2.87, RKM/Uchpinda 2.22, Rosa 3.14×2, TRN/Nawapara
  2.32, Bajaj/Barkhera 4.62); Jhajjar/APCPL 4.09 from ICRA rating (SECONDARY, flagged in `source`).
  Bhilai/NSPCL = honest skip (SAIL captive, no published ECR). Logged in `docs/ecr_scrape_notes.md`.
- *Three `_norm` collisions* → one gen-weighted merged ECR row each (Korba-West/Ext 1.508,
  Mejia/Ext 3.649, Mettur/Ext 4.996; Talcher I+II 1.987 is a 4th, cap-wtd); per-substation detail
  kept in the new rich table `data/raw/plant_tariff_details.csv` (25-col schema, `docs/plant_tariff_schema.md`).
- *Cross-check only, EXCLUDED from headline (base-ECR-held-flat = wrong vintage, same as the
  CERC-2018 cross-check):* TSGENCO (TSERC MYT 22.03.2022) + MPPGCL (MPERC MYT P-53/2020) —
  in the rich table flagged, NOT in `plant_ecr.csv`. KPCL = honest skip (KERC publishes no
  per-station ECR). Raw artefacts + per-genco staging CSVs under `data/raw/sources/`; harvest
  log in `docs/ecr_scrape_notes.md`. Verified no 06 cross-assignment (Tuticorin JV / Neyveli
  variants correctly stay on the model; forward keying assigns by exact `_norm` key).

**REMAINING (future sessions) — push coverage past 62.9%:**
1. WBPDCL deeper unit-splits — order PDFs are **scanned** → need OCR (only the 5 Appendix-A1
   MFCA-recoverable stations captured).
2. Replace HPGCL/UPRVUNL/UPERC-IPP filed-petition (APR) rows with the corresponding HERC/UPERC
   *approved* generation/true-up orders when located (would upgrade basis, not coverage).
3. Replace Jhajjar's ICRA secondary 4.09 with the HERC `O20240305a(1).pdf` station-wise table
   (needs a network session that can reach herc.gov.in).
4. NLC TPS-II / TPS-II Exp / TPS-I Exp — no CERC 2019-24 GT *order* published (only 2025
   true-up TV letters; data.gov.in figures are 2021-23 vintage → excluded per vintage rule).
5. Anomalously-low BERC GMR/Kamalanga 1.20 + JITPL/Derang 1.12 held out — re-source before use.
6. Bongaigaon needs Assam AERC; Bhilai/NSPCL has no published ECR (SAIL captive) — likely permanent skips.
7. Remaining uncovered central/state/private units → fall back to the real-CIL model (`02`/`11`).

## Working conventions
- **Honesty over polish:** never fabricate data. Label modelled vs real clearly
  (the `vc_source` column / coverage reports do this). Keep scaffolds inert until
  real data backs them.
- Develop on `claude/keen-newton-P0cFA`; push there (PR #1). Don't push elsewhere
  without explicit permission. Don't open new PRs unless asked.
- Outputs are deterministic — regenerating them produces no git diff.
- Do not put model identifiers in committed artifacts.
- The repo started empty; `main` is an empty base branch created for PR #1.
