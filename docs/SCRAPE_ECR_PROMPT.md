# Kickoff prompt — fetch REAL FY2022-23 per-station ECR (run in a LOCAL session)

Copy everything in the block below into a fresh Claude Code session **on a machine with
network access** (a local clone, not the cloud sandbox — the cloud environment is
network-restricted, which is the only reason this data is still outstanding).

---

## Mission
Continue the **IndiaCoal** analysis. Fill `data/raw/plant_ecr.csv` with **REAL, FY2022-23,
per-station Energy Charge Rate** (ECR / variable charge, ₹/kWh) for the ~124 state/private +
uncovered-central coal stations that currently have **no metered cost**. Every number must
be traceable to a published source. When you're done, `analysis/06_apply_ecr.py` ingests the
file, overrides the modelled cost, and re-runs the merit-order counterfactual on real data.

## Read first (in this order)
1. `CLAUDE.md` — project memory; the headline question and what's already done.
2. `REPORT.md` §6–§11 — variable cost, the CERC/data.gov.in real-ECR cross-checks, and the
   §11 all-fleet reconstruction this replaces with metered data.
3. `docs/data_sources.md` #1 — the ranked source list (SERC orders, SLDC stacks, MERIT…).
4. `analysis/06_apply_ecr.py` and `data/raw/plant_ecr_template.csv` — the ingestor + format.

## Output contract — the ONLY deliverable that matters
Append rows to **`data/raw/plant_ecr.csv`** with exactly these columns:

```
match_name,ecr_rs_per_kwh,period,source
```

Rules (non-negotiable — this project values honesty over coverage):
- `ecr_rs_per_kwh` = **energy/variable charge ONLY** (₹/kWh). NOT fixed/capacity charge.
  Convert **paise/unit → ₹/kWh** (÷100) where the source is in paise. Sanity range for coal
  is ~₹1.3–4.5/kWh — flag and re-check anything outside it.
- `period` **MUST be FY2022-23.** Multi-year (MYT) orders span e.g. 2019-24 — open the order
  and take the **FY2022-23 / FY23 column specifically**. A wrong-vintage number silently
  breaks the comparison (this is exactly why the CERC data stayed a 2018-basis cross-check).
- `source` = a **precise, verifiable citation**: document title + date + table/page, e.g.
  `"MERC Case 217/2022 MahaGenco MYT Order, 31-Mar-2023, Table 7.x, p.142"`.
- One row per station. `match_name` = the station name (fuzzy-matched; suffixes/punct ignored).
- **NEVER invent, interpolate, or guess a number.** If a station's FY2022-23 ECR isn't in a
  public order, **skip it** — leave it out. Partial real coverage beats fabricated coverage.
- Save every raw artefact you used (PDF/JSON/HTML) under `data/raw/sources/` for audit, and
  keep a running log in `docs/ecr_scrape_notes.md`: found / not-found / ambiguous, with reasons.

## Step 1 — generate your exact worklist from the repo
```bash
python3 - <<'PY'
import pandas as pd
rec = pd.read_csv("data/plant_cost_reconstructed.csv")
df  = pd.read_csv("data/cse_subcritical_clean.csv")
need = rec[rec.vc_source.isin(["reconstructed_landed","modelled_anchor"])].name.unique()
d = df[df.name.isin(need)]
print(d.groupby(["sector","company"])
        .agg(stations=("name","nunique"), GW=("capacity_mw", lambda s: round(s.sum()/1000,2)))
        .sort_values("GW", ascending=False).to_string())
# full station list to fill:
for c, sub in d.groupby("company"):
    print("\n#", c, "->", sorted(sub.name.unique()))
PY
```
~124 stations / ~96 GW. Work **company-by-company** — one SERC order usually covers a whole genco.

## Step 2 — where to look (priority order: top ~10 gencos ≈ 90% of the gap)

