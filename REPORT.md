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

**(b) FY2022-23 *metered per-station* ECR — wanted, but the feeds were down.**
The genuinely FY2022-23, station-level energy-charge feeds (**Grid-India SCED**,
**POSOCO eLibrary**, **state SLDC daily merit-order stacks**, **MERIT**) all
returned HTTP 503 / connection-refused this session. So the FY2022-23 override
(`06_apply_ecr.py`, reading `data/raw/plant_ecr.csv`) has **0% real coverage** — we
refuse to fabricate it — and the headline cost falls back to the real-CIL model in
(a). `06` reports this explicitly.

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

> **Network status (2026-06, Full access):** cercind.gov.in and coal.gov.in are
> reachable (CERC even hosts the CIL price-notification archive). grid-india.in /
> POSOCO eLibrary / meritindia.in returned **HTTP 503** — so the FY2022-23 metered
> per-station ECR could not be harvested. `analysis/07_fetch_ecr.py` re-fetches the
> CIL prices and CERC orders from source and probes those feeds; it writes
> `plant_ecr.csv` only when a real FY2022-23 feed comes back up.

---

## 8. Extensions delivered & their data limits

| # | Extension | Status | Blocking data (not in file) |
|---|---|---|---|
| 1 | Variable cost (₹/kWh) | Domestic price on **real CIL FY2022-23** notified prices + levies; FY2022-23 per-station override layer (`06`) ready but feeds down; **CERC 2018-basis cross-check** (`08`) | FY2022-23 *metered* per-station ECR (SCED/SLDC/MERIT) for the within-fleet freight spread |
| 2 | Grid-region / load proximity | Coarse proxy (~60% coverage) | Lat/long, RLDC bus, load-pocket, congestion |
| 3 | Flexibility / ramp (H1) | Framework + synthetic demo | Block-level SCED generation |
| 4 | Cost-vs-carbon re-dispatch | Done (stylised), on real-CIL cost | Transmission/must-run limits for realism |

See [`docs/data_sources.md`](docs/data_sources.md) for exactly where to obtain the
missing inputs. **This session reached cercind.gov.in (CERC orders + CIL price
archive) and coal.gov.in, but grid-india.in / POSOCO / meritindia.in returned HTTP
503**, so the FY2022-23 metered per-station ECR and live SCED block data could not
be fetched in-session.

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
clean FY2022-23, so it stays a labelled cross-check, not the headline. Full FY2022-23
all-fleet ECR still needs the metered MERIT/SCED/SLDC feeds (blocked from this environment)
or the landed-cost reconstruction route (CIL price + coal linkage + railway freight).

---

### Sources
- [POWER — Pingshan Phase II (49.37% net)](https://www.powermag.com/chinas-pingshan-phase-ii-sets-new-bar-as-worlds-most-efficient-coal-power-plant/)
- [POWER — world's most efficient coal fleets](https://www.powermag.com/who-has-the-worlds-most-efficient-coal-power-plant-fleet/)
- [Global Energy Monitor — estimating CO₂ from coal plants (HHV→LHV conversion)](https://www.gem.wiki/Estimating_carbon_dioxide_emissions_from_coal_plants)
- [Carbon Monitor — near-real-time daily CO₂ (Nature Sci. Data)](https://www.nature.com/articles/s41597-020-00708-7)
