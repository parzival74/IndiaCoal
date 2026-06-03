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
- **FY2022-23 headline counterfactual (`06`, real-ECR override at 70.8% units / 79.3% gen):**
  re-dispatch on the blended cost (real ECR where covered, real-CIL flat-freight model for the
  rest) → as-run **+14.7% above cost-optimal**; cost-vs-carbon **+43.5 MT for ~₹34,911 cr**
  (Actual 213,024 / Cost-merit 185,677 / Carbon-merit 220,588 cr; reflects the 2026-06-03 fifth-wave
  Telangana/Jharkhand/Bina additions + the 2026-06-02 WBPDCL with-MFCA correction).
  Wider than the fully-modelled §4 (+5.5%; +21.1 MT/₹15,263 cr) because real ECRs **un-compress
  the cost ladder** (distant ₹2.7-4.6 vs pithead ₹1.4-1.6 vs modelled ₹1.9-2.1). Mixed-basis
  caveat: the uncovered ~25% (mostly private IPPs) is still modelled, so the ordering of that
  tail isn't metered — read it as the best-available FY2022-23 estimate, directionally robust.
- **The freight axis (`11`, now a short note):** backing implied freight out of the ~30 ISGS
  real ECRs (real delivered ₹/t − CIL pithead − levies) gives pithead **~₹360/t** vs distant
  **~₹2,190/t** (IR cross-check ≈1,460 km) — *why* `02`'s flat ₹900/t compresses the real
  ₹1.4→3.9 spread. The earlier all-fleet landed-cost RECONSTRUCTION was **retired** (2026-06-01)
  once `06` covered 69.6% of gen with real ECR; the per-plant freight reconstruction lives in
  git history. `10` kept as a standalone real-data cross-check (no longer feeds `11`).
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
data/raw/            source xlsx; cil_grade_prices_fy2022-23.csv (REAL); plant_ecr.csv (REAL FY2022-23 per-station ECR, 94 rows/322 units/70.8%, 79.3% of gen, consumed by 06); plant_tariff_details.csv (rich 25-col per-substation tariff/technical table, superset of plant_ecr.csv; incl. TSGENCO/MPPGCL cross-check rows, flagged); sources/ (archived regulatory PDFs + per-genco staging CSVs); plant_ecr_cerc_2018basis.csv (REAL, cross-check); datagov_tariff_ecr_2021-23.csv (REAL central ECR, 2021-23, cross-check); plant_ecr_template.csv; (drop sced_blocks.csv here)
data/                cse_subcritical_clean.csv, plant_cost_blended.csv, plant_real_ecr_central.csv (10)  (generated)
analysis/            common.py + numbered pipeline scripts (01–10) + fetch_datagov_ecr.py + run_all.py
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
  `data/raw/plant_ecr.csv` (**94 ECR rows → 322 of 455 units = 70.8% real coverage**, 79.3% of gen;
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
  `data/plant_real_ecr_central.csv` (matched real central ECR; standalone — no longer feeds
  a downstream step).
- (`11_landed_cost.py` — RETIRED 2026-06-01.) The all-fleet landed-cost RECONSTRUCTION was
  removed once `06` reached 69.6%-of-gen real coverage and superseded it. Its durable finding
  — implied freight pithead ~₹360/t vs distant ~₹2,190/t (IR cross-check ≈1,460 km), i.e. why
  `02`'s flat ₹900/t compresses the real ₹1.4→3.9 spread — survives as REPORT §11 (a short
  note) and in git history. No `plant_cost_reconstructed.csv` is produced anymore.

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

**DONE — FY2022-23 per-station ECR harvested to 70.8% coverage (five waves).** The
interactive metered feeds (MERIT TLS-resets; Grid-India SCED / POSOCO 503) stayed down, so
the FY2022-23 per-station energy charge was harvested from **published, date-stamped
documents** instead → `data/raw/plant_ecr.csv`, **94 ECR rows / 322 of 455 units
= 70.8%** (79.3% of generation), each with a precise citation, energy-charge only, FY2022-23 vintage.
- *First wave (20 stns / 78 units):* MahaGenco/MSPGCL monthly Energy Bill (7 MH stns + 2 MH
  IPPs), MahaSLDC MOD stack (4 NTPC central subcritical), RERC review order RERC/2031/22
  (4 RRVUNL), HPGCL FY2022-23 petition (3 HPGCL, flagged filed petition).