| # | Genco (sector) | ~GW | State | SLDC (Route B) | SERC tariff orders (Route A) |
|---|---|---|---|---|---|
| 1 | MAHAGENCO (State) | 7.6 | Maharashtra | mahasldc.in | merc.gov.in |
| 2 | UPRVUNL (State) | 5.1 | Uttar Pradesh | upsldc.org | uperc.org |
| 3 | RRVUNL (State) | 4.7 | Rajasthan | energy.rajasthan.gov.in (SLDC) | rerc.rajasthan.gov.in |
| 4 | TANGEDCO/TNEB | 4.3 | Tamil Nadu | tnsldc.in | tnerc.gov.in |
| 5 | WBPDCL | 4.2 | West Bengal | wbsldc.in | wberc.gov.in |
| 6 | GSECL | 3.9 | Gujarat | Gujarat SLDC (GETCO) | gercin.org |
| 7 | APGENCO | 3.4 | Andhra Pradesh | core.ap.gov.in / apsldc | aperc.gov.in |
| 8 | TSGENCO | 3.2 | Telangana | tssldc | tserc.gov.in |
| 9 | KPCL | 2.7 | Karnataka | kptclsldc.in (KSLDC) | kerc.karnataka.gov.in |
| 10 | HPGCL | 2.5 | Haryana | hvpnl SLDC | herc.gov.in |

Then marginal returns: MPPGCL→mperc.in, CSPGCL→cserc.gov.in, PSPCL→pserc.gov.in, etc.

**Two routes (use both; prefer A for breadth):**
- **Route A — SERC tariff/true-up orders** → approved **per-station energy charge, FY2022-23**.
  One PDF per genco, authoritative, vintage-clean (same basis as the CERC central cross-check).
  Search the SERC site for `"<genco> tariff order 2022-23"` or `"true-up FY23"`.
- **Route B — SLDC daily Merit-Order-Despatch (MOD) stacks** → the **actual metered dispatched
  ₹/kWh**. Daily PDFs: sample several representative days across FY2022-23, average, and record
  the method in `source`. This is the metered gold standard but more work.
- **MERIT portal `meritindia.in`** — per-state Variable Charge (₹/unit), served via background
  JSON. Inspect the **XHR calls in DevTools → Network** and hit the API endpoint rather than
  scraping the map. `npp.gov.in` (merit chart) and `vidyutpravah.in` mirror it.
- **Private plants** (JSW, JSPL/Jindal, KSK Mahanadi, RKM Powergen, Indiabulls, Adani): PPAs are
  often confidential, but the units appear in the **host-state SLDC MOD** and as a procured
  source in **that state's SERC order**; pure merchant volume clears on IEX (`iexindia.com`).

## Step 3 — tooling & etiquette
Install as needed: `requests beautifulsoup4 lxml pdfplumber pypdfium2`; for the JS MERIT portal,
`playwright` (then `playwright install chromium`). Respect `robots.txt`, send a descriptive
User-Agent, rate-limit (≥1–2 s between requests), and retry with exponential backoff. Don't
hammer government sites.

## Step 4 — method per genco
1. Locate the FY2022-23 tariff/true-up order PDF on the SERC site; download to `data/raw/sources/`.
2. Parse with `pdfplumber`; find the per-station **energy charge** table; pick the **FY2022-23** column.
3. Extract `station → ECR (₹/kWh)`; convert paise→₹ if needed; sanity-check the magnitude.
4. Append rows to `data/raw/plant_ecr.csv` with the precise citation.
5. Log found / not-found / ambiguous in `docs/ecr_scrape_notes.md`.

## Step 5 — verify & finish
```bash
python3 analysis/06_apply_ecr.py     # reports real-vs-modelled coverage + re-runs counterfactual
```
- Read its diagnostics: confirm coverage rose and **matched names are correct** — fix any
  `match_name` spelling that mis-matched or failed to match (cutoff is strict by design).
- `python3 analysis/run_all.py` should stay deterministic (no stray diffs).
- Update `REPORT.md` §7 coverage and the `CLAUDE.md` status block with the new real coverage %.
- Commit to branch **`claude/keen-newton-P0cFA`** with a clear message; `git push -u origin
  claude/keen-newton-P0cFA`. **Do NOT open a PR unless explicitly asked.**
- Do NOT put any model identifier in committed artefacts.

## Definition of done
`data/raw/plant_ecr.csv` holds **real FY2022-23 ECR** for as many of the 124 target stations as
genuinely exist in public orders (top-10 gencos first), each with a **verifiable citation**;
`06_apply_ecr.py` shows the coverage jump and the counterfactual on metered cost; report +
status updated; pushed to the working branch. No fabricated rows. No wrong-vintage rows.

---

*Provenance discipline mirrors the rest of the repo: `vc_source` / coverage reports label real
vs modelled everywhere, and scaffolds stay inert until real data backs them. Keep it that way.*
