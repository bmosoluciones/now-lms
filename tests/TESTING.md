# TESTING.md — now-lms (Intent Solutions fork)

Testing policy + observed state for the fork. Scaffolded 2026-07-28 by
`/implement-tests`; policy sections are **engineer-owned** (edits re-pin via
`scripts/audit-harness init`). Everything in this file is **fork-local**
engineering standard — never offered upstream (see `FORK.md`).

## Classification

- Repo type: `service` (Flask web application)
- Language: Python 3.12 (prod), pip + `test.lock` (hash-pinned installs)
- Databases: PostgreSQL 16 (production, high-fidelity test path), SQLite
  (fast local fixture — known bugs, see Baseline below)
- Monorepo: no

## Thresholds (policy — engineer-owned)

<!-- ENGINEER REVIEW: all thresholds below are MEASURE-ONLY at scaffold time.
     No blocking floor may be added until a baseline exists and the v2.0.0
     sync repairs the inherited suite. Raising a threshold to blocking is a
     deliberate separate change, never bundled with a feature PR. -->

| Gate | Floor | Enforcement |
|---|---|---|
| coverage.line | none (measure-only) | `--cov=now_lms` visible in deploy-line CI; no `--cov-fail-under` |
| mutation.kill | none | not installed (deferred post-sync) |
| pylint | 9.5 | **blocking** in deploy-line CI (pre-existing gate, unchanged) |
| ruff / flake8 | clean | **blocking** in deploy-line CI + L1 pre-commit gate |
| architecture | none | no rule file (candidate post-sync) |

## Waived layers

- L5-a11y — no accessibility tooling; the theme layer is verified manually
  (375/390/768/1024/1440px review recorded in `FORK.md` 2026-07-23).
- L7-UAT-formal — production acceptance is `scripts/deploy-smoke.sh`
  (hard-fails the deploy), not a manual UAT round.

## Installed gates (observational)

- L0: `@intentsolutions/audit-harness` v1.3.1, vendored at `.audit-harness/`
  + `scripts/audit-harness` (2026-07-28).
- L1: `scripts/pre-commit-lint.sh` (ruff + flake8 on staged `now_lms/` files,
  mirroring the deploy-line lint gate) chained into the local
  `.beads/hooks/pre-commit` **outside** the beads-managed markers by
  `scripts/install-git-hooks.sh`. Per-clone install (`.beads/` is
  git-ignored): run the installer once after `bd init`; `bd hooks list` must
  still report 5 beads hooks.
- L2: ruff + flake8 + `pylint --fail-under=9.5` blocking in
  `deploy-line-ci.yml`; mypy advisory in the same workflow (3 pre-existing
  `coupons.py` errors — flips blocking when fixed); CodeQL (python) + gitleaks
  full-history secret scan in `security-scans.yml` (2026-07-28).
- L3: pytest, 51 test files; coverage measured via `--cov=now_lms` (CI +
  `dev/test.sh`), not gated.
- L4: PostgreSQL-backed pytest in CI, advisory (`continue-on-error`) until
  the v2.0.0 sync — see Baseline.
- L6/L7: `features/*.feature` (engineer-owned, hash-pinned) +
  `scripts/deploy-smoke.sh` production smoke.

## Frameworks

pytest (+ pytest-cov, markers: slow / comprehensive / integration / unit /
benchmark), flask test client fixtures in `tests/conftest.py`.

## Baseline (pre-existing failures — do not re-litigate)

~34 full-suite PostgreSQL failures verified identical on a clean baseline:
SQLite-masked strictness bugs + i18n assertion drift, both repaired wholesale
by the upstream v2.0.0 sync (`000-docs/006-AT-ADEC`,
`000-docs/007-OD-CHNG`). The test gate flips to blocking at the sync (#14).
Any failure NOT in this baseline is a regression. `dev/lint.sh` is broken on
this branch (missing `dev/ensure_headers.py`) — use `dev/test.sh`.

## Last audit

2026-07-28 — `/audit-tests`, grade C+ (70/100). Report: `TEST_AUDIT.md`
(transient). Gaps closed same day: L0 harness, L1 hook chain, L3 coverage
visibility, L6 feature specs, traceability scaffolds.

## Traceability

- Requirements: `tests/RTM.md`
- Personas: `tests/PERSONAS.md`
- Journeys: `tests/JOURNEYS.md`
- Decision records: `000-docs/00{2,6,8,9}-AT-ADEC-*.md`, `000-docs/010-AT-ADEC-*.md`
- Product baseline: `000-docs/001-PP-PROD-now-lms-fork-prd.md`
