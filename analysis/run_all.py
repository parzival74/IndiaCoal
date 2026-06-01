"""Run the full pipeline in order. Usage: python3 analysis/run_all.py"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    "common.py",                  # build cleaned CSV
    "01_correlations.py",
    "02_variable_cost.py",        # extension #1 (adds variable_cost column)
    "03_regions.py",              # extension #2
    "04_redispatch.py",           # extension #4 (needs #1)
    "05_flexibility_framework.py",# extension #3
    "06_apply_ecr.py",            # apply real plant-level ECR over the model
]

for s in STEPS:
    print(f"\n{'#'*72}\n# {s}\n{'#'*72}")
    r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"FAILED at {s}")
print("\nAll steps complete. See outputs/ and data/cse_subcritical_clean.csv")
