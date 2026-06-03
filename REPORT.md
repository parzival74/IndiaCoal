# Why efficiency explains only ~30% of PLF in India's subcritical coal fleet

**Dataset:** CSE analysis of CEA's CO₂ database, **2022-23, version 19** —
*Table 1: Performance of Subcritical units* (455 units).
**Two scope notes that drive several conclusions:** (1) the table is
**subcritical units only** — India's supercritical / ultra-supercritical (USC)
plants are *not* in it; (2) the vintage is **2022-23**, not 2024.

All numbers below are reproducible via `analysis/run_all.py`; raw outputs are in
`outputs/`.

---

## 0. The reported statistics — confirmed

| Set | Pearson r | R² | n |
|---|---|---|---|
| All units, Efficiency vs PLF | 0.475 | **22.6%** | 455 |
| PLF ≥ 20 only | **0.552** | **30.5%** | 438 |

Both match the figures in the brief exactly (17 units sit below 20% PLF). So the
factual premise is sound. The interpretation needs three corrections.

---

## 1. The core issue: efficiency is the wrong axis for merit order

Merit order dispatches on **lowest variable cost (₹/kWh)**, not thermal
efficiency:

```
variable cost ≈ SHR (kcal/kWh) × coal price (₹/Gcal) + secondary oil + variable O&M
```

Efficiency captures only the `SHR` term. **Coal price is the dominant term and it
is not in the dataset.** Indian thermal fuel cost ranges ~₹1.5/kWh (mine-mouth
lignite, pithead linkage coal) to ~₹4–5/kWh (imported coal). Two units at the
same efficiency can sit at opposite ends of the merit stack. So a *low* Eff↔PLF
correlation is **largely expected** and is **not** strong evidence that India
ignores merit order.

The data shows the mechanism directly (`outputs/02_variable_cost.txt`). Domestic
coal is now priced on the **real Coal India FY2022-23 grade-wise pithead notified
price** + published levies (royalty, GST, GST compensation cess) + a flagged
freight term (see §7); lignite/imported keep modelled anchors.

| Coal source | n | Efficiency | Variable cost (₹/kWh) | PLF | CO₂ (t/MWh) |
|---|---|---|---|---|---|
| Lignite | 34 | **27.3%** (worst) | **1.80** (cheapest) | 56.8% | **1.34** (dirtiest) |
| Domestic coal | 402 | 31.5% | 2.11 | 62.4% | 1.05 |
| Imported coal | 19 | **33.2%** (best) | **4.65** (dearest) | **26.6%** (idle) | **0.94** (cleanest) |

The starkest single case: **Mundra (Adani, imported coal) — 35.4% efficiency,
among the most efficient units in the fleet — runs at just 10–12% PLF**, while
**Neyveli lignite at 28.9% efficiency runs at ~83%**. That isn't merit order
failing; it's merit order *working on cost*. The efficient unit is idle because
imported coal is expensive; the inefficient unit runs flat-out because lignite is
mine-mouth and dirt cheap.

> **Statistical footnote — reverse causality.** Part of the 30% is *PLF → efficiency*,
> not *efficiency → PLF*: running a unit at low PLF means part-load operation off
> its design point, which *worsens* the measured heat rate. So the true causal
> effect of efficiency on dispatch is even weaker than 30%.

---

## 2. So what explains the other ~70%?

A multivariate OLS of PLF on **every usable plant-technical variable**
(`outputs/01_correlations.txt`, PLF ≥ 20, n = 438):

| Model | R² |
|---|---|
| Efficiency only | 30.5% |
| + Age + Capacity + GCV | 32.4% |
| + Sector | 38.1% |
| + Auxiliary consumption | **43.6%** |

**Everything measurable about the plant, combined, still leaves ~56%
unexplained.** That residual is dominated by variables *not in the spreadsheet*:
**coal cost / source, PPA structure & must-run status, RE backing-down, and
transmission / grid-node location.** Two measurable points stand out:

- **Sector is the single biggest jump (+5.7 pp of R²).** Central units run far
  hotter than the rest:

  | Sector | n | Mean PLF | Mean Eff | Mean Age |
  |---|---|---|---|---|
  | **Centre** (NTPC/DVC/NLC) | 130 | **71.1%** | 32.4 | 22.7 |
  | State | 187 | 58.8% | 30.2 | 24.2 |
  | Private | 121 | 58.4% | 31.6 | 13.8 |

  Central plants combine cheap linkage coal, firm long-term PPAs, payment
  security, and ISGS must-run status.

- **Auxiliary consumption** adds another ~5 pp — high-aux (older, inefficient)
  units run less.

---

## 3. The three hypotheses, tested against the data

### H1 — small/old Western plants ramp fast for the solar-drop / evening peak
**Largely contradicted in this data, but ultimately untestable here.**
- **Age has ~zero correlation with PLF (r = −0.015)** — old plants do *not* run
  more. **Bigger** plants run more, not smaller (Capacity r = +0.225; the 400+ MW
  band averages 68% PLF).
