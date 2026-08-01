#!/usr/bin/env bash
# Bring the production checkout up to origin. The ONLY sanctioned way to change
# what /srv/now-lms contains (bead now-lms-xng).
#
# WHY RESET AND NOT PULL
# /srv/now-lms is reset-only: it may hold no commit that origin does not have.
# On 2026-07-31 two commits authored on this box put production 2 ahead of
# origin, and because the box has no pre-commit hook they also skipped the lint
# gate — which is exactly how a flake8 E303/E302 error in cache.py reached both
# origin and the running image. `git pull` would preserve such commits by
# merging them; `git reset --hard` is the operation that matches the policy.
#
# WHAT THIS WILL AND WILL NOT DESTROY
#   Discarded: local commits, and modifications to TRACKED files.
#   Preserved: untracked and git-ignored files — .env, docker-compose overrides,
#              *.bak, anything the deploy needs that is not in the repo. A hard
#              reset does not touch them, deliberately.
#
# Run ON the VPS: bash /srv/now-lms/scripts/vps-sync.sh
#   --discard-local   proceed even though tracked files are modified locally
#
# Fork-local (production operations); never offered upstream.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

DISCARD_LOCAL=0
for arg in "$@"; do
    case "${arg}" in
        --discard-local) DISCARD_LOCAL=1 ;;
        *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "${BRANCH}" = "HEAD" ]; then
    echo "REFUSING: detached HEAD. Check out the deploy branch first." >&2
    exit 1
fi
REMOTE_REF="origin/${BRANCH}"

if ! git diff --quiet || ! git diff --cached --quiet; then
    if [ "${DISCARD_LOCAL}" -eq 0 ]; then
        {
            echo "REFUSING: tracked files are modified in the checkout."
            echo "  A reset would discard these edits, and on a production box that is"
            echo "  usually someone's in-flight hotfix rather than junk. Look first:"
            git status --short
            echo
            echo "  Re-run with --discard-local once you are sure they are disposable."
        } >&2
        exit 1
    fi
    echo "==> --discard-local given; the following local edits will be destroyed:" >&2
    git status --short >&2
fi

echo "==> Fetching ${REMOTE_REF}"
git fetch --quiet origin "${BRANCH}"

if ! git rev-parse --verify --quiet "${REMOTE_REF}^{commit}" >/dev/null; then
    echo "REFUSING: ${REMOTE_REF} does not exist." >&2
    exit 1
fi

BEFORE="$(git rev-parse HEAD)"
AFTER="$(git rev-parse "${REMOTE_REF}")"

if [ "${BEFORE}" = "${AFTER}" ]; then
    echo "==> Already at ${AFTER} — nothing to sync."
    exit 0
fi

# Three dots: "A...B" is the symmetric difference, so --left-right --count prints
# "<only in A> <only in B>" — ahead and behind from one call.
read -r AHEAD BEHIND <<<"$(git rev-list --left-right --count "HEAD...${REMOTE_REF}")"
if [ "${AHEAD}" -ne 0 ]; then
    echo "==> WARNING: ${AHEAD} commit(s) exist only on this box and are about to be DESTROYED:" >&2
    git log --oneline "${REMOTE_REF}..HEAD" >&2
    echo "    If any of that matters, push it to a branch before continuing." >&2
    # Single-quoted on purpose: the operator should run date(1) when they run the
    # command, not inherit a timestamp from when this warning was printed.
    # -C so the line works pasted from anywhere, matching deploy-vps.sh's remedy.
    # Single-quoted tail on purpose: date(1) must run when the operator runs the
    # command, not when this warning was printed.
    echo "        git -C \"$(pwd)\" push origin "'HEAD:refs/heads/rescue/$(date +%Y%m%d-%H%M%S)' >&2
    echo >&2
fi

echo "==> Incoming (${BEHIND} commit(s)):"
git log --oneline "HEAD..${REMOTE_REF}" | sed 's/^/    /'

git reset --hard "${AFTER}"

echo "==> Synced ${BEFORE} -> ${AFTER} (${REMOTE_REF})"
echo "    Untracked and ignored files (.env, overrides, backups) were left alone."
echo "    Deploy it with: bash scripts/deploy-vps.sh"
