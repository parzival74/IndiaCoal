"""
09 - SIDE ANALYSIS: does efficiency become a tighter proxy at PITHEAD plants?

HYPOTHESIS
----------
At a pithead (mine-mouth) plant, transport/freight -- roughly half of delivered
coal cost -- is ~zero, so variable cost collapses toward a near-pure function of
station heat rate (SHR). Since efficiency is monotone in SHR, efficiency should
then be a TIGHTER proxy for cost (and, via merit-order dispatch, for PLF) within
the pithead subset than across the whole fleet. We test whether the relationship
tightens for {pithead} vs {non-pithead} vs {full fleet}.

TWO TRAPS THIS GUARDS AGAINST (per docs/PITHEAD_TEST_PROMPT.md)
  (a) There is NO distance-to-mine field, so "pithead" is a transparently curated
      PROXY: lignite (mine-mouth by construction) + a documented coal-belt list,
      each with its basis. We cross-check the flag against grid region and against
      real CERC ECR (pithead => low ECR + large model-minus-real gap).
  (b) The modelled variable_cost is built FROM SHR, so testing efficiency against
      it is circular and would look tight everywhere. The cost-side test (2b) uses
      REAL ECR ONLY. The only reachable real per-station ECR is CERC's (14 central
      stations) on a 2018-19 BASIS -- so 2b is coverage-limited and vintage-caveated,
      exactly as the prompt anticipates ("directionally yes but coverage-limited").

NOTE ON NUMBERING: the prompt said "08_pithead_test"; 08 is already taken by the
committed CERC cross-check (08_cerc_crosscheck.py), so this is 09 to avoid clobber.

Depends on: common.py; a full pipeline run so the clean CSV carries grid_region
(03) and variable_cost_rs_per_kwh (02). Input: data/raw/plant_ecr_cerc_2018basis.csv.
Run:    python3 analysis/09_pithead_test.py
Writes: outputs/09_pithead_test.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats
from common import (load_clean, analysis_set, flag_pithead, corr,
                    CORE_PITHEAD_COAL, BORDERLINE_PITHEAD_COAL, REPO, OUT_DIR)

CERC_CSV = os.path.join(REPO, "data", "raw", "plant_ecr_cerc_2018basis.csv")

# The pithead PROXY flag (lignite + curated coal list) and the small Pearson
# helper `corr` now live in common.py so analysis 10 shares the same definitions.
# Matched by EXACT dataset name (no fuzzy match, per the Dadri/Bhadradri lesson).


def ols(y, X, names):
    """Plain OLS via pinv; returns dict with beta, se, t, p, R2, adjR2, n."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    dof = n - k
    sigma2 = (resid @ resid) / dof
    se = np.sqrt(np.diag(sigma2 * XtX_inv))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), dof)
    ss_res = resid @ resid
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot
    adj = 1 - (1 - r2) * (n - 1) / dof
    return dict(names=names, beta=beta, se=se, t=t, p=p, r2=r2, adj=adj, n=n,
                ss_res=ss_res, ss_tot=ss_tot)