- **But annual PLF is a volume metric, not a flexibility metric.** Two-shifting
  and fast ramping show up as *cycling frequency and ramp rate*, which annual PLF
  averages away. So the flexibility intuition could still be true — it is just
  invisible in this dataset. Testing it needs block-level dispatch data
  (extension #3, `05_flexibility_framework.py`).

### H2 — proximity to load centres matters electrically
**Plausible, part of the residual, not testable here — and the coarse regional
proxy points more to *coal* proximity than *load* proximity.** Using a
company-derived grid region for the ~60% of units that are state utilities
(`outputs/03_regions.txt`):

| Region | n | Mean PLF |
|---|---|---|
| **Eastern** (coal belt: DVC/WBPDC/Jharkhand/Odisha) | 54 | **69.8%** |
| Southern | 68 | 58.5% |
| Western (Maharashtra/Gujarat) | 82 | 57.6% |
| Northern | 65 | 55.4% |

Eastern coal-belt states run hottest — a **cheap-pithead-coal (supply-side)**
signal, consistent with cost merit order, rather than the load-proximity story.
True proximity testing needs nodal / load-pocket / RLDC-bus data.

### H3 — DISCOMs prioritise their own plants to delay payments
**The aggregate points the opposite way.** If DISCOMs favoured their own state
gencos, state PLF would be *high* — but **state plants run the *least* (58.8% vs
71.1% central)**. The cash-flow logic is real in specific states/seasons (sunk
fixed-cost PPAs make running "free" at the margin), but it's confounded: central
plants are also genuinely cheaper and must-run, so they top the merit order
anyway. This dataset cannot isolate the effect.

---

## 4. "India maxes at 41% vs China's 50%" — apples to oranges

Three corrections; the gap shrinks substantially.

1. **This table is *subcritical only*.** Subcritical steam is thermodynamically
   capped at ~33–37% gross. The fleet here sits at a median 31.8% (99th pct
   35.5%); the lone 41.7% (Torangallu, imported coal) is an outlier. **India's
   supercritical and USC plants — the efficient ones — simply aren't in this
   table.**
2. **China's "≈50%" is one record unit, not its fleet.** [Pingshan Phase II hits
   49.37% net](https://www.powermag.com/chinas-pingshan-phase-ii-sets-new-bar-as-worlds-most-efficient-coal-power-plant/);
   China's **fleet average is ~38.6%**, USC units 44–46%, USC ~29% of capacity.
   The real story is build-out: China deployed massive USC capacity (2006–2020)
   while India still carries a large subcritical base.
3. **Measurement basis inflates China's number.** China reports **LHV (net)**;
   CSE's efficiency here is **GCV/HHV-based** (it's just 860 ÷ SHR). For India's
   sub-bituminous, high-ash coal, [converting HHV → LHV adds ~3 percentage
   points](https://www.gem.wiki/Estimating_carbon_dioxide_emissions_from_coal_plants).

A fair comparison is roughly **India's best USC (~40–42% net) vs China's best USC
(~47–49%)**, and **India subcritical fleet ~34% LHV vs China fleet ~38.6% LHV** —
a real but much smaller and more explainable gap than "41 vs 50."

---

## 5. The IPCC / CO₂-timing question

The skepticism is half right: **nobody has audited Indian coal-consumption data
within weeks of year-end — but the IPCC isn't who publishes the fast numbers.**

- **The IPCC does not produce annual country emission estimates.** It publishes
  *methodology* (2006 Guidelines + 2019 Refinement: emissions = activity data ×
  emission factor) and assessment reports every ~7 years.
- The **fast annual figures** come from the **Global Carbon Project**,
  **[Carbon Monitor](https://www.nature.com/articles/s41597-020-00708-7)**,
  **IEA**, **EDGAR**, and the **Energy Institute Statistical Review** — explicitly
  **preliminary nowcasts**, not inventories.
- **How they're produced so fast:** not from audited consumption, but from
  **high-frequency proxies** — daily/hourly power-generation data, monthly
  industrial-production indices, mobility, etc. For India, monthly **CEA
  generation**, **Coal India production**, and **customs import** statistics
  arrive with ~1-month lag, and consumption ≈ production + imports − stock change.
  IPCC Tier-1 emission factors (stable to ~2% YoY for coal) are applied,
  uncertainty bands attached, and figures revised later.
- The **official, audited** Indian numbers come via the **UNFCCC inventory**
  (Biennial Update Reports / National Communications) and lag **2–4 years**.

So both are true: the precise number is slow; the *estimate* is fast and
proxy-based.

---

## 6. The key correction: more money ≠ more CO₂

The brief assumed that not following merit order means *both* more cost *and* more
CO₂. In this fleet **those two objectives diverge.** The re-dispatch counterfactual
(`04_redispatch.py`; same total 763 TWh re-stacked; VC & EF held fixed; transmission
/ must-run / ramping ignored — a stylised model to size the trade-off; cost now on
the **real-CIL-grounded** variable cost from §1/§7):

| Scenario | Fuel cost (₹ cr) | CO₂ (MT) |
|---|---|---|
| 1. Actual (as-run) | 157,724 | 777.9 |
| 2. Cost-merit (cheapest VC first) | **149,451** | 767.1 |
| 3. Carbon-merit (cleanest first) | 164,714 | **746.0** |

Two findings:

- **The as-run dispatch is only ~5.5% above cost-optimal.** That is actually
  *evidence India broadly does follow merit order* — the low Eff↔PLF correlation
  was misleading because efficiency ≠ cost.
- **Cost-optimal and carbon-optimal are different objectives.** Going for least
  *cost* instead of least *carbon* costs **+21.1 MT of extra CO₂ to save ~₹15,263
  cr** — an implied abatement cost of roughly **₹7,200/tonne CO₂ (~$87/t)**. The
  cheapest power (pithead lignite, domestic coal) is among the dirtiest; the
  cleanest (imported coal) is the dearest, so strict economic merit order *raises*
  CO₂ relative to a carbon-ranked dispatch.

> The absolute fuel-cost level dropped from earlier drafts because domestic coal is
> now priced on the **real CIL FY2022-23 pithead notified price** (≈₹2.1/kWh) rather
> than an assumed ₹850/Gcal landed anchor (≈₹2.5/kWh). The *direction* (cost and
> carbon optima diverge) is robust; the within-fleet cost spread is still understated
> because per-plant freight is modelled flat (§7, and the CERC cross-check in `08`).

**This misalignment — India's cheapest coal power is also its dirtiest — is the
most policy-relevant finding here, and the textbook case for a carbon price to
re-align the cost and carbon merit orders.**

---

## 7. Populating the variable-cost column with real data (direct answer)

SHR is per-plant and real; the dominant missing term is the per-plant coal price.
We attacked it with real, published data and got **part of the way honestly** —
the part that's reachable and correct-vintage. Three layers, clearly separated:

**(a) Domestic coal price — now REAL and FY2022-23-vintage.** The model's only
assumption block (a guessed ₹850/Gcal landed anchor with invented grade
multipliers) is replaced by the **actual Coal India FY2022-23 grade-wise pithead
notified price** (`data/raw/cil_grade_prices_fy2022-23.csv`). The schedule in force
across all of FY2022-23 is CIL notification 194 dated 27-11-2020 — CIL did not
revise non-coking prices again until 31-May-2023, so a single, period-correct table
applies. On the ex-mine price we add the **published statutory levies** (royalty
14%, GST 5%, GST compensation cess ₹400/t) and a **flagged modelled freight term**
(₹900/t fleet-average). So the base price and levies are real and correctly
vintaged; freight is the one remaining assumption — and it is flat, because
per-plant lead distance isn't in the dataset.

**(b) FY2022-23 *metered/approved per-station* ECR — now at 70.8% real coverage.**
The interactive metered feeds (**MERIT**, **Grid-India SCED**, **POSOCO eLibrary**)
remained unreachable (MERIT TLS-resets; POSOCO/Grid-India 503), but we obtained genuine
FY2022-23, station-level energy charges from **published, date-stamped regulatory
documents** instead, and wrote them to `data/raw/plant_ecr.csv` (consumed by
`06_apply_ecr.py`). **94 ECR rows → 322/455 units = 70.8% real coverage** (79.3% of
generation), each row carrying a precise citation, energy/variable charge only,
FY2022-23 vintage. The first
wave (Maharashtra + central NTPC + Rajasthan + Haryana, 20 stations / 78 units):
- **MahaGenco/MSPGCL monthly Energy Bill to MSEDCL** (mahagenco.in fuel-data) — metered
  per-station Energy Rate (₹/Unit), gen-weighted mean of the two FY-endpoint months
  Apr-2022 & Mar-2023: **7 MahaGenco stations + 2 Maharashtra IPPs** (RattanIndia
  Amravati, JSW Jaigad) off the embedded MahaSLDC DISCOM-wise MOD stack.
- **MahaSLDC DISCOM-wise MOD stack** (CERC Approved Variable Charge, change-in-law = 0)
  — **4 NTPC central subcritical stations** (Vindhyachal, Korba, Sipat-II, Mouda-I),
  capacity-weighted across stages, two-month mean.
- **RERC review order RERC/2031/22, Table 3 "Approved tariff for FY 2022-23"** — approved
  Rate of energy charges (= Energy Cr / Net Gen MU) for **4 RRVUNL stations** (Suratgarh,
  Kota, Chhabra, Kalisindh).
- **HPGCL FY2022-23 tariff petition, Table 38/47** — proposed ECR per HERC MYT Reg 31 for
  **3 HPGCL stations** (Panipat, Yamunanagar/DCRTPP, Rajiv Gandhi/RGTPP), *flagged filed
  petition, not the HERC-approved order*.

The second wave (parallel-agent harvest, one genco per agent, every value operator-verified
against its cited source line; **35 stations across 9 gencos**):
- **GSECL** (GERC Order Case 2025/2021 dtd 30.03.2022, Table 6.1) — Wanakbori, Ukai, Gandhinagar,
  Sikka Extn, Kutch Lignite.
- **TANGEDCO** (TNERC Order 7/2022 dtd 09-09-2022, Table 4-47) — Tuticorin, Mettur (+Ext, merged),
  North Chennai, North Chennai Extension.
- **PSPCL** (PSERC Petn 68/2021 dtd 13-Apr-2022, Table 7.7) — Ropar (GGSSTP), Lehra Mohabbat (GHTP).
- **DVC** (JSERC Order 30-09-2024 true-up, Table 38) — Durgapur, Mejia (+Ext, merged), Chandrapura
  (Jharkhand), Durgapur Steel, Koderma, Raghunathpur, Bokaro-A.
- **CSPGCL** (CSERC Petn 10/2024(T) dtd 01-06-2024, Final True-Up — *actual coal+oil / actual net
  gen*) — Korba-West (+Ext, merged), DSPM, Marwa.
- **WBPDCL** (WBERC TP-95/20-21 dtd 26.07.2022, via WBPDCL MFCA notes in the WBSEDCL FY23-26
  petition Appendix A1) — Kolaghat, Bakreswar, Santaldih, Bandel, Sagardighi. *These use the actual
  fuel-inclusive "Energy Charge with MFCA" (base tariff-order ECR + the MFCA fuel adjustment), set in a
  June-2026 audit for consistency with the actual-cost basis; the MFCA leg is an Apr–Sep FY22-23 average.*
- **UPRVUNL** (UPERC State Discoms Order dtd 25-05-2023, Table 5-16) — Anpara, Obra, Parichha,
  Harduaganj-Ext, *flagged filed APR estimate*.
- **APGENCO** (APERC FPPCA Common Order O.P.57-68/2024 true-up) — Rayalaseema, Dr-NTTPS,
  NTTPS-Stage-IV.
- **NLC** (CERC 2019-24 GT orders, FY22-23 column) — Neyveli New TPP, Barsingsar (both lignite).

Three dataset stations split into two regulatory sub-stations each that collapse to one
fuzzy-match key (Korba-West/Ext, Mejia/Ext, Mettur/Ext) carry a **generation-weighted merged
ECR** in `plant_ecr.csv`, with full per-substation detail preserved in the new rich table
`data/raw/plant_tariff_details.csv` (25-col schema, `docs/plant_tariff_schema.md`). Two gencos
were harvested but kept **OUT of the headline as a cross-check** because their order sets a base
ECR pegged to ≈2019 coal price and holds it flat across the control period (a vintage violation,
same treatment as the CERC-2018 cross-check in (c)): **TSGENCO** (TSERC MYT 22.03.2022, base ECR
constant FY2019-20→FY2023-24) and **MPPGCL** (MPERC MYT P-53/2020, both true-ups state "no truing
up of Energy Charges"). **KPCL** was an honest skip — KERC publishes no per-station ECR. The
`06` reports the real-vs-modelled split and flags every unit via `vc_source`. Raw artefacts and
per-genco staging CSVs are archived under `data/raw/sources/`; the harvest log (found / not-found /
vintage decisions) is in [`docs/ecr_scrape_notes.md`](docs/ecr_scrape_notes.md).

The third wave (NTPC central beneficiary-table harvest + the private-IPP tail, +22 ECR rows →
**286/455 units = 62.9%**) closed most of the remaining NTPC subcritical fleet plus a block of
private IPPs that the dataset carries as "subcritical" 600 MW units:
- **NTPC NR/ER central stations via UPERC** (State Discoms Order 25-05-2023, FY2022-23 power-purchase
  table, *filed-APR estimate*) — Rihand, Singrauli, Unchahar, Dadri (NCTPP), Kahalgaon, Farakka. NTPC
  ISGS ECR is ~uniform across all beneficiary states (billed pro-rata), so a single state's drawal
  table is a valid station-ECR source.
- **NTPC SR central stations via APERC** (FPPCA Common Order O.P.57-68/2024 true-up, "Variable Cost
  Actual") — Ramagundam, Simhadri, Vallur (NTECL JV). **Talcher-Kaniha** appears in both the SR (Stage
  I) and Bihar (Stage II) tables → carried as a **capacity-weighted merged ECR ₹1.987** for the full
  3000 MW station.
- **NTPC-JV / Bihar stations via BERC** (NBPDCL/SBPDCL Tariff Order FY2023-24, Case 16/17 of 2022,
  23-03-2023, Commission-computed FY2022-23) — Muzaffarpur (KBUNL), Nabinagar (BRBCL), and **Barauni
  (BTPS, BSPGCL)** ₹2.685 covering both dataset Barauni entries (Stage I 105 MW + Stage II 2×250).
- **Eight private IPPs via UPERC** (same FY2022-23 power-purchase table, energy/variable charge column,
  each verified `rate × MU/10 ≈ var-Cr`) — Anpara-C (Lanco), KSK Mahanadi (Akaltara/Nariyara), M.B.
  Power (Anuppur), RKM Powergen (Uchpinda), Rosa (Reliance, station-wide rate applied to both phase
  rows), TRN Energy (Nawapara), Bajaj Barkhera.
- **Jhajjar / Indira Gandhi STPP** ₹4.09 from an **ICRA rating rationale** (19-Mar-2024, "the
  variable/energy charge stood at Rs. 4.09 per unit for FY2023") — *flagged `secondary_source`*: real,
  correct vintage, energy-only, but a credit-rating document rather than a regulatory order. Bhilai
  (NSPCL/SAIL captive) was an honest skip.

The fourth wave (West Bengal CESC + Gujarat lignite + Odisha, +9 ECR rows → **306/455 units = 67.3%**)
added three regional clusters:
- **CESC / West Bengal** (WBERC Order Case TP-96/20-21, CESC generation tariff) — **Budge Budge** ₹1.96
  (Annexure-4D fuel cost 96 753.91 Lakh / 4932.43 MU) and **Haldia** ₹2.55 (HEL admitted energy charge
  255.0 p/kWh). **D.P.L.** (Durgapur Projects U7/U8) ₹2.251 from the **WBSEDCL MFCA** Appendix-A1 — *flagged
  H1-only* (FY22-23 DPL order not yet issued → 2021-22 base + realized MFCA). **Maithon (MPL)** ₹2.74 from the
  **Maithon Power Ltd 23rd Annual Report 2022-23** ("average ECR of 2.74 Rs/Kwh") — *flagged `secondary_source`*.
- **GSECL Bhavnagar** ₹2.976 (lignite) — GERC Order 30.03.2022 Table 6.1, the **same order/table/basis** as the
  six existing GSECL headline rows.
- **Odisha + Vizag** — **OPGC I.B.Valley** ₹1.611 (OERC Order Case 104/2021, Commission-approved 161.09 p/kWh,
  pithead MCL G-14 coal), **HNPCL Vizag** ₹3.02 (APERC FPPCA true-up, same source/method as the NTPC-SR rows),
  and the two previously held-out deep-pithead Angul IPPs now **confirmed and included** from the BERC
  NBPDCL/SBPDCL Commission-computed table: **GMR Kamalanga** ₹1.20 and **JITPL Derang** ₹1.12 (low but real —
  cheap mine-mouth MCL coal; the energy-cost column is separated from fixed + total tariff 3.39/3.34).

Two clusters were worked but yielded no headline rows, on the honesty rule: **Telangana** (TSGENCO/TSERC MYT
22.03.2022 — base ECR held flat, a vintage violation → cross-check only, excluded) and **ten Chhattisgarh IPPs**
(Tamnar, Baradarha, Raigarh-JPL, Lanco Pathadi, BALCO, etc. — merchant/concessional/FPPPA pass-through with no
published FY2022-23 station energy charge → genuinely not-found).

The fifth wave (Telangana + Jharkhand + one MP IPP, +8 ECR rows → **322/455 units = 70.8%**) used the
**Wayback Machine** to reach state-SERC PDFs that are otherwise network-blocked, plus a credit-rating
rationale:
- **Telangana TGGENCO** (TSERC true-up for FY2022-23, Table 4-19) — the order the fourth wave flagged as
  the upgrade path. It prints two columns: "approved in MYT 22.03.2022" (the held-flat base, *rejected*)
  and **"claimed in true-up"** (the FY2022-23 actuals). Using the actuals: **Kakatiya-I** ₹3.24,
  **Kakatiya-II** ₹3.19, **K_Gudem New** ₹3.293 (gen-wtd KTPS-V ₹3.34 + KTPS-VI ₹3.25), **Ramagundam-B**
  ₹4.37, **Bhadradri** ₹3.68 (4×270 subcritical). *Flagged `claimed_in_trueup`*: the Commission recovers
  fuel-cost variance via monthly FPPCA, so it prints no separate **approved** FY22-23 ECR — these are the
  petitioner's actuals admitted into the order (a notch below "approved", like the filed-APR rows).
- **SCCL Singareni** ₹3.332 — TSERC SCCL true-up, Table 4-21 *Commission-**approved*** FY22-23 ECR (the
  MYT base 2.345 and the claimed 3.343 both shown; approved 3.332 used). Captive 2×600.
- **TVNL Tenughat** ₹3.215 — JSERC TVNL order (14-12-2023) para 4.12 verbatim *"Actual Energy Charge as
  raised to JBVNL … Rs. 3.215/kWh for FY 2022-23"* (the held-flat MYT base 2.687 rejected).
- **Bina (JPVL)** ₹3.3 — CRISIL rating rationale (25-May-2023) *"the variable cost of generation from the
  plant is Rs 3.3 per unit"* — *flagged `secondary_source`*, like Jhajjar/Maithon.

Still open: WBPDCL deeper unit-splits (no new coverage — all 5 WB stations already covered), the
HERC-approved HPGCL order, a standalone approved UPRVUNL order, and approved-order replacements for the
filed-APR / secondary rows. The remaining ~133 units (largely private/merchant IPPs with no public
per-station ECR, plus captives and KPCL) fall back to the real-CIL model in (a) — this is close to the
ceiling of what public, correct-vintage, per-station data supports.

**The FY2022-23 headline counterfactual (on the real-ECR cost).** Re-running the cost-vs-carbon
re-dispatch on the §7(b) blended cost — real ECR for the 322 covered units (**79.3% of generation**),
real-CIL flat-freight model for the rest (`06_apply_ecr.py`, same total energy):

| Scenario | Fuel cost (₹ cr) | CO₂ (MT) |
|---|---|---|
| Actual (as-run) | 213,024 | 777.9 |
| Cost-merit (cheapest VC first) | **185,677** | 789.5 |
| Carbon-merit (cleanest first) | 220,588 | **746.0** |

As-run is **+14.7% above cost-optimal**, and cost- vs carbon-optimal diverge by **+43.5 MT CO₂ for
~₹34,911 cr**. Both gaps are *wider* than the fully-modelled §4 figures (+5.5%; +21.1 MT / ₹15,263 cr)
for one reason: real ECRs **un-compress the cost ladder** the flat-freight model had flattened (§11) —
distant plants are genuinely dearer (₹2.7–4.6) and pithead genuinely cheaper (₹1.4–1.6) than the
modelled ₹1.9–2.1 band, so both the fleet-average cost level and the spread between as-run and optimal
grow. **Caveat — mixed cost basis:** the merit ranking blends real ECR (79% of gen) with the
flat-freight model (21%, mostly private IPPs); within the real ECR, most are approved/true-up actuals
but a minority are flagged filed-APR, claimed-in-true-up (Telangana), or secondary (rating rationale).
So the uncovered tail's *ordering* is still modelled and a few covered rows are estimates; the gap should
be read as the best available FY2022-23 estimate, directionally robust, not a fully-metered number. The qualitative conclusions hold and sharpen: merit order is broadly followed, and minimum-cost
≠ minimum-carbon (the cheapest coal power is the dirtiest).

**Stability across the coverage expansion (a robustness check).** Across three successive waves —
62.9% (286 units / 69.6% of gen) → 67.3% (306 / 74.9%) → **70.8% (322 / 79.3%)** — the *conclusion*
never moved: the cost-vs-carbon gap held at **+43.5 to +43.7 MT CO₂ for ~₹35,000 cr**, and as-run excess
drifted only +16.1% → +15.7% → **+14.7%** even as cost-optimal rose ₹178,186 → ₹185,677 cr (the level
rises because real ECRs un-compress the ladder; the *gap* is what's stable). Each wave added a *mix* of
cheap pithead (Kamalanga ₹1.20, Derang ₹1.12) and dearer distant/old units (Telangana ₹3.2–4.4,
Vizag ₹3.02), so the merit re-ranking largely nets out. (The level also folds in a June-2026 audit
correction switching the 5 WBPDCL plants from base to actual *with-MFCA* ECR, +~₹1,300 cr.) That the
gap is no longer coverage-sensitive across a 17-point swing in generation coverage is strong evidence
the remaining ~21% tail won't overturn it. (One number is *not* a convergence signal: carbon-optimal
CO₂, 746.0 MT, is the structural minimum — units ordered by emission factor, independent of cost — so it
is fixed at any ECR coverage by construction; the genuine test is the cost side, which is what stabilised.)

**(c) CERC tariff-order ECR — real per-station, but wrong vintage → cross-check
only.** CERC orders *are* reachable, and we extracted the determined ECR for **14
central stations** (NTPC/DVC/NLC) from the 2019-24 generation-tariff orders. But
CERC computes that ECR on the **Oct–Dec 2018 landed coal cost** (a 2018-19 basis;
the energy charge itself is monthly actual pass-through, "subject to truing-up").
Mixing it into the FY2022-23 headline would violate the vintage rule, so it lives
in `data/raw/plant_ecr_cerc_2018basis.csv` and feeds only the **`08_cerc_crosscheck.py`**
comparison — never the headline. (Station names are mapped with an explicit curated
alias list, after a difflib fuzzy-match wrongly snapped "National Capital TPS
(Dadri)" onto the unrelated "Bhadradri" plant.)

**What the cross-check reveals (the key point).** The real CERC ECRs span
**₹1.25/kWh (pithead Sipat/Korba/Singrauli) to ₹3.48/kWh (distant Dadri/Indira
Gandhi)** across these central stations. The model — with its single flat freight
term — compresses that to a narrow **₹1.83–2.08/kWh** band: it *overstates* the
cheap pithead stations and *understates* the distant ones. **Per-plant rail freight
/ pithead-distance is the missing axis that actually drives the within-domestic
merit order**, and only real metered ECR (layer b) can supply it. Consistent with
this, a flat-ish price still tracks PLF (r ≈ −0.43, R² ≈ 18%) somewhat *worse* than
efficiency (R² ≈ 31%): ~88% of units share the compressed domestic band, so the
modelled cost there is largely a rescaling of SHR. (The earlier hand-seeded
"Talcher ₹1.48/kWh" was an approximate placeholder; the real CERC determination
figure for Talcher Stage-II is **₹1.85/kWh on the 2018-19 basis** vs ₹1.98 modelled
— pithead, and the model can't see why it's cheap.) Full detail in
[`docs/methodology_variable_cost.md`](docs/methodology_variable_cost.md).

> **Network status (2026-06, Full access):** cercind.gov.in, coal.gov.in,
> mahagenco.in, cer.iitk.ac.in (IIT-Kanpur ERC Hub) and hpgcl.org.in are reachable.
> meritindia.in still **TLS-resets** and grid-india.in / POSOCO eLibrary return
> **HTTP 503**, so the live *interactive* metered feeds are unavailable — but the
> FY2022-23 per-station energy charge was instead harvested from published, date-stamped
> regulatory documents (MahaGenco fuel-data, MahaSLDC MOD stack, SERC/CERC tariff &
> true-up orders, NTPC beneficiary-DISCOM power-purchase tables, and the private-IPP tail) →
> **94 ECR rows / 322 units (70.8%, 79.3% of generation)** now in `data/raw/plant_ecr.csv`.
> `analysis/07_fetch_ecr.py` re-fetches the CIL prices and CERC orders from source.

---

## 8. Extensions delivered & their data limits

| # | Extension | Status | Blocking data (not in file) |
|---|---|---|---|
| 1 | Variable cost (₹/kWh) | Domestic price on **real CIL FY2022-23** notified prices + levies; FY2022-23 per-station override layer (`06`) at **70.8% real coverage (94 ECR rows / 322 units, 79.3% of gen)** from regulatory docs, NTPC beneficiary tables, state true-ups (incl. Telangana via Wayback) + private IPPs; **CERC 2018-basis cross-check** (`08`) | FY2022-23 *metered* per-station ECR for the remaining ~133 private/captive units (no public per-station ECR) |
| 2 | Grid-region / load proximity | Coarse proxy (~60% coverage) | Lat/long, RLDC bus, load-pocket, congestion |
| 3 | Flexibility / ramp (H1) | Framework + synthetic demo | Block-level SCED generation |
| 4 | Cost-vs-carbon re-dispatch | Done (stylised), on real-CIL cost | Transmission/must-run limits for realism |

See [`docs/data_sources.md`](docs/data_sources.md) for exactly where to obtain the
missing inputs. **Across sessions we harvested FY2022-23 per-station ECR for 94 rows
(322/455 units = 70.8%, 79.3% of generation) from published documents — state gencos
(MahaGenco, RRVUNL, HPGCL, GSECL, TANGEDCO, PSPCL, DVC, CSPGCL, WBPDCL, UPRVUNL, APGENCO, NLC,
CESC, OPGC, TGGENCO, SCCL, TVNL), the NTPC central fleet via beneficiary-DISCOM power-purchase
tables (UPERC/APERC/BERC + MahaSLDC), and the private-IPP tail (UPERC + BERC, plus Jhajjar-ICRA,
Maithon-AR and Bina-CRISIL secondary rows). The **Telangana TGGENCO/SCCL** true-ups were reached
via the **Wayback Machine** (the live state-SERC sites and meritindia.in / grid-india.in / POSOCO
were unreachable in-session)**, so the interactive metered feeds and live SCED block data still
could not be fetched.

## 9. Side analysis: is efficiency a tighter proxy at pithead plants?

If §1 is right — efficiency is the wrong axis because *variable cost* (dominated by
delivered coal price, ~half of which is freight) drives dispatch — then at a **pithead
(mine-mouth) plant freight ≈ 0**, so variable cost collapses toward a near-pure function
of heat rate, and efficiency *should* become a good proxy for cost. We tested this
(`analysis/09_pithead_test.py` → `outputs/09_pithead_test.txt`).

**Flagging pithead (a transparent proxy — there is no distance-to-mine field):** lignite
(mine-mouth by construction) + a curated coal-belt list (Singrauli/Korba/Talcher/Ramagundam
clusters), each with its coalfield basis; matched by exact name. The flag is **independently
validated by the real CERC ECR ladder**: the curated pithead stations average **₹1.64/kWh**
vs **₹2.93/kWh** for the non-pithead central stations — the cheapest plants are exactly the
ones we flagged.

| Test | Full fleet | Pithead | Non-pithead | Read |
|---|---|---|---|---|
| **Eff ↔ cost** (real CERC ECR; the true test) | r=−0.31, R²=0.10 | **r=−0.78, R²=0.62** | r=+0.03, R²≈0.00 | **Supports H.** Efficiency explains ~62% of *real cost* at pithead, ~0% away from it (freight dominates), with the expected negative sign. |
| **Eff ↔ PLF** (PLF≥20) | R²=0.305 | R²=0.650 | R²=0.251 | Apparent tightening, but a **lignite artifact** — see below. |

**Two honest caveats that change the conclusion:**
- The cost-side test (the *real* test) rests on **14 CERC stations on a 2018-19 basis**
  (n=7 per group). It is **directional, not settled** — it becomes a clean result only when
  FY2022-23 per-station ECR coverage broadens.
- The eff↔PLF "tightening" is **mostly lignite + sector/size, not the freight mechanism.**
  Splitting the pithead group: *lignite-only* R²=0.562 but *pithead-coal-only* R²=0.227 —
  **no tighter than the fleet's 0.305.** Cheap mine-mouth lignite runs hard *despite* low
  efficiency, which is itself the cost-over-efficiency point. In an OLS controlling for
  sector and capacity, the `efficiency × pithead` interaction is **not significant**
  (coef +0.44, p=0.31): the PLF tightening does not survive the confounder. PLF also carries
  must-run / demand / transmission noise on top of cost, so we never expected it to be clean.

**Bottom line:** on the data we had at this point, the mechanism showed up on **cost**
(efficiency looked like a strong cost proxy at pithead, a non-proxy away from it) but
*not* on PLF, where lignite and sector/size confound it. **§10 revisits the cost-side
result with a second, contemporaneous real source and finds it does not replicate** —
read the two together.

## 10. Real per-station ECR coverage: the data.gov.in cross-check

We then found the most contemporaneous real per-station ECR reachable: three Rajya Sabha
*"Generating Station-wise Tariff Statement"* datasets on data.gov.in (NTPC FY2021-22;
NLC/DVC 2021-23), giving structured Energy Charge Rate (₹/kWh) for **central/ISGS**
stations. Ingested via `analysis/fetch_datagov_ecr.py` → `data/raw/datagov_tariff_ecr_2021-23.csv`;
analysed in `analysis/10_datagov_ecr.py` → `outputs/10_datagov_ecr.txt`.

**Coverage & validation.** A curated (exact-name) map lands **29 stations / 119 units
(26% of units, 31% of capacity)** — roughly double the 14-station CERC cross-check, and
contemporaneous. The two independent real sources agree almost perfectly on the 12
overlapping stations (**r=0.99, mean |Δ|=₹0.10/kWh**), mutually validating both. The real
ladder is stark and stable: pithead central stations ~**₹1.4–1.6/kWh** (Korba 1.38,
Singrauli 1.39, Rihand 1.40, Sipat 1.42, Vindhyachal 1.60) vs distant central ~**₹2.7–3.9**
(Dadri 3.30, Bongaigaon 3.37, Durgapur 3.93). The flat-freight model compresses all of
these toward ~₹1.9–2.1.

**It tempers the §9 cost-side claim — honestly.** The narrow sub-claim "efficiency proxies
cost *within* the pithead group" **does not replicate** across the two real sources:
CERC-2018 gave pithead-coal eff↔ECR R²=0.62 (n=7), but the contemporaneous data.gov.in
sample gives **R²≈0.00 (n=7)**. Both samples are tiny and they disagree, so that sub-claim
is **not established** — it was thin-sample noise. The reason is visible in the ladder:
pithead-coal ECR is **uniformly low and nearly flat (~₹1.4) regardless of heat rate**, so
efficiency explains almost none of the small within-group variation.

**What is robust** (survives both sources): the pithead flag predicts the cost **level** —
location/freight, not efficiency, sets a low flat floor at the mine and a steep premium far
away. That is the durable form of the §1/§6 thesis: dispatch follows *coal-logistics cost*,
and efficiency is the wrong axis. It is simply not the case that efficiency cleanly proxies
cost even at pithead.

**Still missing.** This is ISGS-only (no state/private merchant plants) and 2021-22/23, not
clean FY2022-23, so it stays a labelled cross-check, not the headline. The FY2022-23 headline
is now the real-ECR override of §7(b) (322 units / 79.3% of generation); §11 below uses these
real ECRs to expose the one remaining modelled term — coal freight.

## 11. The freight axis — why a flat freight compresses the real ladder

The real per-station ECRs (§7b, §8, §10) make the one remaining modelled term — coal
**freight** — visible. Backing out the *implied freight* from the ~30 ISGS stations that
carry a real ECR (`real delivered ₹/t − CIL pithead price − statutory levies`) separates
cleanly: pithead/mine-mouth stations imply only **~₹360/t** (short MGR/conveyor haul),
distant central stations **~₹2,190/t**. That distant figure cross-checks against the
published Indian Railways FY2022-23 coal tariff (~₹1.5/net-tonne-km) as a **~1,460 km**
average lead — a realistic pithead→load-centre haul. This is *why* `02`'s single flat
₹900/t freight compresses the true **₹1.4→3.9/kWh** ECR spread into a narrow ₹1.9–2.1 band:
it overstates cheap pithead stations and understates distant ones. **Per-plant freight /
coal-linkage distance is the missing axis** that real metered ECR (§7b) supplies directly,
and the §4 cost-optimal counterfactual widens once it is un-compressed.

> **Note (scope change).** An earlier version of this section reconstructed an *all-fleet*
> cost by assigning every uncovered unit a two-step freight level (pithead ₹360 / borderline
> ₹1,280 / distant ₹2,190) keyed on the pithead flag, to cover the 100% of units that lacked
> a real ECR. That scaffold has been **retired**: with `06` now carrying real FY2022-23 ECR
> for **322 units / 79.3% of generation**, the real-ECR override (§7b) supersedes it for the
> bulk of the fleet, and the residual ~25% (mostly private IPPs with no public per-station
> ECR) falls back to the real-CIL flat-freight model in `02`. The freight back-out above is
> kept as the durable finding; the full per-plant reconstruction lives in git history.

---

### External / background references

*These are secondary web references for the **contextual** claims in the discussion only — the
China USC-efficiency benchmark, the CO₂ emission-factor methodology, and near-real-time CO₂
nowcasting. They are **not** the data sources for the analysis. The primary data — the CEA/CSE
subcritical dataset, CIL FY2022-23 grade-wise notified prices, and the 86 per-station FY2022-23
energy charges — is sourced from CEA and the individual CERC/SERC tariff orders and genco filings,
cited **inline at point of use**, **per row in [`data/raw/plant_ecr.csv`](data/raw/plant_ecr.csv)**
(each with order number, date, table/page and URL), and catalogued in
[`docs/data_sources.md`](docs/data_sources.md) and [`docs/ecr_scrape_notes.md`](docs/ecr_scrape_notes.md).*

- [POWER — Pingshan Phase II (49.37% net)](https://www.powermag.com/chinas-pingshan-phase-ii-sets-new-bar-as-worlds-most-efficient-coal-power-plant/)
- [POWER — world's most efficient coal fleets](https://www.powermag.com/who-has-the-worlds-most-efficient-coal-power-plant-fleet/)
- [Global Energy Monitor — estimating CO₂ from coal plants (HHV→LHV conversion)](https://www.gem.wiki/Estimating_carbon_dioxide_emissions_from_coal_plants)
- [Carbon Monitor — near-real-time daily CO₂ (Nature Sci. Data)](https://www.nature.com/articles/s41597-020-00708-7)
