# TEST_AUDIT.md — now-lms fork (transient)

**Date:** 2026-07-29 · **Trigger:** `/audit-tests` (owner) · **Branch:** `deploy/now-lms-fixed` (post-v2.0.0-sync)

## Grade: B- (78/100) — up from C+ (70) at the 07-28 audit

The v2.0.0 sync repaired the inherited suite (~34 baseline failures → 1 known
test-infra flake), coverage is measured in CI, lint is blocking, secrets/CodeQL
scan. What keeps this out of the A range is the layer that tonight's incident
proved missing.

## The headline gap (P0): no browser-level E2E — and it just cost us

**Answer to "what E2E are we running with tools like Playwright": none.**
Current L6/L7 = Gherkin *declarations* (`features/*.feature`, 2 files) +
`scripts/deploy-smoke.sh` (curl-level: status codes + bytes served) + Flask
test-client integration tests. No Playwright/Selenium/Cypress anywhere in any
lockfile.

Proof of the gap's cost: **all 49 founding members were locked out of both
courses** (U12 — access helper demanded a completed `pago` even on free
courses) and *nothing failed*. 51 test files green, smoke green, deploy
"verified" — because no test ever walked the one journey the platform exists
for: **member logs in → opens course → opens lesson**. The smoke checks bytes;
it cannot see that an enrolled member's course page renders an Enroll button
instead of lessons.

## Per-layer state

| Layer | State |
|---|---|
| L0 harness | vendored v1.3.1, `verify` OK |
| L1 hooks | installed (pre-commit lint chain) |
| L2 static | ruff/flake8/pylint 9.5 blocking; mypy advisory; CodeQL + gitleaks |
| L3 unit | 51 files; PG suite = 1 known flake (weakref teardown); coverage measured, not gated. Bias: 96 smoke-only (`is not None`) assertions (advisory) |
| L4 integration | PG-backed suite in CI — still `continue-on-error`; **flip now due** (bead `now-lms-dbq`), the sync that justified advisory has landed |
| L5 system | deploy smoke + healthchecks; a11y waived (policy) |
| **L6 E2E** | **P0 GAP — no browser tests; being installed this session (`e2e/` + Playwright + CI job)** |
| L7 acceptance | 2 Gherkin specs, lint-clean, hash-pinned |

## P0/P1 list

1. **P0 — L6 browser E2E absent.** → `implement-tests` handoff (this session):
   Playwright member-journey spec pinning the U12 regression (enrollment with
   `pago=NULL` on a free course MUST open lessons), plus the gating boundary.
2. **P1 — L4 advisory→blocking flip** (`now-lms-dbq`): the stated condition
   (v2.0.0 sync repairs suite) is now true.
3. **P2 — bias burn-down:** 96 smoke-only assertions.

## CI capacity note (owner question)

This repo is **public → GitHub-hosted Actions minutes are free/unmetered**;
"running out of Actions" cannot happen here. A self-hosted runner on the dev
box for THIS repo is a net security risk (public-repo fork PRs + a runner on a
personal machine). If a *private* Intent Solutions repo runs low on minutes,
that's where an ephemeral self-hosted runner belongs — separate decision.

## Escape-scan: n/a (no pending third-party diff; owner-invoked audit)