- *Second wave (parallel-agent harvest, one genco/agent, operator-verified — 35 stns across
  9 gencos):* GSECL (GERC 30.03.2022 Table 6.1), TANGEDCO (TNERC 7/2022 Table 4-47), PSPCL
  (PSERC 68/2021 Table 7.7), DVC (JSERC 30-09-2024 true-up Table 38), CSPGCL (CSERC
  10/2024(T) Final True-Up, actual coal+oil/net-gen), WBPDCL (WBERC TP-95/20-21 via WBSEDCL
  Appendix A1 MFCA notes; uses the ACTUAL 'Energy Charge with MFCA' col = base + MFCA, set
  2026-06-02 audit — see below), UPRVUNL (UPERC 25-05-2023 Table 5-16, flagged filed APR),
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
- *Fourth wave (2026-06-01, WB + GJ-lignite + Odisha → +9 rows, 62.9%→67.3%):* CESC/WB via WBERC
  TP-96/20-21 (Budge Budge 1.96 = Annexure-4D fuel cost/ex-bus gen; Haldia 2.55 = HEL admitted
  255.0 p/kWh); DPL (Durgapur Projects U7/U8) 2.251 via WBSEDCL MFCA Appendix-A1 — flagged H1-ONLY
  (FY22-23 DPL order not yet issued); Maithon/MPL 2.74 from the Maithon Power Ltd 23rd Annual
  Report 2022-23 (SECONDARY, flagged); GSECL Bhavnagar 2.976 (lignite) via GERC 30.03.2022 Table
  6.1 (same order/basis as the 6 existing GSECL rows); OPGC I.B.Valley 1.611 via OERC Case 104/2021
  (Commission-approved 161.09 p/kWh, pithead MCL G-14); HNPCL Vizag 3.02 via APERC FPPCA true-up;
  the two previously held-out deep-pithead Angul IPPs now CONFIRMED + INCLUDED via BERC NBPDCL/SBPDCL
  Commission-computed table (GMR/Kamalanga 1.20, JITPL/Derang 1.12 — low but real, cheap mine-mouth
  MCL coal; energy-cost col separated from fixed + total 3.39/3.34).
- *Fifth wave (2026-06-03, Telangana + Jharkhand + Bina → +8 rows, 67.3%→70.8%, via WAYBACK MACHINE):*
  the live state-SERC sites are network-blocked (curl 000) + WebFetch times out on big PDFs, but
  web.archive.org is curl-reachable → downloaded the **TSERC TGGenco FY22-23 true-up** + **SCCL Singareni
  true-up** Wayback snapshots (now staged). TGGENCO Table 4-19 'ECR as CLAIMED for FY22-23' (the
  'approved-in-MYT' col is the held-flat base, rejected): Kakatiya-I 3.24, Kakatiya-II 3.19, **K_Gudem
  New 3.293** (gen-wtd KTPS-V 3.34 + KTPS-VI 3.25 — resolves the old K_Gudem→KTPS-VII mapping bug),
  R_Gundem-B 4.37 (TSGENCO, distinct from NTPC R_Gundem Stps 4.085 — collision verified clean), Bhadradri
  3.68 (4x270 SUBcritical, agent had wrongly excluded as supercritical). Flagged `claimed_in_trueup`
  (Commission recovers fuel via FPPCA, no separate approved ECR). SCCL **Singareni 3.332** (Table 4-21
  Commission-APPROVED, not the 3.343 claimed/ARR). **Tenughat 3.215** (JSERC TVNL order 14-12-2023 para
  4.12 verbatim actual; jserc.org reachable, PDF staged). **Bina 3.3** (CRISIL JPVL rationale 25-05-2023
  'variable cost of generation … Rs 3.3 per unit', SECONDARY). Rating-rationale sweep of ~28 other private
  IPPs = 0 clean adds (rationales give total cost / merchant realisation, not energy charge). CG IPPs /
  KPCL / NLC-exp / Bongaigaon still genuinely not-found.
- *Excluded earlier (now SUPERSEDED for Telangana):* the fourth wave kept Telangana TSGENCO out as
  wrong-vintage MYT — the fifth wave's true-up replaces that. Still excluded: ten Chhattisgarh IPPs
  (Tamnar, Baradarha, Raigarh-JPL, Lanco Pathadi, BALCO, etc. — merchant/concessional/FPPPA
  pass-through, no published FY2022-23 station energy charge → genuinely not-found, `cg_ipp_cluster.csv`
  = 0 rows). Agent flagged a mapping fix to revisit: `tsgenco.csv` maps "K_Gudem New"→KTPS-VII
  (supercritical 2.409) but the dataset's 250/250/500 MW units are KTPS V/VI (gen-wtd 2.701) — noted,
  not acted on (TS rows excluded anyway).
- *Three `_norm` collisions* → one gen-weighted merged ECR row each (Korba-West/Ext 1.508,
  Mejia/Ext 3.649, Mettur/Ext 4.996; Talcher I+II 1.987 is a 4th, cap-wtd); per-substation detail
  kept in the new rich table `data/raw/plant_tariff_details.csv` (25-col schema, `docs/plant_tariff_schema.md`).
