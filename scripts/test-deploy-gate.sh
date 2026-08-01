#!/usr/bin/env bash
# Acceptance test for the deploy-vps.sh repository-divergence gate (bead now-lms-4bt).
#
# WHY THIS TEST EXISTS
# On 2026-07-31 /srv/now-lms sat 2 commits ahead of origin and 1 behind while the
# deploy reported SMOKE OK. The smoke check was not lying — the checkout WAS what
# was running. It simply had no opinion about whether the checkout matched the
# repository. deploy-vps.sh now refuses that state; this test is what stops the
# refusal from being quietly weakened later.
#
# The interesting assertion is BEHAVIOURAL, not cosmetic: a deliberately diverged
# checkout must make the script EXIT NON-ZERO, not deploy-and-warn.
#
# Builds a throwaway origin + clone in a tempdir and drives every state the gate
# must distinguish. Everything downstream of the gate (docker build, compose up,
# smoke) is stubbed on PATH, so this exercises the gate and nothing else — no
# network, no docker, no side effects on the real checkout.
#
# Run locally: bash scripts/test-deploy-gate.sh
# Fork-local; never offered upstream (deploy-vps.sh is fork-only).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATE="${REPO_ROOT}/scripts/deploy-vps.sh"
[ -f "${GATE}" ] || { echo "cannot find ${GATE}" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

pass=0
fail=0
check() { # check <name> <want-exit> <got-exit> <output> <must-contain>
    local name="$1" want="$2" got="$3" out="$4" needle="$5"
    if [ "${got}" = "${want}" ] && grep -q "${needle}" <<<"${out}"; then
        echo "  PASS  ${name}"
        pass=$((pass + 1))
    else
        echo "  FAIL  ${name} (exit want=${want} got=${got}; expected output to contain '${needle}')"
        sed 's/^/          | /' <<<"${out}"
        fail=$((fail + 1))
    fi
}

# A throwaway origin carrying one commit on the deploy branch name.
git init -q --bare "${TMP}/origin.git"
git clone -q "${TMP}/origin.git" "${TMP}/seed" 2>/dev/null
cd "${TMP}/seed"
git config user.email test@example.invalid
git config user.name "deploy gate test"
echo base > file.txt
git add -A
git commit -qm base
git branch -M deploy/now-lms-fixed
git push -q origin deploy/now-lms-fixed

# The checkout under test, standing in for /srv/now-lms.
git clone -q -b deploy/now-lms-fixed "${TMP}/origin.git" "${TMP}/checkout"
cd "${TMP}/checkout"
git config user.email test@example.invalid
git config user.name "deploy gate test"
mkdir -p scripts
cp "${GATE}" scripts/
printf '#!/bin/bash\nexit 0\n' > scripts/deploy-smoke.sh
mkdir -p "${TMP}/bin"
printf '#!/bin/bash\nif [ "${1:-}" = inspect ]; then echo healthy; fi\nexit 0\n' > "${TMP}/bin/docker"
chmod +x "${TMP}/bin/docker" scripts/deploy-smoke.sh
export PATH="${TMP}/bin:${PATH}"

run() { out="$(bash scripts/deploy-vps.sh "$@" 2>&1)"; rc=$?; }

echo "== a checkout in sync with origin deploys =="
run
check "in-sync deploys"           0 "${rc}" "${out}" "in sync with origin/deploy/now-lms-fixed"

echo "== a checkout AHEAD of origin is refused (this is the 2026-07-31 state) =="
echo local-only >> file.txt
git commit -qam "a commit that exists nowhere else"
run
check "ahead refuses"             1 "${rc}" "${out}" "REFUSING to deploy: the checkout has diverged"
check "ahead names the danger"    1 "${rc}" "${out}" "exist NOWHERE ELSE"
check "ahead reports origin too"  1 "${rc}" "${out}" "origin/deploy/now-lms-fixed"

echo "== --allow-divergent overrides, and taints the receipt =="
run --allow-divergent
check "override proceeds"         0 "${rc}" "${out}" "continuing with a DIVERGENT checkout"
check "override taints receipt"   0 "${rc}" "${out}" "DIVERGENT from origin/deploy/now-lms-fixed"

echo "== a checkout BEHIND origin is refused (it would ship stale code) =="
git reset -q --hard origin/deploy/now-lms-fixed
(cd "${TMP}/seed" && echo newer >> file.txt && git commit -qam newer && git push -q origin deploy/now-lms-fixed)
run
check "behind refuses"            1 "${rc}" "${out}" "1 commit(s) on origin and not here"
check "behind prints the remedy"  1 "${rc}" "${out}" "reset --hard"

echo "== an unknown argument stops the deploy rather than being ignored =="
run --yolo
check "bad arg rejected"          2 "${rc}" "${out}" "unknown argument"

echo "== a detached HEAD is refused: there is no origin branch to compare =="
git checkout -q --detach HEAD
run
check "detached refuses"          1 "${rc}" "${out}" "detached HEAD"

echo
echo "passed=${pass} failed=${fail}"
[ "${fail}" -eq 0 ]
