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

SOURCES (best per-station coverage first):
  1. MERIT portal  https://meritindia.in   - station-wise variable charge / ECR.
        Dynamic app; open it in the new session and inspect the XHR/API calls
        (look for a JSON endpoint returning station name + variable cost). That
        endpoint is the highest-yield single source.
  2. CERC tariff orders  https://cercind.gov.in/recent_orders2022.html (and 2023)
        Per-petition PDFs; extract the Energy Charge Rate for regulated central
        stations. Map order -> station by petition title.
  3. Coal India notified prices  https://coal.gov.in / subsidiary sites
        Grade-wise Rs/tonne -> feeds the grade price model in 02 (domestic),
        not per-plant ECR. Improves the fallback, not the override.
  4. CEA fuel-cost / coal-source DB - to correct the domestic/imported tag in 02.

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


def fetch_merit_ecr() -> pd.DataFrame:
    """TODO: hit MERIT's station endpoint, return [match_name, ecr_rs_per_kwh]."""
    raise NotImplementedError(
        "Inspect https://meritindia.in network calls for the station/variable-cost "
        "JSON endpoint, then parse it here. See module docstring.")


def fetch_cerc_ecr() -> pd.DataFrame:
    """TODO: walk CERC order index, download station PDFs, extract ECR."""
    raise NotImplementedError("Implement CERC tariff-order ECR extraction.")


def main():
    rows = []
    for name, fn in [("MERIT", fetch_merit_ecr), ("CERC", fetch_cerc_ecr)]:
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
