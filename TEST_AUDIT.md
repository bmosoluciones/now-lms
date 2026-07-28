# TEST_AUDIT.md — now-lms (Intent Solutions fork)

**Audited:** 2026-07-28 · branch `feat/blueprint-docs-and-test-layers` · `/audit-tests` (diagnostic-only)
**Grade at audit:** C+ (70/100) → **after `/implement-tests` same day: B (83/100)** — see "Post-install state" below.
**Classification:** `service` (Flask web application; PostgreSQL production, SQLite test fixture)
**Harness at audit:** NOT installed → **now vendored v1.3.1** (`.audit-harness/` + `scripts/audit-harness`; manifest `.harness-hash` pins `features/*.feature`).

## Post-install state (2026-07-28, same branch)

| Gap | Status |
|---|---|
| P0 L1 hooks | **CLOSED** — `scripts/pre-commit-lint.sh` (ruff + flake8 on staged `now_lms/` files) chained into `.beads/hooks/pre-commit` outside the beads markers by `scripts/install-git-hooks.sh` (idempotent, verified ×2). `bd hooks list` still reports 5 installed. A deliberately lint-failing commit was blocked (verified). |
| P1 L0 harness | **CLOSED** — v1.3.1 vendored; `scripts/audit-harness verify` → OK. |
| P1 L3 coverage | **CLOSED (measured, not gated)** — `--cov=now_lms --cov-report=term` added to the deploy-line CI pytest step, with an in-file comment stating why no threshold ships with the first measurement. |
| P1 L6 features | **CLOSED** — `features/request_access.feature` + `features/gating_boundary.feature`, engineer-owned, hash-pinned, written from shipped behavior. |
| Scaffolds | **CLOSED** — `tests/TESTING.md` (policy flagged for engineer review), `tests/RTM.md` (12 REQs, 1 SHOULD partial), `tests/PERSONAS.md` (4), `tests/JOURNEYS.md` (4). |
| P2 items | Open by design (mypy-in-CI, CodeQL, mutation, smoke-assertion tightening) — logged, not this PR. |

> Transient report. The handoff payload at the bottom drives `/implement-tests`.
> Fork constraint that shapes everything here: platform test files are largely
> upstream-inherited; fork-local enforcement must never be pushed upstream and
> must be recorded in `FORK.md` as fork-local engineering standard.

## Per-layer map

