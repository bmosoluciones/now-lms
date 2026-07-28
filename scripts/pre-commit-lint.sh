#!/usr/bin/env bash
# Fork-local L1 gate: block a commit that would fail the deploy line's lint.
#
# Mirrors the fast blocking gates of .github/workflows/deploy-line-ci.yml
# (ruff + flake8) on the STAGED now_lms files only, so a broken commit is
# stopped locally instead of twenty minutes later in CI. pylint (the third
# CI gate) is deliberately NOT run here: its 9.5 score is a whole-package
# measure, and per-file invocation produces different scores — the package
# gate stays CI's job.
#
# Installed into the local git hook chain by scripts/install-git-hooks.sh
# (see that file for why the hook itself cannot be tracked). Bypass for a
# genuine emergency: git commit --no-verify — CI still gates the PR.
#
# Fork-local (Intent Solutions engineering standard); never offered upstream.
set -u

cd "$(git rev-parse --show-toplevel)" || exit 1

# Staged (added/copied/modified/renamed) python files inside now_lms/ —
# the exact scope deploy-line-ci.yml lints.
staged=$(git diff --cached --name-only --diff-filter=ACMR -- 'now_lms/*.py' 'now_lms/**/*.py')
[ -z "$staged" ] && exit 0

if ! command -v python >/dev/null 2>&1; then
    echo "pre-commit-lint: no python on PATH — cannot lint staged now_lms files." >&2
    echo "Activate the venv (source .venv/bin/activate) or bypass with --no-verify." >&2
    exit 1
fi

fail=0

if python -m ruff --version >/dev/null 2>&1; then
    # shellcheck disable=SC2086  # word-splitting the file list is intended
    python -m ruff check $staged || fail=1
else
    echo "pre-commit-lint: ruff not installed in this environment (pip install --require-hashes -r test.lock)." >&2
    fail=1
fi

if python -m flake8 --version >/dev/null 2>&1; then
    # Same flags as deploy-line-ci.yml and dev/test.sh.
    # shellcheck disable=SC2086
    python -m flake8 --max-line-length=120 --ignore=E501,E203,E266,W503,E722 $staged || fail=1
else
    echo "pre-commit-lint: flake8 not installed in this environment (pip install --require-hashes -r test.lock)." >&2
    fail=1
fi

if [ "$fail" -ne 0 ]; then
    echo >&2
    echo "pre-commit-lint: staged now_lms files fail the deploy-line lint gate — commit blocked." >&2
    exit 1
fi

exit 0
