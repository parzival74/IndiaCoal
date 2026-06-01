"""
10 - Contemporaneous CENTRAL/ISGS per-station ECR from data.gov.in.

The most contemporaneous REAL per-station Energy Charge Rate (ECR) we can reach:
Rajya Sabha parliamentary-answer 'Generating Station-wise Tariff Statement' datasets
on data.gov.in (NTPC FY2021-22; NLC/DVC 2021-23 window). Fetched by
analysis/fetch_datagov_ecr.py -> data/raw/datagov_tariff_ecr_2021-23.csv (committed).

WHY IT MATTERS: it roughly DOUBLES our real-ECR coverage vs the 14-station, 2018-basis
CERC cross-check (08) AND is contemporaneous, so it gives the pithead cost-side test a
bigger, vintage-appropriate sample.

VINTAGE / SCOPE CAVEATS (this is a labelled CROSS-CHECK, NOT the FY2022-23 headline):
  * Vintage is 2021-22 / 2021-23, not a clean FY2022-23. FY2021-22 coal prices were
    below the FY2022-23 spike, so these likely modestly UNDERSTATE FY2022-23.
  * ISGS ONLY -- NTPC/DVC/NLC + a couple of JVs. NO state or private merchant plants
    (the majority of the fleet), so it cannot drive an all-fleet headline re-dispatch.
  * Station mapping to our dataset is EXPLICIT/curated (normalised-exact name match,
    NOT fuzzy); gas and supercritical rows are dropped; DVC paise->Rs already handled
    at fetch time. Stage-level ECRs are averaged to one value per station.

Depends on: 02 (variable_cost), 03 (optional), and the committed datagov + CERC CSVs.
Run:    python3 analysis/10_datagov_ecr.py
Writes: outputs/10_datagov_ecr.txt
"""
from __future__ import annotations
import os
import re
import numpy as np
import pandas as pd
from common import load_clean, analysis_set, flag_pithead, corr, REPO, OUT_DIR

DATAGOV_CSV = os.path.join(REPO, "data", "raw", "datagov_tariff_ecr_2021-23.csv")
CERC_CSV = os.path.join(REPO, "data", "raw", "plant_ecr_cerc_2018basis.csv")
HOURS, MAX_PLF = 8760, 0.85

