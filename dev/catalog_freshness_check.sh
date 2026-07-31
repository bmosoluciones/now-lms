#!/bin/bash
# Catalog freshness gate.
#
# ROOT CAUSE: .mo is .gitignore'd, so stale .mo files ship on fresh clones
# and demo deploys. Babel falls back to the msgid (Spanish) for any msgid
# added to .po after the .mo was compiled - the demo "Gender rendered in
# Spanish" bug class.
#
# This gate uses python -m now_lms.i18n_autocompile --check which:
#   1. Recompiles any stale .mo (this is the cure if it fails).
#   2. Probes each locale's .mo in a fresh subprocess (Babel caches in-process).
#   3. Returns exit 0 if all sentinels resolve, exit 1 otherwise.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "-------------------------------------------------"
echo "Catalog freshness check"
echo "-------------------------------------------------"

if ! command -v pybabel >/dev/null 2>&1; then
    echo "pybabel not on PATH; install Babel (pip install babel==2.18.0)"
    exit 1
fi

# Run the gate. Use the Python interpreter that pip installed Babel under.
PYTHON="${PYTHON:-python}"
if ! "$PYTHON" -m now_lms.i18n_autocompile --check; then
    echo
    echo "FAIL: stale or missing translation catalog."
    echo "Fix: run 'pybabel compile -d now_lms/translations' locally"
    echo "and verify the gate passes. The autocompile inside the gate"
    echo "should have regenerated any missing .mo; if it didn't, check"
    echo "now_lms/i18n_autocompile.py logs."
    exit 1
fi

echo "OK: all catalogs fresh."
