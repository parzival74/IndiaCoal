# ECR scrape notes — FY2022-23 per-station Energy Charge Rate

Running log for the `docs/SCRAPE_ECR_PROMPT.md` task: fill `data/raw/plant_ecr.csv`
with REAL, FY2022-23, per-station energy/variable charge (₹/kWh), each with a
verifiable citation. **No fabricated or wrong-vintage rows.**

## Session log

### 2026-06-01 — kickoff (local session, on flight WiFi)

**Environment constraint that dominates everything this session:** the operator is
on in-flight WiFi, throughput ≈ **6.5 KB/s**. Large gov PDFs (tariff orders are
often 5–100 MB) are effectively un-downloadable locally; even a 4 MB MahaGenco fuel
sheet stalls. `pip install pandas scipy …` **failed** — the scipy cp314 wheel
(20 MB) timed out after 6 resume attempts. No `pandas` exists in any interpreter on
the machine yet (`python3.13`, `python3.14`, `/usr/bin/python3` all bare).

**Pivot:** `WebSearch` + `WebFetch` run server-side (not over the slow local
flight link), so they're the viable way to *read* orders and extract numbers. Write
verified rows into `plant_ecr.csv` by hand (no pandas needed for that). Defer running
`06_apply_ecr.py` / `run_all.py` until `pandas` can be installed on a fast connection.

**Reachability probed (curl from the laptop):**

| Host | Result |
|---|---|
| github.com, www.data.gov.in, cercind.gov.in | HTTP 200 (reachable) |
| meritindia.in | TLS handshake **reset by peer** (curl 35) — MERIT JSON route blocked |
| merc.gov.in (root) | **timeout** at 30 s |
| www.mahagenco.in | reachable but **very slow** (served a 4 MB PDF at ~6.5 KB/s; partial only) |

(Reachability is bandwidth-limited, not geo-blocked, except meritindia.in which
actively reset the TLS connection.)

**Source leads identified (verified via WebSearch):**

