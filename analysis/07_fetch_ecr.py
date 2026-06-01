"""
07 - Fetch real plant-level ECR / coal-price data, then hand off to 06.

STATUS: SCAFFOLD, NOT YET RUN. Written in a session whose container was firewalled
(Trusted policy: cercind/coal.gov.in/cea.nic.in/meritindia all returned HTTP 403).
The environment was switched to Full network access, but that only takes effect in
a NEW session. Run this there, inspect the real responses, and complete the
parser TODOs. Until then it is intentionally inert: it will not write fake data.

GOAL: produce data/raw/plant_ecr.csv with columns
    match_name, ecr_rs_per_kwh, period, source
which 06_apply_ecr.py then fuzzy-matches onto the plant table.

VINTAGE RULE: the performance data is FY2022-23, so collect FY2022-23 ECR only.
Do NOT use current-year prices (coal prices swung hugely; mixing vintages breaks
the cost-vs-PLF comparison). Wayback is deliberately NOT used (MERIT's data was
dynamic so snapshots don't capture it; the dated docs below are better anyway).

SOURCES, ranked (see docs/data_sources.md #1 for detail):
  1. CERC FY2022-23 tariff orders  https://cercind.gov.in/recent_orders2022.html
        (+ .../recent_orders2023.html) - authoritative regulated ECR for central/
        ISGS stations (NTPC, DVC, NLC). Per-petition PDFs; map order -> station.
  2. Grid-India FY2022-23 SCED statements / RLDC reports - per-generator variable
        cost for interstate stations. grid-india.in, posoco.in, eLibrary
        https://hrd.posoco.in/elibrary, RLDCs (nrldc/wrldc/srldc/erldc/nerldc).
  3. State SLDC daily Merit-Order-Despatch stacks - most granular per-station
        Rs/kWh; ~30 heterogeneous sites (e.g. Odisha SLDC Merit_Order, MSLDC,
        KSLDC, GSLDC). Covers state gencos.
  4. Coal India 2022-23 grade-wise notified prices  https://coal.gov.in -> grade
        Rs/tonne x plant SHR: universal modelled-ECR fallback + improves 02.
  5. MERIT / NPP mirror (LAST RESORT): MERIT https://meritindia.in is an
        INTERACTIVE MAP - inspect background XHR/JSON for the station/variable-cost
        endpoint (don't scrape HTML); it is flaky. NPP mirror:
        https://npp.gov.in/dashBoard/gc-map-dashboard-meritchart

This file deliberately ships with parsers unimplemented so it never fabricates
ECR values. Fill them against the real responses, then run 06_apply_ecr.py.
"""
from __future__ import annotations
import os
import time
import pandas as pd
from common import REPO

OUT = os.path.join(REPO, "data", "raw", "plant_ecr.csv")
CACHE = os.path.join(REPO, "data", "raw", "_ecr_cache")

MERIT_BASE = "https://meritindia.in"
CERC_ORDER_INDEX = ["https://cercind.gov.in/recent_orders2022.html",
                    "https://cercind.gov.in/recent_orders2023.html"]


def _get(url: str, binary: bool = False, retries: int = 4):
    """GET with retry + on-disk cache. Imports requests lazily (network session)."""
    import requests  # available once the session has network
    os.makedirs(CACHE, exist_ok=True)
    key = os.path.join(CACHE, url.replace("://", "_").replace("/", "_")[:180])
    if os.path.exists(key):
        return open(key, "rb").read() if binary else open(key, encoding="utf-8", errors="replace").read()
    for i in range(retries):
        try:
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            data = r.content if binary else r.text
            mode = "wb" if binary else "w"
            with open(key, mode) as f:
                f.write(data if binary else data)
            return data
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                raise
            time.sleep(2 ** i)


def fetch_cerc_ecr() -> pd.DataFrame:
    """TODO (source 1): walk the CERC FY2022-23 order index, download per-station
    tariff PDFs, extract the Energy Charge Rate, map petition title -> station.
    Return [match_name, ecr_rs_per_kwh, period, source]."""
    raise NotImplementedError("Implement CERC FY2022-23 tariff-order ECR extraction.")


def fetch_sced_ecr() -> pd.DataFrame:
    """TODO (source 2): pull Grid-India FY2022-23 SCED statements / RLDC reports;
    extract per-generator variable cost for interstate stations."""
    raise NotImplementedError("Implement Grid-India SCED variable-cost extraction.")


def fetch_sldc_ecr() -> pd.DataFrame:
    """TODO (source 3): scrape state SLDC daily MOD stacks (per-station Rs/kWh).
    ~30 heterogeneous sites; start with ones publishing clean tables/CSV."""
    raise NotImplementedError("Implement SLDC merit-order-stack ECR extraction.")


def fetch_merit_ecr() -> pd.DataFrame:
    """TODO (source 5, LAST RESORT): MERIT is an interactive map; inspect its
    background XHR/JSON for the station/variable-cost endpoint (don't scrape HTML).
    Try the NPP mirror npp.gov.in/dashBoard/gc-map-dashboard-meritchart if down."""
    raise NotImplementedError(
        "MERIT is an interactive map - find its XHR/JSON data endpoint. Prefer "
        "sources 1-4 (CERC/SCED/SLDC/Coal-India) which are dated and reliable.")


def main():
    # Ordered by reliability/authority; MERIT is intentionally last.
    sources = [("CERC", fetch_cerc_ecr), ("SCED", fetch_sced_ecr),
               ("SLDC", fetch_sldc_ecr), ("MERIT", fetch_merit_ecr)]
    rows = []
    for name, fn in sources:
        try:
            df = fn()
            print(f"[{name}] fetched {len(df)} rows")
            rows.append(df)
        except NotImplementedError as e:
            print(f"[{name}] not implemented yet: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] fetch failed: {e}")

    if not rows:
        print("\nNo sources implemented/succeeded. Not writing data/raw/plant_ecr.csv")
        print("(refusing to emit fabricated ECR). Complete a parser above and re-run.")
        return
    out = pd.concat(rows, ignore_index=True).dropna(subset=["ecr_rs_per_kwh"])
    out["period"] = out.get("period", "FY2022-23")
    out.to_csv(OUT, index=False)
    print(f"\nWrote {len(out)} ECR rows -> {OUT}\nNow run: python3 analysis/06_apply_ecr.py")


if __name__ == "__main__":
    main()
