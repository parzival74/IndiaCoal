# Startup prompt for the next session

Paste the block below when opening a new (Full network access) session on branch
`claude/keen-newton-P0cFA`. It tells the session to fetch real plant-level ECR
and run it through the existing pipeline. See `CLAUDE.md` for full project context
and `docs/data_sources.md` for the resume checklist.

---

```
We're continuing the IndiaCoal analysis. Start by reading CLAUDE.md, REPORT.md,
and docs/data_sources.md — they carry the full context from previous sessions
(I have none of that chat history here, so rely on those files). Work stays on
branch claude/keen-newton-P0cFA (PR #1); don't push elsewhere or open new PRs.

The task: replace the MODELLED variable cost in analysis/02_variable_cost.py with
REAL published plant-level Energy Charge Rate (ECR), now that this environment
has Full network access.

Do this in order:

1. First confirm network access actually works in THIS session:
   curl -s -o /dev/null -w '%{http_code}\n' https://cercind.gov.in
   Expect 200. If it returns 403, stop and tell me — it means this session isn't
   running on the Full-access environment, and I need to fix the environment
   selection rather than have you keep trying.

   VINTAGE RULE: the performance data is FY2022-23, so collect FY2022-23 ECR only.
   Do not use current-year prices (coal prices swung hugely; mixing vintages would
   break the cost-vs-PLF comparison).

2. Work the sources in this priority order (full detail in docs/data_sources.md #1):
   a. CERC FY2022-23 tariff orders (cercind.gov.in) — authoritative regulated ECR
      for central/ISGS stations (NTPC, DVC, NLC); per-petition PDFs.
   b. Grid-India FY2022-23 SCED statements / RLDC reports (grid-india.in,
      hrd.posoco.in/elibrary) — per-generator variable cost for interstate stations.
   c. State SLDC daily merit-order stacks — most granular per-station Rs/kWh, but
      ~30 heterogeneous sites; covers state gencos.
   d. Coal India 2022-23 grade-wise notified prices (coal.gov.in) × plant SHR —
      universal fallback so every unit gets a period-correct number.
   Do NOT rely on MERIT (meritindia.in): it's an interactive map (data via background
   XHR, flaky/semi-defunct) — last resort only, and inspect its XHR endpoint rather
   than scraping HTML. Wayback is not used (it didn't capture MERIT's dynamic data).

3. Implement the parser TODOs in analysis/07_fetch_ecr.py against the REAL
   responses. Critical rule: never fabricate ECR values — if a source fails or a
   field is ambiguous, leave it out and say so. Keep a `source` citation per row.
   Run it to write data/raw/plant_ecr.csv (schema: match_name, ecr_rs_per_kwh,
   period, source).

4. Run python3 analysis/06_apply_ecr.py. Check the coverage % and the fuzzy-match
   diagnostics — manually verify a handful of station name matches are correct
   (the matcher uses difflib; watch for wrong matches on similar names).

5. Re-run the full pipeline (python3 analysis/run_all.py), then update REPORT.md
   section 7 and the extensions table with the REAL coverage and the new
   cost-vs-carbon counterfactual numbers on the blended cost. Note clearly what
   fraction is real ECR vs still modelled.

6. Commit with clear messages and push to claude/keen-newton-P0cFA (PR #1).
   Show me the coverage achieved and any stations you couldn't source.

Caveats to keep in mind: some gov portals have anti-bot/WAF protection even with
network access (you may hit blocks needing different headers or a manual fetch);
the dataset is subcritical-only and 2022-23 vintage; and the goal is honest
real-data coverage, not 100% at the cost of made-up numbers.
```

---

## Notes
- **Partial coverage is an acceptable outcome.** CERC + SCED cover the central/
  ISGS stations (the high-PLF ones); SLDC stacks add state gencos; Coal-India
  grade prices backstop everything else. The `06_apply_ecr.py` coverage report
  states the real-vs-modelled split explicitly, and the `vc_source` column in
  `data/plant_cost_blended.csv` tags every unit as `published_ECR` or `modelled`.
- **MERIT is last resort, not the plan.** It's an interactive map with flaky,
  dynamically-loaded data; lead with the dated CERC/SCED/SLDC/Coal-India sources.
- **Verify fuzzy matches.** The name matcher uses `difflib` with a 0.82 cutoff;
  eyeball the diagnostics table for wrong matches on similarly-named stations.