- **MahaGenco / MSPGCL (genco #1, Maharashtra, ~7.6 GW)** publishes **monthly
  "Fuel data for <month>"** PDFs under `mahagenco.in/wp-content/uploads/…` that
  carry, per thermal station, the **"Approved Variable Charge (Rs/kWh) as per Tariff
  Order"** plus the month's actual variable charge. This is exactly the FY2022-23
  per-station energy charge, station-resolved. Example file:
  `https://www.mahagenco.in/wp-content/uploads/2022/12/Fuel-data-for-Apr-22.pdf`
  (Apr-2022 = first month of FY2022-23). The "approved" figure is constant across
  the year, so ONE FY23 month's sheet yields all MahaGenco stations.
- The governing MERC genco orders: **Case 296 of 2019** (3rd-control-period MYT,
  FY2020-25 base) and **Case 227 of 2022** (MTR / true-up incl. FY2022-23).
  NOTE: the prompt's "Case 217/2022" is actually **MSEDCL** (the *distribution* co),
  not the genco — do not chase it for generation ECR.
- MahaGenco landing page for these: `mahagenco.in/Approved-Tariff` and the monthly
  fuel-data disclosures (regulatory format).

**Status of deliverable:** `data/raw/plant_ecr.csv` not yet created — 0 rows written.
Worklist (Step 1) not yet generated (needs pandas). Nothing committed.

### TODO to resume (in order)
1. **Install pandas/numpy/scipy/openpyxl** (+ optional pdfplumber/pypdfium2) on a
   fast connection. `python3.13 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
   3.13 has prebuilt wheels; 3.14 also does but the *download* is what failed.
2. Run **Step 1** worklist snippet (in the prompt) to get the exact ~124 stations /
   ~96 GW grouped by company — focuses the search on the top-10 gencos.
3. **MahaGenco first** (reachable lead): WebFetch the FY23 fuel-data sheet, extract
   per-station Approved Variable Charge (₹/kWh), write rows with citation
   `"MSPGCL monthly fuel-data disclosure, Apr-2022, Approved Variable Charge as per
   MERC Tariff Order (Case 296/2019 MYT, FY2022-23)"`.
4. Work down the genco list (UPRVUNL, RRVUNL, TANGEDCO, WBPDCL, GSECL, APGENCO,
   TSGENCO, KPCL, HPGCL) via each SERC's FY2022-23 tariff/true-up order, using
   WebFetch to read and extract the FY2022-23 energy-charge column.
5. Run `06_apply_ecr.py`, verify coverage + match_name correctness, then
   `run_all.py` for determinism; update REPORT §7 + CLAUDE.md; commit; push.

### 2026-06-01 — resumed (on land, ~666 KB/s; direct downloads now viable)

**Method that works:** download the gov PDF directly with `curl` (fast on land) OR
have `WebFetch` pull it server-side (it saves the full file locally even though it
can't parse PDF), then extract text with **`pdftotext -layout`** (poppler is
installed at `/opt/homebrew/bin/pdftotext`). Deps installed into `.venv`
(pandas 3.0.3, scipy 1.17.1). meritindia.in still TLS-resets; everything else
needed so far is reachable.

**MahaGenco (genco #1) — DONE.** Source = MSPGCL's **monthly Energy Bill to MSEDCL**
(`mahagenco.in` fuel-data PDFs), which carries each station's metered **Energy Rate
(₹/Unit)** plus the MahaSLDC DISCOM-wise MOD stack. Pulled the two FY2022-23 endpoint
months (Apr-2022, Mar-2023), generation-weighted across unit-groups, took the
two-month mean. The MOD stack also prices IPPs selling to MH — RattanIndia Amravati
(approved VC constant 2.4523) and JSW Jaigad map cleanly to dataset gap stations.

### Rows written so far (9 stations / 30 units / ~12 GW)
| match_name | ₹/kWh | basis |
|---|---|---|
| Bhusawal | 3.542 | MSPGCL bill, gen-wtd mean Apr-22 & Mar-23 |
| Chandrapur_Coal | 3.125 | " |
| K_Kheda Ii (Khaperkheda) | 3.231 | " |
| Koradi | 3.175 | " (subcritical 210 MW unit) |
| Nashik | 3.868 | " |
| Paras | 3.287 | " |
| Parli | 4.533 | " — **FLAGGED >4.5** (old, coal-distant; Mar-23 month 4.88). Real metered, kept. |
| Amaravati TPP | 2.452 | MahaSLDC MOD stack, RattanIndia approved VC (constant FY23) |
| JSW Ratnagiri TPP | 3.939 | MahaSLDC MOD stack, JSW Jaigad U1, mean Apr-22 & Mar-23 |

Validated by `06_apply_ecr.py`: all 9 fuzzy-matched correctly, 0%→6.6% unit coverage.
Real MH ECRs (₹3.1–4.5) sensibly exceed the CIL-notified-price model (₹2.2–2.6) —
FY2022-23 actual delivered coal cost ran above notified pithead price.

### 2026-06-01 — central NTPC stations from the MahaSLDC MOD stack (already-downloaded data)

The two MahaGenco fuel PDFs each embed a **DISCOM-wise MOD stack of Variable Charges**
listing every generator supplying MH (central CS + IPPs) with its CERC/MERC **Approved
Variable Charge (Rs/KWh)** and change-in-law. The two stacks bracket FY2022-23:
**MAY-2022** stack (inside Fuel-data-for-Apr-22.pdf) and **APR-2023** stack (inside
Fuel-Data-for-Mar-2023.pdf). For the NTPC central stations change-in-law = 0, so the
Approved VC IS the pure energy charge. Capacity-weighted across each station's stages
(by ISGS share MW), then mean of the two months. Added 4 NTPC stations that map to
subcritical dataset rows:

| match_name | ₹/kWh | basis |
|---|---|---|
| Vindh_Chal Stps | 1.633 | VSTP-I..V cap-wtd; pithead, mean May-22 1.600 & Apr-23 1.667 |
| Korba Stps | 1.612 | KSTPS I&II + III cap-wtd; pithead, mean 1.505 & 1.719 |
| Sipat Stps | 1.568 | SSTPS-II (subcritical 2×500 stage); mean 1.589 & 1.546 |
| Mouda Stps | 4.151 | MSTPS-I (subcritical 2×500, coal-hauled to Nagpur); mean 4.179 & 4.123 |

NOTE: CSEB "Korba-West/-V/-West Ext" are a DIFFERENT (Chhattisgarh state) Korba and do
NOT collide — `_norm("Korba Stps")="korba"` matches only the NTPC row; CSEB rows norm to
"korba west"/"korba v dspm" and keep the model. Other CS rows in the stack (CGPL/Tata
Mundra, Solapur, Khargone, Gadarwara, Lara, APML Tiroda) are supercritical → NOT in the
subcritical-only dataset, so not written. Validated: 13 rows → **54/455 units = 11.9%**.

### 2026-06-01 — Rajasthan RRVUNL via RERC review order (cer.iitk.ac.in)

Source = **RERC review order RERC/2031/22**, Table 3 "Approved tariff for FY 2022-23"
(review of the order in Petition 1980/22 dtd 23.06.2022; the energy-charge rate was
left unchanged in the review). The table gives, per station, **"Rate of energy charges"
(Rs/kWh) = Energy charges (Rs Cr) / Net Generation (MU)** for FY2022-23 — exactly the
energy/variable component, approved. Fetched as a text PDF via the IIT-Kanpur ERC Hub
(`cer.iitk.ac.in`), archived to `data/raw/sources/rerc_rvun_review_2031-22_fy2022-23.pdf`.

| match_name | ₹/kWh | station (units) | Energy Cr / Gen MU |
|---|---|---|---|
| Suratgarh | 4.220 | STPS (1-6) | 4150.92 / 9837.39 |
| Kota | 3.390 | KTPS (1-7) | 2758.05 / 8145.77 |
| Chhabra Tps | 3.050 | CTPP (1-4) | 1999.10 / 6558.26 |
| Kalisindh | 2.950 | KaTPP (1-2) | 2441.45 / 8266.90 |

Validated: 17 rows → **71/455 units = 15.6%**. All four fuzzy-matched correctly.

### 2026-06-01 — Haryana HPGCL via FY2022-23 tariff petition (hpgcl.org.in)

Source = **HPGCL FY2022-23 tariff petition** (`HPGCL_Tariff_Petition_2022-23_(1).pdf`,
text-based, 69 pp), **Table 38 "Computation of ECR for FY 2022-23"** = **Table 47
"Tariff Summary for FY 2022-23"** — per-unit Energy Charge Rate (Rs/kWh), energy/variable
charge only, computed per HERC MYT Regulation 31. Archived to
`data/raw/sources/hpgcl_tariff_petition_fy2022-23.pdf`.

**Provenance caveat (flagged in the `source` field of each row):** these are HPGCL's
**FILED PETITION (proposed)** figures, NOT the HERC-approved generation order. The
separate HERC HPGCL *generation* tariff/true-up order for FY2022-23 could not be located
online this session — the HERC orders that surface for "true-up FY2022-23" (`O20240216.pdf`,
`O20240305a(1).pdf`) are the **HVPNL transmission / UHBVNL-DHBVNL distribution** orders,
which carry only aggregate power-purchase cost (~₹3.83-4.52/kWh), not per-station HPGCL ECR.
Kept the petition values because they are real, vintage-correct, energy-charge-only and
fully traceable — but labelled as petition, not order. Re-pull the HERC generation order
and replace if/when found.

| match_name | ₹/kWh | station (units) | petition value |
|---|---|---|---|
| Panipat | 3.723 | PTPS-6 (3.812), PTPS-7 & -8 (3.686) | gen-wtd over 1407.29/1688.38/1688.38 MU |
| Yamunanagar TPP | 3.574 | DCRTPP-1/2 | 3.574 each |
| Rajiv Gandhi Tps Hisar | 3.639 | RGTPP-1/2 (Hisar/Khedar) | 3.639 each |

Validated: 20 rows → **78/455 units = 17.1%**. All three matched correctly.

### Not-found / ambiguous / deferred
- meritindia.in JSON route: unreachable this session (TLS reset). Use SERC orders
  (Route A) instead.
- **HERC HPGCL generation order FY2022-23:** not located (see HPGCL caveat above); used
  the filed petition instead, flagged.
- **UPRVUNL (UP, 18 units / 5.05 GW):** uperc.org lists only the current year on
  `Tariff_Order_Users.aspx`; the FY2022-23 UPRVUNL generation ARR/true-up order PDF did
  not surface via search (App_File results were Discom/transmission orders only). Deferred —
  needs the uperc.org "Previous Years" archive or the cer.iitk UPERC hub.
- **GSECL (Gujarat, 18 units / 3.86 GW):** the GERC GSECL *generation* order did not
  surface (search returned GETCO/UGVCL transmission/discom orders). The GSECL
  **true-up petition** `Final-Petition-for-GSECL-True-up-F.Y.-2022-23-ARR_FY-24-25` is
  downloadable from gsecl.in but the server is very slow (curl timeouts). In progress.
- **WBPDC (West Bengal, 16 units / 4.2 GW):** WBERC tariff PDFs (e.g. TP98) are **scanned**
  (HP Scan, 0 extractable text) → not parseable without OCR. Skipped.
- Local raw-artefact archiving under `data/raw/sources/` deferred where files are
  too large for the flight link; `mahagenco_fuel_apr22.pdf` partially downloaded
  (~0.9 MB of 4.1 MB). Re-pull complete copies on a fast connection for the audit trail.

### 2026-06-01 — parallel-agent harvest, 9 gencos (one agent per genco, operator-verified)

Ran one research agent per genco against its FY2022-23 SERC/CERC order, each writing an
isolated staging CSV under `data/raw/sources/staging/`; **every ECR value verified by the
operator against the cited source table line before merge** ("parallel agents, I verify").
Merged the headline-eligible rows into `data/raw/plant_ecr.csv` and the full per-substation
detail (25-col schema, `docs/plant_tariff_schema.md`) into `data/raw/plant_tariff_details.csv`.

**Vintage discipline applied** (same rule as the CERC-2018 cross-check): an order's per-FY
ECR is FY2022-23 vintage only if the energy charge for that year is computed on
contemporaneous/actual FY2022-23 fuel cost. True-up orders (actual FY22-23 cost) and annual
FY2022-23 ARR/tariff orders = **headline-eligible**. MYT orders that set a base ECR pegged to
old (≈2019) coal price and hold it FLAT across the control period = **cross-check only,
EXCLUDED** from the headline (kept in the rich table, flagged).

**Headline rows added (35 stations across 9 gencos):**

| genco | source (order / table) | stations added |
|---|---|---|
| GSECL (Gujarat) | GERC Order Case 2025/2021 dtd 30.03.2022, Table 6.1 (approved ECR FY22-23) | Wanakbori 4.232, Ukai_Coal 3.915, Gandhi Nagar 4.293, Sikka Extn 3.956, Kutch Lignite 3.113 |
| TANGEDCO (TN) | TNERC Order 7/2022 dtd 09-09-2022, Table 4-47 | Tuticorin 3.96, **Mettur 4.996** (merged 5.00+4.99), North Chennai 3.59, North Chennai Extension 3.94 |
| PSPCL (Punjab) | PSERC Petn 68/2021 dtd 13-Apr-2022, Table 7.7 p.203 | Ropar 3.6037, Ghtp (Leh.Moh.) 3.6824 |
| DVC | JSERC Order 30-09-2024 (DVC true-up FY22-23), Table 38 p.96 | Durgapur 3.434, **Mejia 3.649** (merged U#1-6 + Ext U#7&8), Chandrapura 3.624 (Jharkhand), Durgapur Steel Tps 3.793, Koderma 3.540, Raghunathpur TPP Ph-I 3.881, Bokaro A ''Exp'' 2.771 |
| CSPGCL (CG) | CSERC Petn 10/2024(T) dtd 01-06-2024, Final True-Up FY22-23 (actual coal+oil / actual net gen) | **Korba-West 1.508** (merged HTPS+KWTPP), Korba-V(Dspm Tps) 1.612, Marwa TPP 1.837 |
| WBPDCL (WB) | WBERC TP-95/20-21 dtd 26.07.2022, via WBPDCL MFCA notes in WBSEDCL FY23-26 Petn Appendix A1 | Kolaghat 2.7841, Bakreswar 1.8290, Santaldih 1.9497, Bandel 2.1709 (Unit-V), Sagardighi TPP 1.7911 (Stage-I) |
| UPRVUNL (UP) | UPERC State Discoms Order dtd 25-05-2023, Table 5-16 p.349 (FILED APR, flagged) | Anpara 1.941, Obra-A 2.58, Paricha 3.657, H_Ganj B 3.94 |
| APGENCO (AP) | APERC FPPCA Common Order O.P.57-68/2024, Sec(ii) actual VC (true-up) | Rayal Seema 4.33, Vijaywada (Dr. N.TATA Rao Tps) 3.99, Vijaywada TPP-Iv 3.63 |
| NLC (lignite) | CERC 2019-24 GT orders (219/GT/2019; 386/GT/2020), FY22-23 column | Neyveli New TPP 2.115, Barsingar Ligniteite 0.848 |

**Three `_norm` collisions** resolved by writing ONE generation-weighted merged row per
colliding key (06 can only hold one ECR per `_norm` key); full per-substation fidelity kept
in `plant_tariff_details.csv`:
- `korba west`: Korba-West (HTPS 4×210 @1.589) + Korba-West Ext (KWTPP 500 @1.395) → **1.508**
- `mejia`: Mejia (MTPS U#1-6 @3.715) + Mejia Tps Ext (U#7&8 @3.577) → **3.649**
- `mettur`: Mettur (5.00) + Mettur Tps Ext (4.99) → **4.996**

**Split-station mappings** (dataset capacity used to pick the right substation): Bandel = Unit-V
(1×210, matches dataset); Sagardighi = Stage-I representative; UPRVUNL Obra-A = order's OBRA-B
(operational 5×200, the order's OBRA-A had zero FY22-23 gen); H_Ganj B = Harduaganj Extension.

**Cross-check only — EXCLUDED from headline** (base ECR held flat, not FY22-23 vintage; in the
rich table flagged, NOT in `plant_ecr.csv`):
- **TSGENCO** (TSERC MYT Order 22.03.2022, Table 75): Bhadradri 2.363, K_Gudem New 2.409,
  Kakatiya II 2.925, Kakatiya I 3.035, R_Gundem-B 2.988. Sec 6.14.9: "Base ECR remains the
  same for the entire 4th control period FY2019-20 to FY2023-24."
- **MPPGCL** (MPERC MYT P-53/2020 dtd 19-05-2021, Table 43): Amar Kantak Ext 1.413, Satpura
  2.330, Sanjay Gandhi 2.051. Base/working-capital ECR pegged ≈early-2019; both true-ups
  (P-71/2023, P-76/2024) state "no truing up of Energy Charges."

**KPCL (Karnataka): honest skip** — KERC orders publish no per-station ECR for Raichur/Bellary;
0 rows written rather than fabricate.

**Cross-assignment audit (06 forward keying):** 06 maps each ECR row → its single closest plant
`_norm` key, then assigns by *exact key equality*, so near-miss plants do NOT inherit a neighbour's
ECR. Verified in the regenerated `data/plant_cost_blended.csv`: `Tuticorin JV` / `Tuticorin JV
Stage-IV` (NTPL, a different JV) and all four other Neyveli variants (`St Ii`, `Tps(Z)`, `Exp -Ii`,
`Fst Ext`) correctly stay on the model; only the intended `Neyveli New TPP`, `Tuticorin`,
`Chandrapura`/`Chandrapur_Coal`, `Korba Stps`(NTPC)/`Korba-West`(CSPGCL) resolved to their own rows.

Validated by `06_apply_ecr.py`: **55 ECR rows → 197/455 units = 43.3% coverage** (up from 78
units / 17.1%). Non-06 pipeline outputs (01–05, 08, 10, 11) reverted — their only diffs were
float-ULP / redispatch tie-break noise from the local env (they don't consume `plant_ecr.csv`).

### Raw artefacts (this harvest), under data/raw/sources/
`gsecl_gerc_tariff_order_fy2022-23.pdf`, `tneb_jmk_to_fy2023.pdf`,
`pspcl_pserc_tariff_order_to_fy2022-23.pdf`, `dvc_jserc_2024a.pdf`,
`cspgcl_cserc_tariff_order_fy2024-25.pdf`, `wbpdcl_wbsedcl_appendixA1.pdf`,
`uperc_statediscoms_fy2023-24.pdf`, `apgenco_aperc_FPPCA_FY2022-23.pdf`,
`nlc_tsii_219-GT-2019.pdf`, `nlc_barsingsar_386-GT-2020.pdf`,
`tsgenco_myt_order_22032022.pdf`, `mppgcl_myt_p53-2020_19may2021.pdf`.
Per-genco staging CSVs (with full verification notes per row) under
`data/raw/sources/staging/`.

### Still-open coverage gaps (future sessions)
- WBPDCL remaining units: order PDFs are scanned → only the 5 stations recoverable via the
  WBSEDCL Appendix-A1 MFCA debit-notes were captured; deeper unit splits need OCR.
- NLC TPS-II / TPS-II Exp / TPS-I Exp: no CERC 2019-24 GT *order* published (only 2025 true-up
  TV letters); data.gov.in figures are 2021-23 vintage → excluded per vintage rule.
- HPGCL: still the filed petition, not the HERC-approved generation order (not located).
- UPRVUNL: filed APR estimate, not a standalone approved generation order.

## Wave 3 — NTPC + private IPPs (2026-06-01): 55 → 77 ECR rows, 43.3% → 62.9% (286/455 units)

All FY2022-23, energy/variable charge ONLY, each row arithmetic-checked (`rate × MU/10 ≈ var-Cr`)
against its cited table. Staging CSVs (full per-row verification) under `data/raw/sources/staging/`.

**NTPC NR/ER — UPERC APR FY2022-23 power-purchase table** (`staging/ntpc_uperc.csv`, FILED estimate):
order "Approval of ARR…FY2023-24, APR of FY2022-23, True-up FY2021-22" (25-05-2023), Sec d.a NTPC
p.351-352, col "Annual Energy/Variable Charge (Rs/kWh)". 6 stations, UP-drawal gen-weighted where the
station has stage splits: Rihand 1.754 (I/II/III 1.81/1.74/1.72), Singrauli 1.67, Unchahar/FGUTPS
4.357 (I-IV), Dadri/NCTPS-coal 4.386 (gas DADRI-GPS 13.42 excluded), Kahalgaon/KHTPS 3.614,
Farakka/FSTPS 3.55. (NTPC ECR ~uniform across beneficiaries; UPERC table is a valid source.)
Korba/Vindhyachal/Sipat/Mouda in the same table were ALREADY covered (MahaSLDC) — used as cross-checks
(consistent); Tanda/Solapur/Barh/NPGCL/Karanpura/Darlipali are absent from the subcritical dataset
(440 MW old or 660 MW supercritical), correctly skipped.

**NTPC SR — APERC FPPCA true-up** (`staging/ntpc_sr.csv`, ACTUAL): Common Order O.P.57-68/2024 p.53
col "Variable Cost Actual Rs/kWh". Ramagundam 4.085 (I&II 4.14 + III 3.84), Simhadri 4.451
(St1 4.49 + St2 4.36), Vallur/NTECL 3.478 (192.70 Cr / 554 MU, CGS table). TANGEDCO cross-check
discarded — its central-station tables stop at FY2020-21 (wrong vintage).

**NTPC-JV Bihar + Barauni — BERC** (`staging/ntpc_bihar.csv`, `staging/berc_barauni.csv`):
NBPDCL Tariff Order FY2023-24 (Case 16/17 of 2022, 23-03-2023), Table 5.17 p.207-208 "Power Purchase
Cost for FY 2022-23 as computed by Commission", col "Energy Cost (Rs./kwh)". Muzaffarpur/KBUNL-II 2.92,
Nabinagar/BRBCL 2.75, **Barauni/BTPS 2.685** (uniform Stage I+II; covers dataset `Barauni` +
`Barauni (Ext)`). Commission-computed FY2022-23 (true-up pending) → flagged filed_petition.

**Talcher Kaniha — MERGED** (BERC Stage I 2.08 + APERC Stage II 1.94): dataset `Talcher Stps` is the
full 6×500 = 3000 MW station, so cap-weighted (1000·2.08 + 2000·1.94)/3000 = **1.987**. Both BERC and
APERC rows `_norm` to key `talcher`; single merged row (precedent: Korba-West/Mejia/Mettur).
(BERC `Talcher Stage I` 2.08 reconciles APERC `Talcher St II` 1.94 — complementary stages, not a clash.)

**Private IPPs — UPERC APR FY2022-23** (`staging/uperc_ipp.csv`, same table, Sec "Thermal", FILED):
8 rows — Anapara "C"/LANCO 2.61, KSK Mahanadi/Akaltara 3.38 (multi-state PPA, UP share), M.B.Power/
Anuppur 2.87, RKM/Uchpinda 2.22, Rosa 3.14 (both `Rosa TPP`→`rosa` and `Rosa TPP Ph-1`→`rosa 1`
keys), TRN/Nawapara 2.32, Bajaj/Barkhera 4.62 (small 45 MW, high but in-range). Several are 600 MW
units that CSE nonetheless included in the subcritical table, so they are legitimate dataset members.
BERC GMR/Kamalanga 1.20 and JITPL/Derang 1.12 looked anomalously low → HELD OUT of headline.

**Jhajjar/APCPL "Indra Gandhi STPP" 4.09 — SECONDARY** (`staging/ntpc_jhajjar_bhilai.csv`, flagged):
ICRA "Aravali Power Company Pvt Ltd: Ratings reaffirmed" (19-Mar-2024) p.1, verbatim "the variable/
energy charge stood at Rs. 4.09 per unit for FY2023". Energy-only, correct vintage, in sanity band, but
a credit-rating agency figure — NOT a regulatory order, so the `source` string flags it explicitly.
Primary CERC 489/GT/2020 ECR 3.475 is 2018-basis (excluded); HERC DISCOM order unreachable (timeouts).

**Bhilai/NSPCL — HONEST SKIP**: NSPCL is a SAIL captive plant — coal cost borne entirely by SAIL,
"energy charges do not form part of the tariff" (CRISIL 03-07-2023). CSERC 4.44 is an all-in landed
rate (not energy-only); CERC 396/GT/2020 2.336 is 2018-basis. No publishable FY2022-23 ECR → 0 rows.

**Counterfactual on the new 62.9%-real blended cost** (06): real ECRs run systematically ABOVE the
flat-freight model for distant state/IPP plants (the model compresses the freight spread), so as-run
fuel cost rises to ₹206,922 cr / 777.9 MT; as-run is **+16.1% above cost-optimal** (₹178,186 cr);
cost-vs-carbon gap **+43.7 MT CO₂ for +₹35,841 cr**. The "cheapest coal is also dirtiest" divergence
holds and widens as coverage grows.

### Raw artefacts (Wave 3), under data/raw/sources/staging/
`berc_discoms_fy2023-24.pdf` (471 pp), `apgenco_aperc_FPPCA_FY2022-23.pdf`,
`icra_apcpl_rating.pdf`, `cerc_apcpl_489-GT-2020.pdf`, `cerc_396-GT-2020.pdf`,
`sail_bhilai_cserc_extract.pdf`; UPERC PDF already on disk from Wave 2.

## RJ+GJ-lignite cluster (agent)

Target: 4 Rajasthan/Gujarat lignite stations — `Jallippa Kapurdi TPP` (Raj West/JSW
Barmer), `Bhavnagar TPP` (GSECL), `Surat Lignite` (GIPCL SLPP), `Akrimota Lig` (GMDC).
Result: **1 FOUND (Bhavnagar), 3 NOT-FOUND.** Staging row in
`data/raw/sources/staging/rj_gj_cluster.csv`.

**Bhavnagar TPP — FOUND (real, FY2022-23). ECR = 2.976 ₹/kWh.**
The on-disk GSECL order already carries it. `gsecl_gerc_tariff_order_fy2022-23.pdf`
(GERC Order dtd 30.03.2022, Case No.2025 of 2021), **Table 6.1 "Energy Charges
Approved for FY 2022-23", Sr.9 "BLTPS*" = 2.976 ₹/kWh (p.141).** BLTPS = Bhavnagar
Lignite TPS, 2×250 MW CFBC, GSECL captive lignite. This is the *same order + same
Table 6.1* that supplied every existing GSECL row (Wanakbori 4.232, Ukai 3.915,
KLTPS 3.113…), so basis = `approved_order`, identical to its siblings. Supporting
norms from the same order: SHR 2623 kcal/kWh, aux 11%, oil 1.00 ml/kWh, transit
0.80% (Table 5.14 approved-params summary, p.45); approved gross gen 1201.03 MU,
PLF 27.42% (Table 5.15); fixed chg 168.60 Cr (Table 6.2). Caveat noted in the row:
Table 5.15 col-10 *net* fuel-cost/unit shows 2.81, but the headline ECR the
Commission "approves" and that the sibling GSECL rows use is Table 6.1 = 2.976.
PPA-based (marked * in Table 6.1) but a genuine GERC-approved FY2022-23 energy charge
(Sikka Extension, already in the dataset, is also a PPA-based * row). Arithmetic
check: 2.976 ₹/kWh is in-band for lignite; the order's own Table 5.15 net 2.81 and
gross-of-aux variants bracket it.

**Jallippa Kapurdi TPP (Raj West Power / JSW Energy Barmer, 8×135 MW lignite) —
NOT FOUND (no FY2022-23 vintage).** RERC tariff-orders index
(`rerc.rajasthan.gov.in/rerc-user-files/tariff-orders`, full list scraped & parsed)
shows the *latest* Raj West / JSW Energy (Barmer) **generation** tariff orders are:
Petn **1286/17** "Determination of ARR and tariff for **FY 2018-19**" (13.06.2019),
and Petn **1583/19** (I.A.2/2020) "Interim tariff for **FY 2020-21**" (23.04.2020).
There is **no RERC order determining an FY2022-23 (or even FY2021-22) energy charge**
for Raj West — the most recent is an FY2020-21 *interim*. An FY2018-19/FY2020-21
figure = WRONG VINTAGE for the headline → SKIP. Also checked: cer.iitk RERC hub,
prayaspune archive docs 941 (RERC/1539/19) & 1347 (RERC/2193/24) — both are RRVPNL
**transmission** true-ups, not Raj West generation. WebSearch surfaced no FY2022-23
Raj West generation ECR.

**Surat Lignite (GIPCL SLPP, 4×125 MW lignite) — NOT FOUND.** GIPCL SLPP supplies
GUVNL under a long-term PPA; its variable/energy charge is recovered through GUVNL's
**FPPPA fuel pass-through**, not a GERC per-station ECR determination. GERC tariff-
orders page (`gercin.org/order-category/tariff-orders`) lists **no** GIPCL/SLPP
generation energy-charge order; cer.iitk GERC hub lists "Surat Lig. PP" / "Surat Lig.
PP (Slpp Station-II)" as stations but carries no per-station ECR. No published
FY2022-23 energy charge → SKIP. (Annual-report cost-of-generation would be a company
self-disclosure, not a regulatory ECR — excluded per rules.)

**Akrimota Lig (GMDC Akrimota TPS, 2×125 MW lignite) — NOT FOUND.** Downloaded &
parsed the one located GERC order, Case **2279/2023** (GUVNL vs GMDC, **29.05.2024**,
`staging/gmdc_gerc_2279-2023_trueup_29052024.pdf`, 20 pp). It renegotiates **only
fixed-cost parameters** for FY2022-23 — O&M Rs 32.50 lakh/MW, RoE, SHR (approved 2534
vs actual 2929 kcal/kWh), aux 11%→12% — and contains **no energy/variable charge
(₹/kWh)**. Like GIPCL, GMDC's energy charge is FPPPA pass-through to GUVNL, not a
GERC ECR. No published FY2022-23 ECR → SKIP.

Net coverage delta from this cluster: **+1 station (Bhavnagar TPP, 2 units, lignite).**


## WB cluster (agent) — 2026-06-01

Target: 4 West Bengal stations (Budge Budge, Haldia, D.P.L., Maithon Rb TPP), none
previously in `plant_ecr.csv`. Staging → `data/raw/sources/staging/wb_cluster.csv`
(4 verified rows, human verifies + merges; agent did NOT touch `plant_ecr.csv`).
NOTE: dataset rows "Durgapur" (DVC DTPS) and "Durgapur Steel Tps" (DSTPS) are already
covered via JSERC and are DIFFERENT plants from "D.P.L." (Durgapur Projects Ltd, WB state).

**Budge Budge — FOUND, Rs 1.96/kWh (FY2022-23 admitted).** WBERC Order Case
**TP-96/20-21**, "Tariff Application of CESC Ltd for FY2020-21/2021-22/2022-23"
(CESC is a vertically-integrated licensee; WBERC sets its generation energy charge).
**Annexure-4D "Fuel Cost Determination of Budge Budge Generating Station", Sl.22
"Ex-bus energy charge (20/3)" Admitted 22-23 = 1.96** Rs/kWh (the order's own per-unit
energy charge on ex-bus/sent-out gen). Energy/fuel charge only. Arith check: Sl.20 Total
Cost of Fuel 96753.91 Lakh / Sl.3 Ex-bus gen 4932.43 MU = 1.9616 ≈ 1.96. (Sl.21
"Fuel Cost/unit" on gross gen = 1.79.) The order gives distinct 22-23 values (2.02/1.96/1.96
across the 3 years) → genuinely FY2022-23-specific, NOT a flat base. File:
`wberc_tp96_22-23.pdf` (downloaded; pdftotext OK). Southern (135 MW) 2.89 in same order is
NOT in the CSE dataset → skipped.

**Haldia — FOUND, Rs 2.55/kWh (FY2022-23 admitted).** Same WBERC TP-96/20-21 order:
para text "energy charge is admitted @ 245.0 p/kwh for 20-21 and 21-22 and **255.0 p/kwh
for 22-23**" + table "Admitted Power Purchase Cost from HEL" Sl.2 Energy Charge Rate
22-23 = 255 p/kWh = Rs 2.55/kWh. This is Haldia Energy Ltd's (HEL, CESC subsidiary, 2x300)
generating-station energy charge for the 7th control period; STU/SLDC/fixed/transmission
charges listed separately (Sl.4-7), so this is energy-only. Arith: Sl.3 Energy Charge
98507 Lakh / Sl.1 3863 MU = 2.55. File: `wberc_tp96_22-23.pdf`.

**D.P.L. — FOUND (H1 only), Rs 2.251/kWh (FY2022-23 Apr-Sep, MFCA actual).** From the
on-disk **WBSEDCL Power-Purchase Appendix A1 (MFCA)** (`wbpdcl_wbsedcl_appendixA1.txt`),
DPL(Unit-7) & DPL(Unit-8) statements headed "2022-23 (April 2022 to September 2022)":
U7 "Energy Charge with MFCA" = 216.79 p/kWh (Tariff-Order-2021-22 base 153.62 + avg MFCA
top-up 63.17); U8 = 228.06 p/kWh (base 159.56 + MFCA 68.50). Gen-weighted by scheduled
energy (U7 283.143 MU, U8 797.019 MU) = 225.11 p/kWh = **Rs 2.251/kWh**. Arith checks
pass exactly: U7 MFCA 1788.670Lakh*10/283.143 = 63.17; U8 5459.749Lakh*10/797.019 = 68.50.
Energy charge incl. fuel adjustment only (no fixed/capacity). CAVEAT (flagged in CSV):
covers **only H1 FY2022-23** because the FY2022-23 DPL tariff order was not yet issued —
so it is the 2021-22 base ECR + realized MFCA top-up for Apr-Sep 2022. Real & correct-vintage
for H1, but H1-only; human may prefer to hold for a full-year DPL true-up.

**Maithon Rb TPP — FOUND, Rs 2.74/kWh (FY2022-23 company-AR actual).** Maithon Power Ltd
(Tata 74 : DVC 26 JV) **23rd Annual Report 2022-23**, Directors'/Board Report
("Coal Management & Operations"), verbatim: "achieved the ever-highest PLF at **82.14% at
an average energy charge rate (ECR) of 2.74 Rs/Kwh**" (FY23). Energy/variable charge only
(CERC normative landed-fuel-cost ECR; Maithon is CERC cost-plus). Sanity cross-check: P&L
"Cost of Fuel Consumed" 1943.68 Cr / Generation 7555 MU(gross) = 2.57, / 7455 MU(sold-LT)
= 2.61 — the accounting fuel-inventory expense sits just below the billed normative ECR,
in-band. File: `mpl_annual_report_fy2022-23.pdf` (downloaded from tatapower.com). FLAG:
company annual report, not a regulatory order (but it is MPL's own audited ECR, correct
vintage). data.gov.in ~2.54 was 2021-23 vintage → superseded by this AR figure.

### Where I looked but did NOT use (Maithon)
- WBERC TP-104-DVC and TP-98 PDFs: downloaded but **scanned image PDFs** (0 extractable
  text; this .venv has no pdfplumber/OCR) → removed from staging, unused.
- on-disk PSPCL PSERC FY2022-23 order + JSERC DVC 2024 order + BERC discoms FY2023-24:
  grepped, **no Maithon/MPL ECR row** (Maithon is a separate CERC-regulated JV, absent from
  beneficiary-DISCOM power-purchase tables I had).
- CARE Ratings Maithon PR (Jun-2025): describes cost-plus structure, **no per-unit FY23 ECR**.
- → The company annual report was the cleanest primary FY2022-23 source for Maithon.

### Net result
4/4 target stations FOUND with real, FY2022-23-vintage, energy-charge-only figures and
arithmetic cross-checks. Coverage would rise 290 → 294 units on merge (Budge Budge 3 units,
Haldia 2, D.P.L. 2, Maithon Rb TPP 2 = +9 units), all currently on the modelled fallback.
Real values run ABOVE the flat-freight model (1.96 vs ~1.83; 2.55 vs ~2.0; 2.25 vs ~2.02;
2.74 vs ~1.79) — consistent with the project finding that the model compresses the freight
spread for distant/eastern plants.
Artefacts under `data/raw/sources/staging/`: `wberc_tp96_22-23.pdf`+`.txt`,
`mpl_annual_report_fy2022-23.pdf`+`.txt`, `care_maithon_2025.pdf`+`.txt`,
`wbpdcl_wbsedcl_appendixA1.*` (pre-existing), `wb_cluster.csv`.

## OD cluster (agent) — Odisha IPPs + OPGC + Vizag (2026-06-01)

Target: I.B.Valley (OPGC), Derang (JITPL), Kamalanga (GMR), Vizag TPP (Hinduja/HNPCL).
All 4 FOUND with real FY2022-23 energy/variable charge. Staging: `staging/od_cluster.csv`.

- **I.B.Valley — FOUND 1.611 (161.09 P/U).** OERC Order **Case 104/2021 dtd 24.03.2022**,
  "Generation Tariff of OPGC (Unit I & II) for FY 2022-23". Table-10 (Computation of Energy
  Charges, p.33) and Table-12 (Summary of Approved Generation Tariff, p.38): **OERC-approved
  Energy/Variable Charge = 161.09 Paisa/kWh** (OPGC proposed 177.89; Commission cut to
  161.09 on G-14 coal Rs1614.52/MT, GCV 3101). Approved tariff order (forward ARR
  determination), correct FY2022-23 vintage. `staging/oerc_opgc_tariff_FY2022-23.pdf` (+ .txt).
  *Disambiguation:* the dataset's "I.B.Valley" = OPGC **Stage-I Units 1&2 (2x210 subcritical)**.
  Order **C-96/2021** (`staging/oerc_opgc_C-96-2021.pdf`) is a DIFFERENT plant — **Units 3&4
  (2x660 supercritical, ECR 126.15 P/U indicative)** — EXCLUDED (supercritical + not the 2x210
  subcritical row). Kept the PDF for audit only.
- **Vizag TPP (HNPCL) — FOUND 3.02.** APERC **FPPCA Common Order O.P.Nos.57-68 of 2024**,
  Sec(ii) "Variable Costs for FY 2022-23" sub-sec (f) "Others - Private IPPs", **p.55-56**:
  HNPCL **actual Variable Cost 3.02 Rs/kWh** (Approved 2.76; Admissible VC = actual claim
  Rs1368.56 Cr, approved "as filed"). Same source/method as the APGENCO + NTPC-SR rows already
  in the table. Arithmetic: 1368.56 Cr x10 / 3.02 = 4531.7 MU ~= HNPCL FY2022-23 actual gen
  4532 MU (FPPCA availability table). On-disk `staging/apgenco_aperc_FPPCA_FY2022-23.pdf`.
  (aperc.gov.in itself was UNREACHABLE this session — port 443 timeout; used the on-disk PDF.
  CARE rating `staging/care_hnpcl_rating_2024.pdf` confirms cost-plus PPA, actual-fuel pass-
  through energy charge, but gives no number — not used.)
- **Kamalanga (GMR) — FOUND 1.20 — RESOLVES the held-out value.** Prior harvest "held out"
  ~1.20 as anomalously low. Re-sourced: BERC **NBPDCL & SBPDCL Tariff Order FY 2023-24**,
  **Table 5.17** "Power Purchase Cost for NBPDCL for FY 2022-23 **as computed by Commission**"
  (p.208-209) and **Table 5.18** (SBPDCL, p.211): GMR **Energy Cost = 1.20 Rs/kwh** — this is
  the labelled **Energy cost (Rs/kwh)** column, NOT a fixed-charge mislabel. Fixed cost is a
  separate column (1.18 Rs/MW = 141.13 Cr); Total tariff 3.53 Rs/kwh (excluded). Arithmetic:
  NBPDCL 79.70 Cr x10 / 664.15 MU = 1.200; SBPDCL 93.56 Cr x10 / 779.65 MU = 1.200 — both DISCOM
  tables agree. **The 1.20 is genuine** — GMR Kamalanga (3x350) is a deep-pithead Talcher/Angul
  IPP on cheap MCL coal; sub-1.3 is real here, not an error. `staging/berc_discoms_fy2023-24.pdf`.
- **Derang (JITPL) — FOUND 1.12 — RESOLVES the held-out value.** Same BERC Tables 5.17/5.18
  (FY2022-23 as computed by Commission): JITPL **Energy Cost = 1.12 Rs/kwh** (Energy-cost column).
  Fixed cost separate (2.01 Rs/MW = 210.81 Cr); Total 5.09 Rs/kwh (excluded). Arithmetic:
  NBPDCL 52.38 Cr x10 / 467.66 MU = 1.120; SBPDCL 61.49 Cr x10 / 548.99 MU = 1.120 — both agree.
  **The 1.12 is genuine** — JITPL Derang (2x600) is a deep-pithead Angul IPP on MCL coal.
  NB: the prior harvest's earlier BERC table (Table 4.21 for **FY 2021-22**) also showed 1.20/1.12
  for GMR/JITPL — same value two years running because pithead MCL coal cost is flat-low; that
  table was wrong-vintage (FY21-22), but Table 5.17/5.18 is the correct FY2022-23 one.

NOT-FOUND / NOTES: none skipped. oerc.gov.in reachable (used direct curl + pdftotext -layout);
aperc.gov.in unreachable (timeout) so Vizag used the pre-staged FPPCA PDF. The two sub-1.3 IPP
values are flagged in `od_cluster.csv` with full column-label + arithmetic proof so the human can
verify the "energy cost" column before merging.

## TS cluster (agent)

Target: 5 Telangana stations — Singareni TPP (SCCL captive 2x600), Bhadradri TPP (TSGenco
4x270), K_Gudem New (TSGenco Kothagudem KTPS subcritical), Kakatiya TPP Stage-I (1x500) &
Stage-II (1x600). Staging: `data/raw/sources/staging/ts_cluster.csv`. Source artifact:
`tserc_rst_fy2022-23_slideshare.html` (full-text HTML of the RST FY2022-23 order, scraped
from the slideshare mirror because the regulator host is unreachable — see below).

NETWORK: every Telangana regulator host is UNREACHABLE from this session — `tgerc.telangana.gov.in`
(IPv4 164.100.187.151) and `tserc.gov.in` both time out on TCP connect, and so does the DISCOM
site `tgsouthernpower.org`. Confirmed not a local-only block: the jina.ai reader proxy
(`r.jina.ai`, fetches from its own datacenter) also got `TimeoutError: Navigation timeout` on the
same URLs, and the Google Docs viewer returned only a JS shell. So no PDF could be downloaded.
WORKAROUND: the RST FY2022-23 order is mirrored full-text on slideshare
(`ramaiahkumar/telangana-tariff-retail-supply-tariff-rst-order-for-fy-202223pdf`), whose HTML
embeds the order's table text; saved it and grepped out Table 4-14 (TSGenco thermal) and Table
4-16 (medium-term sources, incl. SCCL STPP) verbatim.

VINTAGE VERDICT — all 5 are WRONG-VINTAGE (MYT base, not FY2022-23 actual), flagged as such:
- The RST FY2022-23 Tables 4-14/4-16 are the *approved test-year projection* (order dated
  23.03.2022). For TSGenco stations the variable cost is computed from the MYT-order-22.03.2022
  BASE ECR, which the order itself states is held flat across FY2019-20..FY2023-24 — i.e. the
  exact wrong-vintage case the prompt warns about (same numbers already in `tsgenco.csv`). For
  SCCL Singareni STPP, the order explicitly says the tariff "has been considered as per the Order
  dated 28.08.2020 on approval of generation tariff for STPP for the Control Period from FY2019-20
  to FY2023-24" — also a flat MYT base.
- A genuine FY2022-23-actual source DOES exist: TGERC "Order on true-up for FY 2022-23 and MYT
  (FY2024-25..2028-29)" dated 28.10.2024 — `.../2024/FY 24-25 TGGenco MYT.pdf`. It is ONLY on the
  unreachable tgerc host, with no slideshare/scribd mirror; direct curl, retry, and jina proxy all
  failed. This is the one document a future network-enabled session should pull to upgrade these
  5 rows to real FY2022-23 true-up actuals (and to get an SCCL STPP FY2022-23 true-up, if filed).

VERIFIED VALUES (arithmetic-checked, ECR = ApprovedVarCost_Cr*10 / ApprovedQuantum_MU):
- Bhadradri TPP            BTPS    7361.10 MU / 1739.60 cr -> 2.363 Rs/kWh (Table 4-14 p.127)
- Kakatiya TPP (Stage-I)   KTPP I  3192.75 MU /  969.13 cr -> 3.035 Rs/kWh (Table 4-14 p.127)
- Kakatiya TPP (Stage-II)  KTPP II 3910.46 MU / 1143.71 cr -> 2.925 Rs/kWh (Table 4-14 p.127)
- K_Gudem New (KTPS V+VI)  gen-wtd 6429.13 MU / 1736.32 cr -> 2.701 Rs/kWh (Table 4-14 p.127)
- Singareni TPP (SCCL STPP) STPP   9044.38 MU / 2120.91 cr -> 2.345 Rs/kWh (Table 4-16 p.130;
  the order also prints the per-unit rate "STPP 2.345" in its medium-term variable-rate sub-table)

MAPPING NOTE — K_Gudem New: dataset units are 250+250+500 MW (ages ~27/26/13) = Kothagudem KTPS
subcritical Stage V & VI. The existing `tsgenco.csv` mapped K_Gudem New -> KTPS-VII (1x800 MW,
ECR 2.409), but KTPS-VII is SUPERCRITICAL and would not appear in the CSE subcritical table — so
the correct subcritical mapping is KTPS V/VI (gen-wtd 2.701), not KTPS-VII. Flagged in the CSV.

SINGARENI is NOT a TSGenco station: it's SCCL captive, bought by the DISCOMs as a medium-term
source (Table 4-16), distinct from NTPC's "Telangana STPP / TSTPP" (2x800 MW supercritical,
Ramagundam) which also appears in the same order — do not conflate the two.

NOT-FOUND: no FY2022-23-ACTUAL (true-up/FPPCA) ECR found for any of the 5 — the only such order
(TGGenco true-up 28.10.2024) is on the unreachable host. All 5 rows are MYT-base / wrong-vintage,
flagged, suitable as a cross-check only (consistent with how `tsgenco.csv` already holds them).

## CG-IPP cluster (agent)

Target = 10 Chhattisgarh / CG-adjacent private IPP dataset stations. **RESULT: 0 verified
FY2022-23 per-station ECR rows.** All 10 are merchant / short-term / captive sellers whose
FY2022-23 energy charge is not published per-station in any reachable regulator order. Staging
CSV `data/raw/sources/staging/cg_ipp_cluster.csv` therefore carries header + not-found note only.

Per-station verdicts (match_name -> status, where looked):

- **Tamnar TPP** (O.P. Jindal / JPL 2400 MW Tamnar-II) -> NOT-FOUND. JPL sells ~870 MW long-term
  to KSEB(Kerala)/TANGEDCO(TN)/CSPDCL, "majority under short-term PPAs/exchanges" (CARE/Powerline).
  Checked: TANGEDCO TNERC true-up (on disk) IPP list = TAQA/LANCO-Aban/PIONEER-Penna only, no
  Jindal, and trues up only to FY2020-21 (wrong vintage). UPERC/PSPCL/GUVNL tables: no Jindal.
  CSERC FY2023-24 concessional table lists "M/s Jindal Power Ltd. 1.54" but that is FY2021-22
  + a concessional blended rate, not a FY2022-23 ECR -> excluded.
- **Raigarh TPP(OP Jindal Tps)** (dataset attributes to JSW Energy = JSW bought JPL's 1000 MW
  Raigarh in 2021) -> NOT-FOUND. No per-station FY2022-23 energy charge in any reachable order
  (JSW Raigarh is largely merchant/short-term). Not in UPERC/PSPCL/GUVNL/TNERC/CSERC rate tables.
- **Baradarha TPP** (DB Power 2x600) -> NOT-FOUND. DB Power had ~923 MW long/medium-term PPAs
  (GEM). Checked: GERC DGVCL FY2022-23 order (downloaded, 13.6k lines) station-wise GUVNL
  power-purchase table p.153-154 -> DB Power NOT listed (GUVNL IPPs = GSEG/GIPCL/GMDC/GPPC/Essar/
  Adani/ACB-India/CGPL). BERC discom table (on disk) has DB Power rows but all blank/zero
  (no Bihar drawal). CSERC FY2023-24 concessional table "M/s DB Power Ltd. 3.23" = FY2021-22
  concessional blended -> wrong vintage, excluded.
- **Pathadi Tps Ph -I** (Lanco Amarkantak 2x300, Korba) -> NOT-FOUND (clean ECR). Unit-1 -> MPERC
  (true-up Petition 64/2023, order 03.03.2023 exists) but MPERC gen-tariff is a normative
  SHR/coal-cost computation, not a published FY2022-23 actual ECR figure I could read; Unit-2 ->
  Haryana (HERC FY2022-23 true-up O20240305a(1).pdf) which was UNREACHABLE this session
  (herc.gov.in curl 000 / WebFetch timeout). CSERC concessional "M/s Lanco Amarkantak 1.97" =
  FY2021-22 concessional -> excluded. Re-source from MP DISCOM (MPPMCL) power-purchase true-up
  or HERC station-wise table in a network session that can reach herc.gov.in / mperc.in.
- **Balco TPP** (BALCO/Vedanta captive 2x300, Korba) -> NOT-FOUND. Captive; only on-disk figure
  is CSERC FY2023-24 concessional "M/s Balco 1.77" (FY2021-22, concessional) -> excluded.
- **Avantha Bhandar TPP** (= Korba West Power Co Ltd / REGL, private 600 MW; NOT CSPGCL's 500 MW
  Korba West KWTPP) -> NOT-FOUND. Care taken not to mis-assign CSPGCL KWTPP ECR 1.306 to this
  private station. Only on-disk figure: CSERC concessional "M/s Korba West Power Company Ltd.
  (REGL) 1.60" (FY2021-22, flat concessional) -> excluded.
- **Binjkote** (SKS Power Generation 2x300) -> NOT-FOUND. Merchant/insolvency-resolved. CSERC
  concessional "M/s S K S Power Generation Ltd. 1.60" (FY2021-22, flat) -> excluded.
- **Bandakhar TPP** (Maruti Clean Coal & Power 300 MW) -> NOT-FOUND. CSERC concessional
  "M/s Maruti Clean Coal & Power Ltd. 1.60" (FY2021-22, flat) -> excluded.
- **Kasaipalli** (ACB India 270 MW) -> NOT-FOUND. CSERC concessional "M/s ACB (India) Ltd.
  (270 MW) 1.60" (FY2021-22, flat concessional) -> excluded. (The "ACB India Ltd. 0.75" row in
  the GERC DGVCL table is a Gujarat lignite source, not this CG plant.)
- **Mahadev Prasad STPP** (Adhunik Power 540 MW; located Jharkhand/Padampur, NOT CG) -> NOT-FOUND.
  ~60% PPA coverage, partly merchant; no per-station FY2022-23 ECR in reachable JERC/MP orders.

Sources searched (this session): on-disk staging txt (CSERC FY2023-24 & FY2024-25, UPERC discom,
PSPCL FY2022-23, BERC discom, TANGEDCO TNERC, MPPGCL, TSGenco, NLC, DVC, GSECL); downloaded fresh
GERC DGVCL FY2022-23 order; WebSearch for each plant's PPA off-taker + regulator order. CSERC
FY2024-25 order trues up FY2022-23 but reports concessional power only as an aggregate
(2,351.96 MU @ Rs2.87/kWh), NOT station-wise. herc.gov.in and cserc.gov.in are unreachable from
this session's Bash (curl 000); HERC PDF too slow for WebFetch.

Vintage/honesty note: CSERC's "Concessional Power through CSPTrdCL" rows are the obvious temptation
but are disqualified twice over - FY2021-22 vintage AND mostly a flat Rs1.60/kWh contracted
concessional rate (the order even states uncovered generators are billed a flat Rs1.60/kWh), i.e.
not a plant-specific energy/variable charge. Left for the model fallback (`02`) rather than faked.

## Fourth-wave VERIFICATION AUDIT (2026-06-02, post-merge critical review)

Independent re-verification of all 9 fourth-wave rows against their cited source text
(operator, not harvest agent). Every row passed; no value or mapping changed.

- **Matching integrity (06).** All 9 ECR rows fuzzy-match to the correct plant/company
  and no others. Specifically checked the only real collision risk: the dataset has TWO
  Haldia plants — `Haldia` (Haldia Energy Ltd, CESC supplier) and
  `India Power TPP (Haldia, Hiranmaye)` (Hiranmaye Energy Ltd). The 2.55 row maps ONLY to
  HEL `Haldia` (exact norm key "haldia"); the Hiranmaye plant correctly stays modelled
  (₹2.27/2.21). Verified `Korba Stps` (NTPC, 1.612, MahaSLDC) and `Korba-V(Dspm Tps)`
  (CSPGCL DSPM, 1.612, CSERC true-up) showing the identical 1.612 is a COINCIDENCE, not a
  mis-match — distinct norm keys ("korba" vs "korba v dspm"), two independent sources, both
  Korba-coalfield pithead so genuinely similar.
- **Vizag/HNPCL 3.02 (APERC FPPCA, line 2316).** Table shows HNPCL approved per-unit VC 2.76
  vs ACTUAL 3.02 (9% higher), actual claim ₹1368.56 Cr admitted as filed. Using the actual
  (3.02), correct for a "real FY2022-23 actual ECR" basis. Arithmetic: 1368.56×10/3.02 =
  4532 MU = HNPCL FY2022-23 actual gen. Energy-only; fixed ₹1234.67 Cr is a separate arrears
  line (excluded).
- **Kamalanga 1.20 / Derang 1.12 (BERC, lines 5017-5018).** Component breakout confirms 1.20/1.12
  is the ENERGY column (GMR: fixed 1.34 + energy 1.20 ... total 3.39; JITPL: fixed 2.03 +
  energy 1.12 ... total 3.34; cost split 160.01+104.87+31.06 = 295.94 reconciles). NOT a
  mis-read total. Independently validated physically: heat-rate × MCL G14 price (≈₹1.61/kg)
  gives ≈1.24 (Kamalanga) / ≈1.12 (Derang) — matches. Sub-1.3 but real (deep-pithead Angul MCL).
- **Budge Budge 1.96 / Haldia 2.55 (WBERC TP-96).** Both use Commission-ADMITTED, not proposed,
  figures. Budge Budge: admitted fuel cost 96753.91 Lakh (line 2271) / ex-bus gen 4932.43 MU
  (line 2237) = 1.9616. Haldia: HEL admitted availability 3863 MU (line 990); the earlier
  2.80 figure was a projection column, 2.55 is admitted.
- **DPL 2.251** remains the weakest row (H1-only, 2021-22 base + realized MFCA; flagged), and
  **Maithon 2.74** a flagged secondary (company AR; ~5% above its own fuel-cost/gen sanity 2.57-2.61).
  Both low-impact (2 units each), kept with explicit caveats per the secondary/partial-year precedent.

Headline figures in REPORT/CLAUDE/README re-checked against `outputs/06_apply_ecr.txt`.
No stale 62.9%/69.6% headline figures remain (only correct historical wave-transition markers).

## FULL 86-ROW VERIFICATION AUDIT (2026-06-02) — every row vs primary source

Re-verified ALL 86 ECR rows against their cited primary source: 7 parallel agents by genco-cluster
(MahaGenco/MahaSLDC, RRVUNL/HPGCL, GSECL/TANGEDCO/PSPCL, DVC/WBPDCL/CSPGCL, UPRVUNL/APGENCO/NLC,
NTPC-central, UPERC-IPP/Jhajjar) + the 9 fourth-wave rows + operator adjudication of every flag.
**Result: 86/86 values correctly extracted, correct energy-charge component, FY2022-23 vintage, 0 fabricated.**

Two agent-raised flags were adjudicated and found to be FALSE ALARMS:
- **DVC Mejia 3.649** — correct. The merged ECR (Mejia + Mejia-Ext, both _norm "mejia") is the
  generation-weighted average by the *dataset's* per-unit generation: (3.715·7495.6 + 3.577·6867.3)/14362.9
  = 3.6491. The agent recomputed with the source order's implied MU (→3.683); the dataset-generation
  weighting is the right basis for the counterfactual and reproduces 3.649 exactly.
- **WBPDCL Bandel 217.09 (base)** — real. The committed source `.txt` was a corrupt EMBEDDED-OCR layer in
  which 217.09 was mangled. Fresh tesseract re-OCR of all 150 pages confirms the BTPS-V block on p.24:
  `49.78 217.09 266.87` (MFCA / base / with-MFCA). The clean OCR now REPLACES the corrupt committed
  `wbpdcl_wbsedcl_appendixA1.txt`. The dataset's Bandel = Unit-V (210 MW / 1407 GWh ≈ 117 MU/month), so
  217.09 (not the small costly Unit-I 271.80) is the right unit.

ONE REAL FINDING & FIX (user-approved):
- The WBPDCL source publishes three columns — **MFCA adjustment (A) | base tariff-order ECR (B) |
  Energy Charge with MFCA (C=A+B)**. Earlier waves harvested col B (base, EXCLUDING the fuel adjustment).
  In the FY2022-23 coal-price spike that understated the 5 WBPDCL plants ~13–25% vs their actual cost,
  and was inconsistent with the actual-basis rows (CSPGCL actual coal+oil, DVC true-up, APERC actual VC).
  Switched all 5 to the ACTUAL col C ('Energy Charge with MFCA'), arithmetic col-A+col-B=col-C verified:
  | plant | MFCA(A) | base(B) | with-MFCA(C)=ECR used |
  | Kolaghat   | 66.04 | 278.41 | 344.45 → 3.4445 |
  | Bakreswar  | 45.50 | 182.90 | 228.40 → 2.2840 |
  | Santaldih  | 49.17 | 194.97 | 244.14 → 2.4414 |
  | Bandel-V   | 49.78 | 217.09 | 266.87 → 2.6687 |
  | Sagardighi | 23.95 | 179.11 | 203.06 → 2.0306 |
  Caveat: the MFCA leg is the Apr–Sep FY22-23 average (the debit-note bundle covers H1). Headline after
  fix: Actual 208,240 / Cost-merit 180,035 / Carbon-merit 215,139 cr; as-run +15.7%; gap +43.7 MT / ₹35,104 cr.
  Residual basis heterogeneity remains (already caveated in REPORT §7b): GSECL/TANGEDCO/UPERC-APR rows are
  approved-base where actuals aren't separately published; WBPDCL now joins the actual-basis subset because
  its source uniquely publishes both.

## 2026-06-02 COVERAGE-PUSH SESSION — local sync done, network harvest BLOCKED

Attempted the documented next-step harvests. Outcome split cleanly:

**DONE (local, no network needed):**
- **Rich table synced** (`plant_tariff_details.csv`, 72→81 rows): added the 9 fourth-wave stations
  (Budge Budge, Haldia, D.P.L., Maithon, Bhavnagar, I.B.Valley, Vizag, Kamalanga, Derang) with their
  verified structured extras (gen MU, capacity, SHR/aux/transit for Bhavnagar, GCV/landed/grade for
  I.B.Valley, fixed-charge for Kamalanga/Derang, etc.), and updated the 7 WBPDCL rows to the actual
  with-MFCA basis (col C = base + MFCA) matching the plant_ecr.csv audit fix. The rich table does NOT
  feed `06`, so no counterfactual change.
- **WBPDCL deeper unit-split** check: no new coverage available — all 5 WB dataset stations are already
  covered; Sagardighi Stage-I (2.0306) vs Stage-II (2.0314) are within 0.001, immaterial.

**BLOCKED (need a network-enabled LOCAL session) — nothing added, per honesty rule:**
- Network probe: state SERC sites all return curl `000` (tgerc.telangana.gov.in, herc.gov.in,
  cserc.gov.in, aerc.gov.in, mperc.in) even with `--insecure`+browser-UA; central sites OK. Server-side
  WebSearch works but WebFetch TIMES OUT on the large scanned SERC PDFs, and a background harvest agent
  died with an API ConnectionRefused. So no source could be downloaded+verified here.
- **Telangana TGGENCO** (highest-value, ~5 subcritical stations / ~19,600 GWh): located the FY2022-23
  true-up order URL (tgerc.telangana.gov.in .../2024/FY 24-25 TGGenco MYT.pdf) — recorded in
  docs/SCRAPE_ECR_PROMPT.md for a future local session. NOT harvested (couldn't download/verify).
- **CG IPPs / KPCL / NLC expansions / Assam Bongaigaon / MPPGCL / basis-upgrades (HPGCL/UPRVUNL/
  Jhajjar/DPL/Maithon approved orders):** all need the blocked state-SERC sites, or are confirmed
  no-public-ECR / wrong-vintage. Honest skips; precise leads in SCRAPE_ECR_PROMPT.md.

**Net:** coverage stays 306/455 = 67.3% (74.9% of gen) — this is the practical ceiling reachable from
this (cloud/Drive-synced) environment. Pushing past it requires the LOCAL-network session described in
docs/SCRAPE_ECR_PROMPT.md. No fabricated rows added.
