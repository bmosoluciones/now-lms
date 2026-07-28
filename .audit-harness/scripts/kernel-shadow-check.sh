#!/usr/bin/env bash
# kernel-shadow-check.sh — flag local re-declarations of kernel-owned contracts.
#
# The kernel @intentsolutions/core is the single source of truth for the
# canonical platform contracts: the gate-result/v1 predicate shape and the
# evidence-bundle payload shape (and, downstream, the authoring/v1 artifact
# schemas). This repo (audit-harness) is a CONSUMER of those contracts — it
# emits gate-result rows and EvidenceBundles, it must NOT re-define their
# shapes. A local re-declaration ("shadow") is supply-chain drift: the harness
# would validate against its own stale copy instead of the kernel the dashboard
# verifies with.
#
# This detector greps for files that re-DECLARE a kernel-owned schema shape,
# as opposed to REFERENCING the kernel (importing from @intentsolutions/core,
# or naming the predicate URI in a gate_id string — both legitimate).
#
# A SHADOW is:
#   * a JSON Schema document whose "$id" claims a kernel-owned canonical id
#     (evals.intentsolutions.io/gate-result/... or .../evidence-bundle/...), OR
#   * a TS/Python source file that DEFINES (not imports) a GateResultV1 /
#     EvidenceBundle / EvidenceBundlePayload type/interface/class.
#
# NOT a shadow (allowlisted):
#   * tests/fixtures/**   — a frozen offline copy of the kernel schema, pinned
#                           deliberately so the regression suite runs without a
#                           network fetch. This is a test pin, not a contract.
#   * ci/**               — the CI-only emitter; it IMPORTS the kernel validators
#                           (@intentsolutions/core/validators/v1/*) and only
#                           declares emitter-internal plumbing types.
#   * schemas/conform/**  — the harness's OWN deterministic structural floor for
#                           authoring artifacts, namespaced under conform/v1.
#                           This is a separate, shallower contract from the
#                           kernel authoring/v1 validity SSoT — intentionally
#                           different, not a re-declaration.
#
# Background: iah-E02 (the architecture question — peerDep-only vs full TS port
# vs second-emitter — that historically blocked a standing kernel-shadow check)
# is now CLOSED, so this detector ships.
#
# Exit codes:
#   0 — no shadows found (or shadows found in advisory/default mode)
#   1 — shadows found AND --strict was passed (gate)
#
# Default mode is ADVISORY (exit 0, annotate). Pass --strict to make a shadow
# a hard failure. CI runs the advisory mode so the lane is green while still
# surfacing any shadow as a GitHub annotation.

set -euo pipefail

# Bash version floor: these gates rely on bash 4+ features. Refuse early with a
# clear message on bash 3.x (e.g. macOS system bash) instead of failing later
# with a cryptic syntax error (jcgw).
[ "${BASH_VERSINFO:-0}" -ge 4 ] || { echo 'audit-harness requires bash >= 4' >&2; exit 3; }

STRICT=0
ROOT="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict) STRICT=1; shift ;;
    --root) ROOT="${2:-.}"; shift 2 ;;
    --help|-h)
      echo "Usage: kernel-shadow-check.sh [--strict] [--root DIR]"
      echo "  Flags local re-declarations of kernel-owned gate-result/evidence-bundle contracts."
      echo "  Default: advisory (exit 0). --strict: exit 1 on any shadow."
      exit 0 ;;
    *) echo "kernel-shadow-check: unknown arg '$1'" >&2; exit 2 ;;
  esac
done

cd "$ROOT"

# Paths that are allowed to carry a kernel-shaped artifact (see header).
# A match is a shadow only if it is OUTSIDE all of these.
is_allowlisted() {
  case "$1" in
    tests/fixtures/*) return 0 ;;
    ci/*)             return 0 ;;
    schemas/conform/*) return 0 ;;
    node_modules/*)   return 0 ;;
    .git/*)           return 0 ;;
    *) return 1 ;;
  esac
}

shadows=()

# 1. JSON Schema documents claiming a kernel-owned canonical $id.
#    The kernel owns gate-result/<ver> and evidence-bundle/<ver> ids under
#    evals.intentsolutions.io. conform/v1 ids are the harness's own (allowlisted
#    structurally by the schemas/conform/ path skip below).
# shellcheck disable=SC2016  # the grep pattern's $id is a literal, not a shell var
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  rel="${f#./}"
  is_allowlisted "$rel" && continue
  shadows+=("$rel  (re-declares a kernel-owned JSON Schema \$id)")
done < <(grep -rIlE '"\$id"[[:space:]]*:[[:space:]]*"https://evals\.intentsolutions\.io/(gate-result|evidence-bundle)/' \
            --include='*.json' --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null || true)

# 2. TS/Python source DEFINING (not importing) a kernel-owned type/class.
#    Definitions look like `interface GateResultV1`, `class EvidenceBundle`,
#    `type EvidenceBundlePayload = ...`. Imports (`import { GateResultV1Schema }
#    from '@intentsolutions/core/...'`) are NOT matched by these anchors.
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  rel="${f#./}"
  is_allowlisted "$rel" && continue
  shadows+=("$rel  (defines a kernel-owned type — should import from @intentsolutions/core)")
done < <(grep -rIlE \
            '(^|[[:space:]])(export[[:space:]]+)?(interface|class|type)[[:space:]]+(GateResultV1|EvidenceBundle|EvidenceBundlePayload)\b' \
            --include='*.ts' --include='*.py' --exclude-dir=node_modules --exclude-dir=.git . 2>/dev/null || true)

if [[ ${#shadows[@]} -eq 0 ]]; then
  echo "kernel-shadow-check: clean — no local re-declarations of kernel-owned contracts."
  exit 0
fi

echo "kernel-shadow-check: found ${#shadows[@]} potential kernel shadow(s):" >&2
for s in "${shadows[@]}"; do
  echo "  - $s" >&2
  # GitHub Actions annotation (surfaces in the PR even in advisory mode).
  file_only="${s%%  *}"
  echo "::warning file=${file_only}::kernel shadow — this file re-declares a kernel-owned contract; reference @intentsolutions/core instead"
done

if [[ "$STRICT" -eq 1 ]]; then
  echo "kernel-shadow-check: --strict — failing the build." >&2
  exit 1
fi

echo "kernel-shadow-check: advisory mode — not failing the build (pass --strict to gate)." >&2
exit 0
