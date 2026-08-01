#!/usr/bin/env bash
# Make this clone reset-only: it may receive commits from origin, but it may not
# author them. Install once on the production box (bead now-lms-xng).
#
# WHY
# /srv/now-lms is not a development clone, but git cannot tell the difference. On
# 2026-07-31 two commits were authored there. Both skipped the repo's lint gate,
# because scripts/install-git-hooks.sh installs that gate into .beads/hooks and
# the production box has no beads workspace — `core.hooksPath` is unset there and
# `.git/hooks/pre-commit` did not exist. One of those commits carried a flake8
# E303/E302 error that reached origin AND the running image.
#
# WHY NOT JUST INSTALL THE LINT HOOK THERE
# Because linting production commits still leaves production holding commits that
# exist nowhere else — unreviewed, unreproducible, and invisible to every clone.
# The failure mode worth removing is authorship, not bad formatting.
#
# WHY THE CHECKOUT STAYS AT ALL
# It is load-bearing: docker-compose.yml declares `build: context: .`, so the
# image is COMPILED on the box from this checkout, and BUILD_SHA comes from
# `git rev-parse HEAD` (the build fails without it). .env and the compose file
# live here too. Git stays; only authorship goes.
#
# HONEST LIMIT: `git commit --no-verify` still bypasses this hook. That is fine.
# This stops the accident; scripts/deploy-vps.sh stops the consequence, because
# it refuses to deploy a checkout that has diverged from origin however the
# divergence got there. Defence in depth, not a wall.
#
# Usage, ON the VPS:  bash /srv/now-lms/scripts/install-vps-reset-only.sh
#   --force   install into a clone that is not /srv/now-lms (say, a staging box)
#   --remove  take it back off
#
# Fork-local (production operations); never offered upstream.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
ROOT="$(git rev-parse --show-toplevel)"

FORCE=0
REMOVE=0
for arg in "$@"; do
    case "${arg}" in
        --force) FORCE=1 ;;
        --remove) REMOVE=1 ;;
        *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

# The path guard deliberately does NOT apply to --remove: taking the hook back
# off must always work, or a --force install into the wrong clone would be
# unremovable without hand-editing .git/hooks.
if [ "${REMOVE}" -eq 0 ] && [ "${ROOT}" != "/srv/now-lms" ] && [ "${FORCE}" -eq 0 ]; then
    {
        echo "REFUSING: this clone is ${ROOT}, not /srv/now-lms."
        echo "  Installing here would block commits in what looks like a development"
        echo "  clone. If you really mean it (a staging box, say), pass --force."
    } >&2
    exit 1
fi

# The production box has no beads workspace, so core.hooksPath is unset and
# .git/hooks is live. If that ever changes, honour the configured path instead of
# writing a hook git will ignore.
#
# `git rev-parse --git-path hooks` already accounts for core.hooksPath, including
# relative values, which git resolves against the current directory rather than
# the repo root. Doing the arithmetic by hand here got it wrong for values like
# `../hooks` (Kilo, PR #59) — so let git answer, and only fall back to manual
# construction if it somehow returns nothing.
HOOKS_DIR="$(git rev-parse --git-path hooks 2>/dev/null || true)"
[ -n "${HOOKS_DIR}" ] || HOOKS_DIR="${ROOT}/.git/hooks"
case "${HOOKS_DIR}" in
    /*) ;;
    *) HOOKS_DIR="${ROOT}/${HOOKS_DIR}" ;;
esac
HOOK="${HOOKS_DIR}/pre-commit"

if [ "${REMOVE}" -eq 1 ]; then
    if [ -f "${HOOK}" ] && grep -q 'reset-only checkout' "${HOOK}"; then
        rm -f "${HOOK}"
        echo "removed: ${HOOK} — this clone can author commits again."
    else
        echo "nothing to remove: ${HOOK} is not the reset-only hook."
    fi
    exit 0
fi

if [ -f "${HOOK}" ] && ! grep -q 'reset-only checkout' "${HOOK}"; then
    {
        echo "REFUSING: ${HOOK} already exists and is not ours."
        echo "  Refusing to clobber someone else's hook. Inspect it, then move it aside."
    } >&2
    exit 1
fi

mkdir -p "${HOOKS_DIR}"
cat >"${HOOK}" <<'EOF'
#!/bin/sh
# Installed by scripts/install-vps-reset-only.sh. Do not edit by hand.
# This is a reset-only checkout: it takes commits FROM origin and authors none.
cat >&2 <<'MSG'

REFUSING to commit: this is a reset-only production checkout.

Production holds no commit that origin does not have. A commit made here would
exist nowhere else -- no PR reviewed it, no other clone can reproduce it, and
the lint gate that runs on a development clone does not run here.

To change what production runs:
  1. Commit the change on a development clone, open a PR, let CI check it.
  2. Merge it.
  3. On this box:  bash /srv/now-lms/scripts/vps-sync.sh
  4. Deploy it:    bash /srv/now-lms/scripts/deploy-vps.sh

If you are mid-incident and genuinely cannot wait, the honest move is to make
the change, push it to a rescue branch, and open the PR after -- not to leave an
unreproducible commit on the production box.

Policy: bead now-lms-xng. Remove with scripts/install-vps-reset-only.sh --remove.

MSG
exit 1
EOF
chmod +x "${HOOK}"

echo "installed: ${HOOK}"
echo "  ${ROOT} is now reset-only. Update it with scripts/vps-sync.sh."