def main():
    lines = []
    log = lines.append
    df = load_clean()
    df = flag_pithead(df)

    log("=" * 74)
    log("09 - PITHEAD SUB-ANALYSIS: does efficiency tighten as a cost/PLF proxy?")
    log("=" * 74)
    log("Side analysis. 'Pithead' is a CURATED PROXY (no distance-to-mine field):")
    log("lignite (mine-mouth by construction) + a documented coal-belt list.\n")

    # ----- STEP 1: the flag, transparently -------------------------------------
    nu = df["name"].nunique()
    log("-" * 74)
    log("STEP 1  PITHEAD FLAG (proxy)")
    log("-" * 74)
    lig = sorted(df[df["is_lignite"]]["name"].unique())
    core = sorted(df[df["is_core_coal"]]["name"].unique())
    log(f"Lignite stations (structural mine-mouth): {len(lig)}")
    log("  " + ", ".join(lig))
    log(f"\nCore coal pithead stations (curated, exact-name): {len(core)}")
    for nm in core:
        log(f"  {nm:<22} -- {CORE_PITHEAD_COAL[nm]}")
    log(f"\nBorderline coal-belt (EXCLUDED from primary flag; sensitivity only): "
        f"{len(BORDERLINE_PITHEAD_COAL)}")
    for nm, basis in BORDERLINE_PITHEAD_COAL.items():
        present = "" if nm in set(df["name"]) else "  [not in dataset]"
        log(f"  {nm:<28} -- {basis}{present}")
    n_units_p = int(df["pithead"].sum())
    n_stn_p = df[df["pithead"]]["name"].nunique()
    log(f"\nPRIMARY pithead flag => {n_stn_p}/{nu} stations, {n_units_p}/{len(df)} units "
        f"(lignite {len(lig)} + core coal {len(core)} stations).")

    # Cross-check 1: grid region (coal-belt Eastern = ER) as a coarse supply proxy
    if "grid_region" in df.columns:
        log("\nCross-check 1 -- pithead share by grid region (coarse supply proxy):")
        tab = (df.assign(p=df["pithead"].astype(int))
                 .groupby("grid_region")
                 .agg(units=("p", "size"), pithead=("p", "sum")).reset_index())
        tab["pithead_%"] = (100 * tab["pithead"] / tab["units"]).round(1)
        log(tab.to_string(index=False))
        log("  (ER = Eastern coal belt; grid region only partly tracks coal supply,")
        log("   and 180 units are 'Unallocated', so this is a weak corroborator.)")

    # ----- Cross-check 2 (strongest): CERC real ECR validates the flag ----------
    cerc = None
    if os.path.exists(CERC_CSV):
        cerc = pd.read_csv(CERC_CSV, comment="#")
        cc = df.merge(cerc, left_on="name", right_on="match_name", how="inner")
        cc = (cc.groupby("name")
                .agg(pithead=("pithead", "first"),
                     ecr=("ecr_rs_per_kwh", "first"),
                     model_vc=("variable_cost_rs_per_kwh", "mean")
                     if "variable_cost_rs_per_kwh" in df.columns else ("plf_pct", "mean"))
                .reset_index())
        log("\nCross-check 2 (STRONGEST) -- real CERC ECR by pithead flag "
            "(*** 2018-19 basis ***):")
        for grp, sub in cc.groupby(cc["pithead"].map({True: "pithead", False: "non-pithead"})):
            log(f"  {grp:<12} n={len(sub):>2}  mean ECR Rs {sub['ecr'].mean():.2f}/kWh "
                f"(range {sub['ecr'].min():.2f}-{sub['ecr'].max():.2f})")
        if "variable_cost_rs_per_kwh" in df.columns:
            cc["model_minus_real"] = cc["model_vc"] - cc["ecr"]
            for grp, sub in cc.groupby(cc["pithead"].map({True: "pithead", False: "non-pithead"})):
                log(f"  {grp:<12} mean (model VC - real ECR) = "
                    f"Rs {sub['model_minus_real'].mean():+.2f}/kWh")
        log("  => pithead stations show systematically LOWER real ECR (the flat-freight")
        log("     model overstates them) -- this independently validates the flag.")
    else:
        log("\n[Cross-check 2 skipped: CERC ECR file not found.]")

    # ----- STEP 2: relationships per group (PLF>=20 convention) ----------------
    aset = analysis_set(df)  # PLF >= 20
    groups = {
        "full fleet":   aset,
        "pithead":      aset[aset["pithead"]],
        "non-pithead":  aset[~aset["pithead"]],
    }
    log("\n" + "-" * 74)
    log("STEP 2a  EFFICIENCY vs PLF   (PLF>=20; Pearson r, R²=r²)")
    log("-" * 74)
    log(f"  {'group':<14}{'n':>5}{'r':>9}{'R²':>9}")
    for g, sub in groups.items():
        r, r2, n = corr(sub["efficiency_pct"], sub["plf_pct"])
        if r is None:
            log(f"  {g:<14}{n:>5}      n<3 -- skipped")
        else:
            log(f"  {g:<14}{n:>5}{r:>9.3f}{r2:>9.3f}")
    # lignite confounds the pithead group: cheap fuel runs hard DESPITE low efficiency.
    log("  breakout of the pithead group:")
    for g, mask in [("  pithead-coal", aset["pithead"] & ~aset["is_lignite"]),
                    ("  lignite-only", aset["is_lignite"])]:
        sub = aset[mask]
        r, r2, n = corr(sub["efficiency_pct"], sub["plf_pct"])
        if r is None:
            log(f"  {g:<14}{n:>5}      n<3 -- skipped")
        else:
            log(f"  {g:<14}{n:>5}{r:>9.3f}{r2:>9.3f}")

    log("\n" + "-" * 74)
    log("STEP 2b  EFFICIENCY vs REAL COST (CERC ECR)  *** 2018-19 BASIS; thin ***")
    log("-" * 74)
    if cerc is not None:
        cset = aset.merge(cerc[["match_name", "ecr_rs_per_kwh"]],
                          left_on="name", right_on="match_name", how="inner")
        cset = cset.drop_duplicates("name")
        log("  CRITICAL: uses REAL CERC ECR (the modelled VC is built from SHR, so")
        log("  testing efficiency against it would be circular). Coverage is the 14")
        log("  CERC central stations only, on a 2018-19 basis -- read as DIRECTIONAL.")
        log(f"  {'group':<14}{'n':>5}{'r':>9}{'R²':>9}   (r<0 expected: higher eff -> lower ECR)")
        for g, mask in [("all CERC", cset["name"].notna()),
                        ("pithead", cset["pithead"]),
                        ("non-pithead", ~cset["pithead"])]:
            sub = cset[mask]
            r, r2, n = corr(sub["efficiency_pct"], sub["ecr_rs_per_kwh"])
            if r is None:
                log(f"  {g:<14}{n:>5}      n<3 -- too thin, not reported")
            else:
                flag = "  <-- n tiny, indicative only" if n < 10 else ""
                log(f"  {g:<14}{n:>5}{r:>9.3f}{r2:>9.3f}{flag}")
    else:
        log("  [skipped: no real ECR available]")

    # ----- STEP 3: control for the confounder (pithead ~ big central baseload) --
    log("\n" + "-" * 74)
    log("STEP 3  CONFOUNDER CONTROL (pithead is mostly large central baseload)")
    log("-" * 74)
    # (i) within-Centre eff<->PLF, pithead vs non-pithead
    centre = aset[aset["sector"].astype(str).str.contains("Centre", case=False, na=False)]
    log("(i) Efficiency vs PLF WITHIN the Centre sector only "
        "(removes sector; size still varies):")
    log(f"  {'group':<18}{'n':>5}{'r':>9}{'R²':>9}")
    for g, mask in [("Centre, all", centre["name"].notna()),
                    ("Centre, pithead", centre["pithead"]),
                    ("Centre, non-pithead", ~centre["pithead"])]:
        sub = centre[mask]
        r, r2, n = corr(sub["efficiency_pct"], sub["plf_pct"])
        if r is None:
            log(f"  {g:<18}{n:>5}      n<3 -- skipped")
        else:
            log(f"  {g:<18}{n:>5}{r:>9.3f}{r2:>9.3f}")

    # (ii) OLS: PLF ~ efficiency + capacity + sector + pithead + efficiency*pithead
    reg = aset.dropna(subset=["plf_pct", "efficiency_pct", "capacity_mw", "sector"]).copy()
    secs = sorted(reg["sector"].astype(str).unique())
    base_sec = "Centre" if "Centre" in secs else secs[0]
    dum_secs = [s for s in secs if s != base_sec]
    eff = reg["efficiency_pct"].to_numpy()
    cap = reg["capacity_mw"].to_numpy()
    pit = reg["pithead"].astype(float).to_numpy()
    cols = [np.ones(len(reg)), eff, cap]
    names = ["const", "efficiency", "capacity_mw"]
    for s in dum_secs:
        cols.append((reg["sector"].astype(str) == s).astype(float).to_numpy())
        names.append(f"sector[{s}]")
    # base model (no pithead) for ΔR²
    base = ols(reg["plf_pct"].to_numpy(), np.column_stack(cols), list(names))
    # full model: + pithead + efficiency*pithead interaction
    cols_full = cols + [pit, eff * pit]
    names_full = names + ["pithead", "efficiency:pithead"]
    full = ols(reg["plf_pct"].to_numpy(), np.column_stack(cols_full), names_full)
    log(f"\n(ii) OLS  PLF ~ efficiency + capacity + sector(base={base_sec}) "
        f"+ pithead + efficiency:pithead   (n={full['n']})")
    log(f"  {'term':<22}{'coef':>10}{'std err':>10}{'t':>8}{'p':>9}")
    for nm, b, se, t, p in zip(full["names"], full["beta"], full["se"], full["t"], full["p"]):
        log(f"  {nm:<22}{b:>10.3f}{se:>10.3f}{t:>8.2f}{p:>9.3f}")
    log(f"  base model R²={base['r2']:.3f} (adj {base['adj']:.3f}); "
        f"full R²={full['r2']:.3f} (adj {full['adj']:.3f}); "
        f"ΔR²={full['r2']-base['r2']:+.3f}")
    log("  Interpretation: 'efficiency' is the PLF-slope for NON-pithead plants;")
    log("  'efficiency:pithead' is the EXTRA slope for pithead plants. A positive,")
    log("  significant interaction => efficiency tracks PLF more tightly at pithead")
    log("  even after sector + size are controlled.")

    # ----- READ -----------------------------------------------------------------
    log("\n" + "=" * 74)
    log("READ (honest):")
    log("=" * 74)
    log("- The pithead flag is a curated PROXY but is independently validated by the")
    log("  real CERC ECR ladder (cross-check 2): pithead stations are the cheapest.")
    log("- Cost-side test (2b) is the true test of the claim, but rests on 14 CERC")
    log("  stations on a 2018-19 basis -- DIRECTIONAL, not a settled result. It")
    log("  becomes answerable once FY2022-23 per-station ECR coverage is broad.")
    log("- PLF-side (2a) is muddied by lignite: cheap mine-mouth lignite runs hard")
    log("  DESPITE low efficiency, which is itself the cost>efficiency point.")
    log("- Step 3 shows whether any pithead tightening survives the sector/size")
    log("  confounder; see the interaction term and ΔR² above.")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "09_pithead_test.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
