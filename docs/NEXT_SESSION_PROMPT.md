# Startup prompt for the next session

Paste the block below when opening a new (Full network access) session. The domestic
coal price is already grounded on real CIL FY2022-23 notified prices; this prompt is
for the REMAINING task — fetching FY2022-23 *metered* per-station ECR once those feeds
(Grid-India SCED / POSOCO / SLDC / MERIT) are reachable again. See `CLAUDE.md` for full
project context and `docs/data_sources.md` for the resume checklist.

---

```
We're continuing the IndiaCoal analysis. Start by reading CLAUDE.md, REPORT.md,
and docs/data_sources.md — they carry the full context from previous sessions
(I have none of that chat history here, so rely on those files). Don't open new PRs.

ALREADY DONE (2026-06 Full-access session): domestic coal is now priced on REAL CIL
FY2022-23 grade-wise pithead notified prices (data/raw/cil_grade_prices_fy2022-23.csv,
fetched from cercind.gov.in's CPI archive) + statutory levies + a flagged flat
freight, in analysis/02_variable_cost.py. CERC per-station ECR for 14 central stations
was parsed into data/raw/plant_ecr_cerc_2018basis.csv but it's a 2018-19 basis
(working-capital ECR on Oct-Dec 2018 coal cost), so it's a LABELLED CROSS-CHECK
(analysis/08_cerc_crosscheck.py), NOT the FY2022-23 headline.

THE REMAINING TASK: the genuinely FY2022-23 METERED per-station ECR feeds were all
DOWN last session (Grid-India SCED, POSOCO eLibrary, state SLDC stacks, MERIT/NPP
returned HTTP 503/refused). When they're back up, fetch them to fill
data/raw/plant_ecr.csv (FY2022-23 only) and raise 06's coverage above 0%.

Do this in order:

1. Confirm the FY2022-23 feeds are actually reachable in THIS session:
   for u in https://grid-india.in https://hrd.posoco.in/elibrary https://meritindia.in; do
     curl -s -o /dev/null -w "$u %{http_code}\n" -A "Mozilla/5.0" "$u"; done
   If they're still 503, stop and tell me — there's nothing new to fetch and the
   headline already rests on the real CIL prices. (cercind.gov.in / coal.gov.in were
   200 last session; analysis/07_fetch_ecr.py probes all of these.)

   VINTAGE RULE: only FY2022-23 ECR goes into plant_ecr.csv. Do NOT paste the CERC
   2018-basis ECR there — it lives in plant_ecr_cerc_2018basis.csv for the 08 cross-check.

2. Work the FY2022-23 metered sources (full detail in docs/data_sources.md):
   a. Grid-India SCED statements / RLDC reports — per-generator variable cost, ISGS.
   b. State SLDC daily merit-order stacks — most granular per-station Rs/kWh, ~30 sites.
   c. MERIT (meritindia.in) — interactive map; inspect its background XHR/JSON, don't
      scrape HTML; flaky, last resort.

3. Implement the SCED/SLDC/MERIT parser in analysis/07_fetch_ecr.py against the REAL
   responses. Critical rule: never fabricate ECR — if a source fails or a field is
   ambiguous, leave it out and say so. Keep a `source` citation per row. It writes
   data/raw/plant_ecr.csv (schema: match_name, ecr_rs_per_kwh, period, source).

4. Run python3 analysis/06_apply_ecr.py. Check coverage % and the fuzzy-match
   diagnostics — manually verify station-name matches (difflib already mis-hit
   "Bhadradri" for Dadri once; prefer explicit aliases for the big stations).

5. Re-run python3 analysis/run_all.py, then update REPORT.md §7 and the extensions
   table with the REAL FY2022-23 coverage and the new counterfactual on the blended
   cost. State clearly what fraction is real metered ECR vs the CIL-grounded model.

6. Commit with clear messages and push to the working branch. Show me the coverage
   achieved and any stations you couldn't source.

Caveats: some gov portals have anti-bot/WAF protection even with network access;
the dataset is subcritical-only and FY2022-23 vintage; honest real-data coverage,
not 100% at the cost of made-up numbers.
```

---

## Notes
- **Partial coverage is an acceptable outcome.** Coal-India grade prices already
  backstop the whole domestic fleet (real, FY2022-23). SCED would add interstate
  stations, SLDC stacks the state gencos. `06_apply_ecr.py` states the real-vs-model
  split explicitly; the `vc_source` column tags every unit `published_ECR`/`modelled`.
- **CERC is the wrong vintage for the headline** — it's a 2018-19-basis working-capital
  ECR. Already captured as the `08` cross-check; don't re-add it to `plant_ecr.csv`.
- **MERIT is last resort, not the plan.** Interactive map, flaky XHR-loaded data.
- **Verify fuzzy matches.** The matcher uses `difflib` (0.82 cutoff); it mis-hit
  "Bhadradri" for Dadri once — prefer explicit aliases for the big central stations.