- *Cross-check only, EXCLUDED from headline (base-ECR-held-flat = wrong vintage, same as the
  CERC-2018 cross-check):* TSGENCO (TSERC MYT 22.03.2022) + MPPGCL (MPERC MYT P-53/2020) —
  in the rich table flagged, NOT in `plant_ecr.csv`. KPCL = honest skip (KERC publishes no
  per-station ECR). Raw artefacts + per-genco staging CSVs under `data/raw/sources/`; harvest
  log in `docs/ecr_scrape_notes.md`. Verified no 06 cross-assignment (Tuticorin JV / Neyveli
  variants correctly stay on the model; forward keying assigns by exact `_norm` key).

**FULL 86-ROW VERIFICATION AUDIT (2026-06-02).** Re-verified every ECR row against its cited primary
source (7 parallel agents by genco-cluster + operator adjudication). Result: **86/86 values correctly
extracted, 0 fabricated.** Two agent flags were false alarms: (a) DVC Mejia 3.649 is correct — it's the
gen-wtd merge by *dataset* generation ((3.715·7495.6+3.577·6867.3)/14362.9=3.649), the agent used the
source order's MU; (b) WBPDCL Bandel 2.171 base was real — the committed `.txt` was corrupt embedded OCR,
fresh tesseract OCR (now committed) confirms `49.78 217.09 266.87` on p.24. **One real finding & fix:**
the 5 WBPDCL rows had used the BASE tariff-order ECR (col A), excluding the MFCA fuel adjustment the same
source reports; switched (user-approved) to the ACTUAL **'Energy Charge with MFCA'** (col B = base+MFCA):
Kolaghat 2.78→3.4445, Bakreswar 1.83→2.284, Santaldih 1.95→2.4414, Bandel 2.17→2.6687, Sagardighi
1.79→2.0306. Headline moved <1% (cost-merit 178,720→180,035; as-run +15.9→+15.7%; gap ₹35,666→35,104 cr).
Audit detail in `docs/ecr_scrape_notes.md`.

**REMAINING (future sessions) — push coverage past 70.8%.** KEY UNBLOCK (2026-06-03): state-SERC sites
are curl-`000` and WebFetch times out on big PDFs, BUT **web.archive.org (Wayback) IS curl-reachable** —
download the archived SERC PDF to disk and pdftotext/OCR it. This cracked Telangana (see fifth wave) and
is the go-to for any other blocked SERC order. Rating-agency sites (icra/care/crisil/indiaratings), BSE,
CEA, cercind, jserc, berc are also reachable. Remaining gaps:
1. WBPDCL deeper unit-splits — DONE: no new coverage (all 5 WB stations covered; Sagardighi I/II immaterial).
2. Replace HPGCL/UPRVUNL/UPERC-IPP filed-APR + DPL H1-only + Maithon/Jhajjar/Bina secondary rows with
   *approved* SERC orders when located (basis upgrade, not coverage). Jhajjar: HERC `O20240305a(1).pdf`
   — try via Wayback (herc.gov.in live is 000).
3. TGGENCO claimed-in-trueup rows (Kakatiya/K_Gudem/R_Gundem-B/Bhadradri) — upgrade to a Commission-
   *approved* ECR if a later TSERC order prints one (current order recovers fuel via FPPCA, claimed only).
4. NLC TPS-II / expansions — no CERC 2019-24 GT *order* published (only 2025 TV letters; data.gov 2021-23 → excluded).
5. CG merchant IPPs (Tamnar/Baradarha/Raigarh-JPL/Lanco/BALCO/SKS/Maruti/ACB), KPCL (Bellary/Raichur),
   Bongaigaon (NTPC, NE beneficiary AERC), captives (Bhilai/NSPCL) — no public FY22-23 station ECR found
   (rating rationales give total-cost/merchant-realisation, not energy charge). Re-source if a CSERC FPPPA /
   beneficiary table / Wayback'd SERC order surfaces. Largely the practical ceiling.
6. Remaining ~133 uncovered units → fall back to the real-CIL model (`02`).

## Working conventions
- **Honesty over polish:** never fabricate data. Label modelled vs real clearly
  (the `vc_source` column / coverage reports do this). Keep scaffolds inert until
  real data backs them.
- Develop on `claude/keen-newton-P0cFA`; push there (PR #1). Don't push elsewhere
  without explicit permission. Don't open new PRs unless asked.
- Outputs are deterministic — regenerating them produces no git diff.
- Do not put model identifiers in committed artifacts.
- The repo started empty; `main` is an empty base branch created for PR #1.
