# Schema — `data/raw/plant_tariff_details.csv`

A **rich, per-station tariff/technical research table** harvested from FY2022-23 SERC/CERC
tariff orders, true-up orders, metered fuel bills and SLDC merit-order stacks. It is a
**superset** of `data/raw/plant_ecr.csv`: the lean `plant_ecr.csv` (consumed by
`analysis/06_apply_ecr.py`) carries only `match_name, ecr_rs_per_kwh, period, source`,
whereas this file preserves every other useful field the same source documents expose, so
future analyses (cost decomposition, heat-rate vs efficiency, fuel-quality, fixed-cost
recovery, emissions) don't need a re-fetch.

**Rules (inherited, non-negotiable):** every numeric value must be REAL and traceable to a
published document; **never fabricate or interpolate** — leave blank if a source doesn't
give it. ECR/energy-charge vintage MUST be **FY2022-23**. Other technical fields may carry a
nearby-vintage norm (e.g. a multi-year SHR norm) — note it in `basis`/`flag`. One logical
row per station × source. Sparse by design (blank = not stated in that source).

## Columns

| column | unit | meaning |
|---|---|---|
| `match_name` | — | dataset station name, **exact dataset spelling** (so it self-joins via `06`'s `_norm`) |
| `unit_group` | — | which units the figures cover (e.g. "Units 1-7", "Stage-II", "PTPS-6,7,8") |
| `genco` | — | operating company (UPRVUNL, GSECL, NTPC, DVC, …) |
| `state` | — | state / RLDC region |
| `period` | — | fiscal year of the ECR figure (FY2022-23 for the headline) |
| `basis` | — | provenance type: `approved_order` \| `trueup_order` \| `filed_petition` \| `metered_bill` \| `mod_stack` |
| `ecr_rs_per_kwh` | ₹/kWh | **energy/variable charge only** (NOT fixed/capacity). Coal sanity ~1.3–4.5; flag outliers |
| `fixed_charge_rs_per_kwh` | ₹/kWh | fixed/capacity charge per unit, if the order expresses it per-kWh |
| `capacity_charge_rs_cr` | ₹ crore | annual fixed/capacity charge (annual ARR fixed cost), if given as a total |
| `station_heat_rate_kcal_per_kwh` | kcal/kWh | gross station heat rate (norm or actual — say which in `flag`) |
| `aux_consumption_pct` | % | auxiliary power consumption |
| `specific_coal_consumption_kg_per_kwh` | kg/kWh | specific coal consumption |
| `secondary_oil_ml_per_kwh` | ml/kWh | secondary fuel (oil) consumption |
| `transit_loss_pct` | % | coal transit / handling loss allowed |
| `gcv_coal_kcal_per_kg` | kcal/kg | as-billed/as-received GCV of coal used in the computation |
| `landed_coal_cost_rs_per_tonne` | ₹/t | delivered (landed) coal price = pithead + freight + levies |
| `coal_grade` | — | coal grade if stated (G1–G17 / GCV band) |
| `gcv_oil_kcal_per_litre` | kcal/L | GCV of secondary oil |
| `landed_oil_cost_rs_per_kl` | ₹/kL | landed cost of secondary oil |
| `generation_mu` | MU | net / ex-bus generation (approved or actual — note in `flag`) |
| `plf_pct` | % | plant load factor, if the order states it |
| `capacity_mw` | MW | station capacity as stated in the order |
| `source` | — | precise citation: doc title + date + table/page (e.g. "RERC review order RERC/2031/22, Table 3, FY2022-23") |
| `source_file` | — | archived raw artefact filename under `data/raw/sources/` |
| `flag` | — | caveats: e.g. `filed_petition_not_order`, `gen-wtd across units`, `norm not actual`, `outlier>4.5` |

## Which sources populate which fields (observed)

- **MahaGenco/MSPGCL monthly Energy Bill** → `ecr` (metered Energy Rate ₹/Unit), `gcv_coal`,
  `landed_coal_cost`, `specific_coal_consumption`, `gcv_oil`, `landed_oil_cost`, `generation_mu`.
- **MahaSLDC DISCOM-wise MOD stack** → `ecr` (Approved Variable Charge), `capacity_mw`, `basis=mod_stack`.
- **RERC / SERC generation tariff order** → `ecr` (Rate of energy charges = Energy ₹cr / Net Gen MU),
  `capacity_charge_rs_cr`, `station_heat_rate`, `aux_consumption_pct`, `transit_loss_pct`,
  `gcv_coal`, `landed_coal_cost`, `generation_mu`, `plf_pct`.
- **HPGCL-style ARR petition** → `ecr` (per HERC MYT Reg 31), `generation_mu`, `aux_consumption_pct`,
  `capacity_charge_rs_cr`, `gcv_coal`, `landed_coal_cost` — `basis=filed_petition`.

Consumers should read with `comment='#'` and treat blanks as NaN.