| Layer | Status | Evidence | Severity |
|---|---|---|---|
| L0 harness | **absent** | no `.audit-harness/`, no `scripts/audit-harness`, no manifest | P1 (install first) |
| L1 git hooks | **absent** | `core.hooksPath=.beads/hooks` (beads sync only: post-checkout, post-merge, pre-commit*, pre-push, prepare-commit-msg — none run lint/tests). Nothing blocks a broken commit locally. | **P0** |
| L2 static | **installed + enforced** | ruff + flake8 (`--max-line-length=120`) + `pylint --fail-under=9.5` blocking in `deploy-line-ci.yml`; mypy in `dev/test.sh` but **not** in the CI job | P2 (mypy absent from CI) |
| L3 unit | **installed, coverage invisible at the gate** | 51 test files; `pytest-cov` in `test.lock`; `dev/test.sh` runs `--cov=now_lms` locally, but the deploy-line CI pytest step runs bare (`pytest --tb=short -q`) and no coverage report/artifact exists on the gate. `codecov.yml` only feeds `release.yml`, which never fires on the deploy line. | **P1** |
| L3 bias | advisory | `bias-count.sh`: 91 smoke-only (`is not None`-class) assertions | advisory |
| L3 mutation | absent | no mutmut config | P2 (deferred — suite must first be green on PG post-sync) |
| L4 integration | **installed, advisory** | PG-backed pytest in CI with `continue-on-error: true` — deliberate + documented (~34 pre-existing failures in two classes both repaired wholesale by the v2.0.0 sync); `test_multipledb.py`, `test_alembic_upgrade.py` present | documented, flips to blocking at sync (#14) |
| L5 security | partial | Greptile + MiniMax AI review on PRs; no CodeQL/semgrep/gitleaks workflow | P2 |
| L6 E2E/BDD | **absent (Gherkin)** | `test_end_to_end_*.py` exist (in-process route-level), but **0 `.feature` files** — no engineer-owned acceptance spec for the flows now carrying real user data (`/request-access`, gating boundary) | **P1** |
| L7 acceptance | partial | `scripts/deploy-smoke.sh` hard-fails deploys unless `/request-access` serves, teaser is live, `/contact` 404s — real production acceptance, but not linked to written scenarios | P2 |

## Deterministic gate results

| Gate | Result |
|---|---|
| Hash manifest | none (fresh repo) |
| Bias count | 91 smoke-only assertions (advisory; mostly upstream-inherited tests) |
| Gherkin lint | N/A — zero `.feature` files (the finding itself) |
| Coverage | **unmeasured on the gate** — the P1 above; measuring it is the fix, gating it is explicitly out of scope this PR |
| Mutation / CRAP | not run — suite is red on the high-fidelity (PG) path for pre-existing reasons; measurement deferred until post-sync green |
| Escape-scan | clean (docs-only diff staged this branch) |

## Known pre-existing failure baseline (do not re-litigate)

~34 full-suite PostgreSQL failures, verified identical on a clean baseline:
SQLite-masked strictness bugs (varchar-too-long, fixture FK violations) +
i18n assertion drift (fork emits English, inherited tests assert Spanish).
Both classes are replaced wholesale by the v2.0.0 sync. Any NEW failure is
unambiguous against this baseline. `dev/lint.sh` is broken on this branch
(missing `dev/ensure_headers.py`; upstream #217 has the fix, arrives with the
sync) — use `dev/test.sh`.

## RTM / personas / journeys

All absent (`tests/RTM.md`, `tests/PERSONAS.md`, `tests/JOURNEYS.md`,
`tests/TESTING.md`). Fresh-repo scaffold path: `/implement-tests` generates
initial skeletons from the ADR set (`000-docs/002/006/008/009/010-AT-ADEC`),
the PRD (`000-docs/001-PP-PROD`), and the locked plan (`000-docs/011-PP-PLAN`)
— unusually rich source material for a first RTM.

## Gap list

**P0**
1. L1 — no local enforcement hook; `core.hooksPath` is claimed by `.beads/hooks`, so the install MUST chain (call the beads hook, then lint) — replacing it breaks beads sync.

**P1**
2. L0 — vendor `@intentsolutions/audit-harness` in-repo (Python repo → `install.sh` vendoring); hooks/CI reference the in-repo copy, never `~/.claude/` paths.
3. L3 — coverage invisible on the deploy-line gate: add `--cov=now_lms` + a visible report to the CI pytest step. **Measured, NOT gated** — no `--cov-fail-under`, no Codecov ratchet, in this PR.
4. L6 — zero `.feature` files: scaffold acceptance features for the two flows carrying real user data — the `/request-access` intake and the anonymous gating boundary (302-to-intake, teaser, `/contact` 404) — matching the shipped behavior and the deploy smoke.

**P2 (logged, not this PR)**
5. mypy runs locally but not in the CI lint block.
6. No CodeQL/secret-scan workflow on the fork.
7. Mutation testing — post-sync, once PG suite is green.
8. 91 smoke-only assertions — mostly upstream-inherited; tightening them is upstream-contribution work, not fork-local.

## Handoff payload → /implement-tests

```json
{
  "classification": {"repo_type": "service", "language": "python", "package_manager": "pip", "monorepo": false},
  "tests_md_path": "tests/TESTING.md",
  "p0_gaps": [
    {"layer": "L1", "gap": "no lint/test git hook; must CHAIN with core.hooksPath=.beads/hooks (beads sync), never replace it"}
  ],
  "p1_gaps": [
    {"layer": "L0", "gap": "vendor @intentsolutions/audit-harness in-repo via install.sh; reference in-repo copy only"},
    {"layer": "L3", "gap": "add --cov=now_lms + visible report to deploy-line-ci.yml pytest step; measured not gated"},
    {"layer": "L6", "gap": "scaffold features/*.feature for /request-access intake and the gating boundary"}
  ],
  "rtm_gaps": ["tests/RTM.md absent — scaffold from ADRs 1-5 + PRD + 011-PP-PLAN"],
  "persona_gaps": ["tests/PERSONAS.md absent — personas exist in PRD §3 (cohort member, operator/admin, anonymous visitor)"],
  "journey_gaps": ["tests/JOURNEYS.md absent — journeys exist in 011-PP-PLAN verification sweep"],
  "install_order": ["L0", "L1", "L3-coverage", "L6", "scaffolds"],
  "constraints": [
    "fork: enforcement is fork-local, recorded in FORK.md, never offered upstream",
    "no new blocking gates in this PR (coverage measured only; 34 PG failures pre-existing)",
    "beads hooks must keep working: bd hooks list must still report 5 installed after L1 lands"
  ]
}
```
