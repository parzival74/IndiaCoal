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