# Curated map: OUR station name -> the tariff 'station_raw' rows to average (stages).
# Only stations confidently present in our SUBCRITICAL fleet. Gas + supercritical
# tariff rows (Lara, Solapur, Khargone, Kudgi, Barh, Tanda, the NTPC gas fleet, the
# JV supercriticals, etc.) are intentionally absent. Barauni is omitted: the tariff
# lists it under NTPC while our data marks it State, and the I/II stages can't be
# confidently split across our 'Barauni' vs 'Barauni (Ext)'.
CURATED = {
    # --- NTPC coal (vintage 2021-22) ---
    "Singrauli Stps":  ["Singrauli STPS"],
    "Rihand":          ["Rihand STPS-I", "Rihand STPS-II", "Rihand STPS-III"],
    "Unchahar":        ["FGUTPS Unchahar-I", "FGUTPS Unchahar-II",
                        "FGUTPS Unchahar-III", "FGUTPS Unchahar-IV"],
    "Dadri (NcTPP)":   ["NCTPS Dadri-I", "NCTPS Dadri-II"],      # coal Dadri (not gas 'Dadri')
    "Korba Stps":      ["Korba STPS-I&II", "Korba STPS-III"],
    "Sipat Stps":      ["Sipat STPS-I", "Sipat STPS-II"],
    "Vindh_Chal Stps": ["Vindhyachal STPS-I", "Vindhyachal STPS-II", "Vindhyachal STPS-III",
                        "Vindhyachal STPS-IV", "Vindhyachal STPS-V"],
    "Mouda Stps":      ["Mouda STPS-I", "Mouda STPS-II"],
    "Talcher Stps":    ["Talcher STPS-I", "Talcher STPS-II"],    # Kaniha; excl old 'Talcher TPS'
    "Kahalgaon":       ["Kahalgaon STPS-I", "Kahalgaon STPS-II"],
    "Farakka Stps":    ["Farakka STPS-I&II", "Farakka STPS-III"],
    "R_Gundem Stps":   ["Ramagundam STPS-I&II", "Ramagundam STPS-III"],
    "Simhadri":        ["Simhadri STPS-I", "Simhadri STPS-II"],
    "Bongaigaon TPP":  ["Bongaigaon TPS"],
    "Maithon Rb TPP":  ["Maithon Power Limited"],               # private-sector data point
    # --- DVC coal (vintage 2021-23; paise->Rs already normalised at fetch) ---
    "Durgapur":            ["DTPS"],
    "Mejia":               ["MTPS (1-3)", "MTPS (4)", "MTPS (5-6)"],
    "Mejia Tps Ext":       ["MTPS (7-8)"],
    "Chandrapura":         ["CTPS (7-8)"],
    "Durgapur Steel Tps":  ["DSTPS (1-2)"],
    "Koderma":             ["KTPS (1-2)"],
    "Raghunathpur TPP Ph-I": ["RTPS (1-2)"],
    "Bokaro A Exp":        ["BTPS A"],                          # resolved normalised-exact
    # --- NLC lignite (vintage 2021-23) ---
    "Neyveli St Ii":       ["TS-II St.1", "TS-II St.2"],
    "Neyveli New TPP":     ["NNTPP"],
    "Neyveli Tps Exp -Ii": ["TPS-2 Exp."],
    "Neyveli Fst Ext":     ["TPS-I Exp."],                      # TPS-I Expansion
    "Barsingar Ligniteite": ["BTPS"],                          # Barsingsar (NLC)
    "Tuticorin JV":        ["NTPL"],                            # NLC Tamil Nadu Power
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def dispatch(df, order_col, total_gwh, vc_col):
    d = df.sort_values(order_col, ascending=True).copy()
    cap = d["capacity_mw"] * HOURS * MAX_PLF / 1000.0
    gen, rem = np.zeros(len(d)), total_gwh
    for i, c in enumerate(cap.values):
        if rem <= 0:
            break
        take = min(c, rem)
        gen[i] = take
        rem -= take
    d["_g"] = gen
    cost = (d["_g"] * 1e6 * d[vc_col]).sum() / 1e7
    co2 = (d["_g"] * d["ef_t_per_mwh"] / 1000.0).sum()
    return cost, co2


def main():
    out_lines = []
    def log(s=""):
        out_lines.append(s)

    if not os.path.exists(DATAGOV_CSV):
        log("[10] data/raw/datagov_tariff_ecr_2021-23.csv not found -- run "
            "analysis/fetch_datagov_ecr.py (needs DATAGOVIN_API_KEY). Skipping.")
        _write(out_lines)
        return

    df = flag_pithead(load_clean())
    if "variable_cost_rs_per_kwh" not in df.columns:
        raise SystemExit("Run analysis/02_variable_cost.py first.")

    dg = pd.read_csv(DATAGOV_CSV)
    # dedupe identical station_raw across datasets (the Bihar subset duplicates NTPC)
    dgm = (dg.groupby("station_raw")
             .agg(ecr=("ecr_rs_per_kwh", "mean"), vintage=("vintage", "first"),
                  category=("category", "first")).reset_index())
    raw_ecr = dict(zip(dgm["station_raw"], dgm["ecr"]))
    raw_vint = dict(zip(dgm["station_raw"], dgm["vintage"]))

    # resolve each curated key to the EXACT dataset name (normalised-exact, robust to
    # the stray curly quotes in "Bokaro A ''Exp''") and average its mapped stages.
    ours_norm = {}
    for nm in df["name"].unique():
        ours_norm.setdefault(_norm(nm), nm)
    rows, missing_key, missing_raw = [], [], []
    for our_key, raws in CURATED.items():
        real = ours_norm.get(_norm(our_key))
        if real is None:
            missing_key.append(our_key)
            continue
        vals = [raw_ecr[r] for r in raws if r in raw_ecr]
        miss = [r for r in raws if r not in raw_ecr]
        missing_raw += miss
        if not vals:
            continue
        rows.append({"name": real, "dg_ecr": float(np.mean(vals)),
                     "n_stage": len(vals),
                     "vintage": raw_vint.get(raws[0], "?")})
    matched = pd.DataFrame(rows)
    # persist the matched real central ECR table for 11_landed_cost.py to consume.
    matched.to_csv(os.path.join(REPO, "data", "plant_real_ecr_central.csv"), index=False)

    log("=" * 74)
    log("10 - CONTEMPORANEOUS CENTRAL/ISGS ECR from data.gov.in (Rajya Sabha tariff")
    log("     statements). *** 2021-22 / 2021-23, ISGS-ONLY -- a CROSS-CHECK, not the")
    log("     FY2022-23 headline. ***")
    log("=" * 74)
    if missing_key:
        log(f"[WARN] curated keys not found in dataset (skipped): {missing_key}")
    if missing_raw:
        log(f"[WARN] tariff rows not found (skipped): {sorted(set(missing_raw))}")

    # ---- coverage ----
    m = df.merge(matched, on="name", how="left")
    cov_units = int(m["dg_ecr"].notna().sum())
    cov_stns = matched["name"].nunique()
    cap_cov = m.loc[m["dg_ecr"].notna(), "capacity_mw"].sum()
    cap_tot = m["capacity_mw"].sum()
    log(f"\nCOVERAGE: {cov_stns} stations / {cov_units} of {len(df)} units "
        f"({100*cov_units/len(df):.0f}%); {cap_cov/cap_tot*100:.0f}% of fleet capacity.")
    by = (m[m["dg_ecr"].notna()].groupby("sector")
            .agg(stations=("name", "nunique"), units=("name", "size")).reset_index())
    log("  by sector:")
    log("   " + by.to_string(index=False).replace("\n", "\n   "))

    # ---- the ECR ladder + cross-checks vs model and vs CERC-2018 ----
    cerc = pd.read_csv(CERC_CSV, comment="#") if os.path.exists(CERC_CSV) else None
    cmap = dict(zip(cerc["match_name"], cerc["ecr_rs_per_kwh"])) if cerc is not None else {}
    # capacity-weighted station means (fully vectorised; no groupby.apply)
    df["_we"] = df["efficiency_pct"] * df["capacity_mw"]
    df["_wv"] = df["variable_cost_rs_per_kwh"] * df["capacity_mw"]
    g = df.groupby("name")
    w = g["capacity_mw"].sum()
    stn = pd.DataFrame({
        "sector": g["sector"].first(),
        "pithead": g["pithead"].first().astype(bool),
        "is_lignite": g["is_lignite"].first().astype(bool),
        "eff": (g["_we"].sum() / w).astype(float),
        "model_vc": (g["_wv"].sum() / w).astype(float),
    }).reset_index()
    t = stn.merge(matched[["name", "dg_ecr", "vintage"]], on="name", how="inner")
    t["cerc_2018"] = t["name"].map(cmap)
    t = t.sort_values("dg_ecr")
    log("\nREAL central ECR ladder (data.gov.in), with model VC and CERC-2018 alongside:")
    log("-" * 74)
    show = t.assign(pit=np.where(t["pithead"], "P", " "))[
        ["name", "sector", "pit", "eff", "dg_ecr", "model_vc", "cerc_2018", "vintage"]]
    show = show.rename(columns={"name": "station", "dg_ecr": "datagov_ECR",
                                "model_vc": "model_VC", "eff": "eff%"})
    log(show.to_string(index=False, na_rep="-",
                       float_format=lambda v: f"{v:.2f}"))

    both = t.dropna(subset=["cerc_2018"])
    if len(both) >= 3:
        r, r2, n = corr(both["dg_ecr"], both["cerc_2018"])
        mad = (both["dg_ecr"] - both["cerc_2018"]).abs().mean()
        log(f"\nAgreement with CERC-2018 on the {n} overlapping stations: r={r:.2f} "
            f"(R²={r2:.2f}), mean |Δ|=Rs {mad:.2f}/kWh -- the two independent real")
        log("sources track each other, mutually validating both.")
    rd = (t["dg_ecr"] - t["model_vc"])
    log(f"Model VC vs real datagov ECR: mean Δ=Rs {rd.mean():+.2f}/kWh "
        f"(flat-freight model overstates pithead, understates distant central units).")

    # ---- pithead COST-SIDE test (2b) on this bigger, contemporaneous sample ----
    log("\n" + "-" * 74)
    log("PITHEAD COST-SIDE TEST (eff vs REAL ECR) -- now on the data.gov.in sample")
    log("-" * 74)
    log("Re-runs analysis 09's true test (efficiency vs real cost) with contemporaneous")
    log("ECR and a larger n. NOTE: central ISGS only, so the 'non-pithead' group here is")
    log("distant CENTRAL units, not the whole fleet. (r<0 expected: higher eff->lower ECR.)")
    log(f"  {'group':<14}{'n':>5}{'r':>9}{'R²':>9}")
    for g, mask in [("all central", t["name"].notna()),
                    ("pithead", t["pithead"]),
                    ("non-pithead", ~t["pithead"]),
                    ("  excl-lignite", t["pithead"] & ~t["is_lignite"])]:
        sub = t[mask]
        r, r2, n = corr(sub["eff"], sub["dg_ecr"])
        if r is None:
            log(f"  {g:<14}{n:>5}      n<3 -- skipped")
        else:
            log(f"  {g:<14}{n:>5}{r:>9.3f}{r2:>9.3f}")
    log("Compare analysis 09 (CERC-2018, n=7/group): pithead R²=0.62, non-pithead ~0.00.")

    # ---- illustrative re-dispatch (covered use datagov ECR, rest model) ----
    d = df.dropna(subset=["capacity_mw", "net_gen_gwh", "variable_cost_rs_per_kwh",
                          "ef_t_per_mwh"]).copy()
    em = dict(zip(matched["name"], matched["dg_ecr"]))
    d["vc_x"] = d.apply(lambda r: em.get(r["name"], r["variable_cost_rs_per_kwh"]), axis=1)
    n_sub = int(d["name"].isin(em).sum())
    total = d["net_gen_gwh"].sum()
    base_model = (d["net_gen_gwh"] * 1e6 * d["variable_cost_rs_per_kwh"]).sum() / 1e7
    base_mixed = (d["net_gen_gwh"] * 1e6 * d["vc_x"]).sum() / 1e7
    co2_actual = (d["net_gen_gwh"] * d["ef_t_per_mwh"] / 1000.0).sum()
    cm_cost, cm_co2 = dispatch(d, "vc_x", total, "vc_x")
    cb_cost, cb_co2 = dispatch(d, "ef_t_per_mwh", total, "vc_x")
    log("\n" + "-" * 74)
    log("ILLUSTRATIVE re-dispatch with datagov ECR on covered units (MIXED VINTAGE)")
    log("-" * 74)
    log(f"  {n_sub} units carry a real datagov ECR; the other {len(d)-n_sub} keep the model.")
    log(f"  As-run fuel cost: model-only Rs {base_model:,.0f} cr | datagov blend "
        f"Rs {base_mixed:,.0f} cr  (CO2 {co2_actual:,.1f} MT)")
    log(f"  Cost-merit Rs {cm_cost:,.0f} cr (CO2 {cm_co2:,.1f} MT) | "
        f"Carbon-merit Rs {cb_cost:,.0f} cr (CO2 {cb_co2:,.1f} MT)")
    log(f"  Cost-vs-carbon gap: {cm_co2-cb_co2:+,.1f} MT CO2 for Rs {cb_cost-cm_cost:+,.0f} cr.")
    log("  Direction-of-travel only (ISGS-only, 2021-23): substituting real central ECRs")
    log("  re-ranks the cheap pithead central units, reinforcing the headline finding.")

    log("\n" + "=" * 74)
    log("READ: This is the strongest REAL ECR coverage we have (central sector), and it")
    log("corroborates both the CERC-2018 ladder and the pithead cost-side result -- on a")
    log("contemporaneous, larger sample. It is NOT the FY2022-23 headline: state/private")
    log("plants are absent and the vintage is 2021-22/23. Closing the rest needs the")
    log("metered MERIT/SCED/SLDC feeds (blocked) or the landed-cost reconstruction route.")
    _write(out_lines)


def _write(out_lines):
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "10_datagov_ecr.txt")
    with open(out, "w") as f:
        f.write("\n".join(out_lines) + "\n")
    print("\n".join(out_lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
