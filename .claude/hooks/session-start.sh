#!/bin/bash
# SessionStart hook: install Python deps and run the analysis pipeline so that
# data/ and outputs/ are fresh at the start of each Claude Code on the web session.
set -euo pipefail

# Only run in Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Install dependencies (idempotent; container state is cached after first run).
pip install --quiet -r requirements.txt

# Regenerate cleaned data + outputs. Deterministic, so this produces no git diff.
# Non-fatal: a pipeline hiccup should not block the session from starting.
python3 analysis/run_all.py >/dev/null || echo "[session-start hook] run_all.py failed (non-fatal)"
