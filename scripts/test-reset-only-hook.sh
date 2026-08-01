#!/usr/bin/env bash
# Acceptance test for the reset-only production checkout (bead now-lms-xng).
#
# The behavioural claim under test: in a clone marked reset-only, `git commit`
# FAILS. Not warns — fails. That is the whole point, because on 2026-07-31 two
# commits authored on the production box put it 2 ahead of origin and skipped
# the lint gate, and one of them shipped a flake8 error into the running image.
#
# Also pins the guard rails found while writing this: the installer must refuse
# to arm a clone that is not /srv/now-lms without --force, and --remove must
# work REGARDLESS of path (an earlier revision failed that, which would have
# made a mis-forced install unremovable without hand-editing .git/hooks).
#
# Run locally: bash scripts/test-reset-only-hook.sh
# Fork-local; never offered upstream.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="${REPO_ROOT}/scripts/install-vps-reset-only.sh"
[ -f "${INSTALLER}" ] || { echo "cannot find ${INSTALLER}" >&2; exit 1; }

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

git init -q "${TMP}/clone"
cd "${TMP}/clone"
git config user.email test@example.invalid
git config user.name "reset-only test"
mkdir -p scripts
cp "${INSTALLER}" scripts/
chmod +x scripts/install-vps-reset-only.sh
echo base > file.txt
git add -A
git commit -qm base

run() { out="$(bash scripts/install-vps-reset-only.sh "$@" 2>&1)"; rc=$?; }
commit() { echo "$RANDOM" >> file.txt; out="$(git commit -am "attempt" 2>&1)"; rc=$?; }

echo "== a clone that is not /srv/now-lms is not armed by accident =="
run
check "guards on path"        1 "${rc}" "${out}" "not /srv/now-lms"

echo "== --force arms it =="
run --force
check "force installs"        0 "${rc}" "${out}" "is now reset-only"

echo "== the point of the whole exercise: commit FAILS, it does not warn =="
commit
check "commit refused"        1 "${rc}" "${out}" "REFUSING to commit"
check "refusal says how"      1 "${rc}" "${out}" "vps-sync.sh"

echo "== re-arming is idempotent, not an error =="
run --force
check "idempotent"            0 "${rc}" "${out}" "is now reset-only"

echo "== --remove works regardless of path, or a bad --force is unremovable =="
run --remove
check "remove ignores guard"  0 "${rc}" "${out}" "can author commits again"

echo "== authorship really is restored =="
commit
check "commit allowed again"  0 "${rc}" "${out}" "attempt"

echo "== a foreign pre-commit hook is never clobbered =="
printf '#!/bin/sh\nexit 0\n' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
run --force
check "refuses to clobber"    1 "${rc}" "${out}" "already exists and is not ours"

echo
echo "passed=${pass} failed=${fail}"
[ "${fail}" -eq 0 ]
