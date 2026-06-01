"""
08 - CROSS-CHECK: real CERC per-station ECR vs the FY2022-23 headline model.

*** THIS IS A SECONDARY, VINTAGE-MISMATCHED CROSS-CHECK -- NOT THE HEADLINE. ***

The headline variable cost (02) and counterfactual (04/06) are FY2022-23. The only
authoritative PER-STATION ECR that is currently reachable comes from CERC tariff
orders, but those state the ECR on a 2018-19 basis (working-capital ECR computed on
the Oct-Dec 2018 landed coal cost at the start of the 2019-24 tariff period); the
genuinely FY2022-23 per-station feeds (Grid-India SCED, POSOCO, state SLDC, MERIT)
were all unreachable this session. To respect the FY2022-23 vintage rule, those
CERC numbers are kept OUT of the headline and used only here, clearly labelled.

This step does two things, both flagged as 2018-19 basis:
  1. Per-station: lines up the FY2022-23 model VC against the CERC ECR for the
     stations CERC covers -- exposing the real pithead->distant ECR spread
     (~Rs1.25 to ~Rs3.5/kWh) that the headline model's flat freight term flattens.
  2. An ILLUSTRATIVE re-dispatch where the covered stations use their CERC ECR
     (rest keep the model) -- to size how much the headline counterfactual would
     move if real per-station dispersion were available. MIXED VINTAGE: read as a
     direction-of-travel check, not a result.

Input : data/raw/plant_ecr_cerc_2018basis.csv (curated, explicit name mapping).
Depends on: 02_variable_cost.py (variable_cost_rs_per_kwh).
Run:  python3 analysis/08_cerc_crosscheck.py
Writes: outputs/08_cerc_crosscheck.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from common import load_clean, REPO, OUT_DIR

CERC_CSV = os.path.join(REPO, "data", "raw", "plant_ecr_cerc_2018basis.csv")
HOURS, MAX_PLF = 8760, 0.85


def dispatch(df, order_col, total_gwh):
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
    cost = (d["_g"] * 1e6 * d["vc_x"]).sum() / 1e7
    co2 = (d["_g"] * d["ef_t_per_mwh"] / 1000.0).sum()
    return cost, co2


def main():
    lines = []
    log = lines.append
    df = load_clean()
    if "variable_cost_rs_per_kwh" not in df.columns:
        raise SystemExit("Run analysis/02_variable_cost.py first.")
    if not os.path.exists(CERC_CSV):
        raise SystemExit(f"Missing {CERC_CSV}")

    cerc = pd.read_csv(CERC_CSV, comment="#")
    log("=" * 72)
    log("08 - CERC PER-STATION ECR CROSS-CHECK  (*** 2018-19 BASIS, NOT FY2022-23 ***)")
    log("=" * 72)
    log("Headline cost (02) and counterfactual (04/06) are FY2022-23 and are NOT")
    log("changed by this step. CERC tariff-order ECRs are a 2018-19-basis cross-check")
    log("because the FY2022-23 per-station feeds (Grid-India SCED/POSOCO/SLDC/MERIT)")
    log("were unreachable this session. Station-name mapping is explicit (not fuzzy).\n")

    # Exact join on the curated match_name (already dataset station names).
    names = set(df["name"])
    miss = sorted(set(cerc["match_name"]) - names)
    if miss:
        log(f"[WARN] CERC rows not found in dataset (skipped): {miss}")
    m = df.merge(cerc, left_on="name", right_on="match_name", how="inner")
    # one row per station (these are all single-name central stations)
    comp = (m.groupby("name")
              .agg(sector=("sector", "first"),
                   model_vc=("variable_cost_rs_per_kwh", "mean"),
                   cerc_ecr=("ecr_rs_per_kwh", "first"),
                   basis=("basis", "first"),
                   plf=("plf_pct", "mean"))
              .reset_index().sort_values("cerc_ecr"))
    comp["model_minus_cerc"] = (comp["model_vc"] - comp["cerc_ecr"]).round(2)

    log(f"Stations with a CERC ECR matched to the dataset: {comp['name'].nunique()}")
    log("\nPer-station: FY2022-23 model VC  vs  CERC ECR (2018-19 basis), Rs/kWh")
    log("-" * 72)
    show = comp.rename(columns={"name": "station"})[
        ["station", "sector", "model_vc", "cerc_ecr", "model_minus_cerc", "basis", "plf"]]
    log(show.round(3).to_string(index=False))

    log("\nWhat the cross-check shows:")
    log(f"  Real CERC ECR spread : Rs {comp['cerc_ecr'].min():.2f} (pithead) -> "
        f"Rs {comp['cerc_ecr'].max():.2f}/kWh (distant) across these central stations.")
    log(f"  Model VC spread      : Rs {comp['model_vc'].min():.2f} -> "
        f"Rs {comp['model_vc'].max():.2f}/kWh  (flat freight COMPRESSES the real range).")
    log("  => The model's single freight term overstates pithead stations (Korba,")
    log("     Sipat, Singrauli) and understates distant ones (Dadri, Unchahar, Indira")
    log("     Gandhi). Per-plant rail freight / pithead-distance is the missing axis.")

    # ---- ILLUSTRATIVE re-dispatch: covered stations use CERC ECR, rest = model ----
    d = df.dropna(subset=["capacity_mw", "net_gen_gwh", "variable_cost_rs_per_kwh",
                          "ef_t_per_mwh"]).copy()
    ecr_map = dict(zip(cerc["match_name"], cerc["ecr_rs_per_kwh"]))
    d["vc_model"] = d["variable_cost_rs_per_kwh"]
    d["vc_x"] = d.apply(lambda r: ecr_map.get(r["name"], r["variable_cost_rs_per_kwh"]), axis=1)
    n_sub = int(d["name"].isin(ecr_map).sum())
    total = d["net_gen_gwh"].sum()

    base_model = (d["net_gen_gwh"] * 1e6 * d["vc_model"]).sum() / 1e7
    base_mixed = (d["net_gen_gwh"] * 1e6 * d["vc_x"]).sum() / 1e7
    co2_actual = (d["net_gen_gwh"] * d["ef_t_per_mwh"] / 1000.0).sum()
    cm_cost, cm_co2 = dispatch(d, "vc_x", total)
    cb_cost, cb_co2 = dispatch(d, "ef_t_per_mwh", total)

    log("\n" + "-" * 72)
    log("ILLUSTRATIVE re-dispatch with CERC ECR on the covered stations (MIXED VINTAGE)")
    log("-" * 72)
    log(f"  {n_sub} units carry a real CERC ECR; the other {len(d)-n_sub} keep the FY2022-23 model.")
    log(f"  As-run fuel cost: model-only Rs {base_model:,.0f} cr | with CERC blend "
        f"Rs {base_mixed:,.0f} cr  (CO2 {co2_actual:,.1f} MT)")
    log(f"  Cost-merit  : Rs {cm_cost:,.0f} cr | CO2 {cm_co2:,.1f} MT")
    log(f"  Carbon-merit: Rs {cb_cost:,.0f} cr | CO2 {cb_co2:,.1f} MT")
    log(f"  Cost-vs-carbon gap: {cm_co2-cb_co2:+,.1f} MT CO2 for Rs {cb_cost-cm_cost:+,.0f} cr.")
    log("\n  Direction-of-travel only (do not quote as a FY2022-23 result): substituting")
    log("  the real per-station dispersion mainly RE-RANKS the cheap pithead central")
    log("  units, reinforcing the headline finding that cost- and carbon-merit diverge.")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "08_cerc_crosscheck.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
