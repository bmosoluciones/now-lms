#!/bin/bash
# Deploy the current checkout of /srv/now-lms to the running stack — provably.
#
# WHY THIS SCRIPT EXISTS (fork issue #14)
# In July the checkout said one commit, the image was built from another, and the
# theme actually served came from a third state hand-copied into the Docker
# volumes. Nobody could answer "what is deployed?" without hashing files inside
# the container. This script closes all three gaps:
#   1. The image records its commit (BUILD_SHA file + label; the build FAILS
#      without it).
#   2. The volume-shadowed content is refreshed from the freshly built image.
#      NOW_LMS_THEMES_DIR (/app/themes) is Flask's ENTIRE template root and
#      NOW_LMS_DATA_DIR (/app/data) serves all static assets, and the app only
#      populates them when EMPTY (upstream's empty-only guard) — so without this
#      step a rebuild "succeeds" and changes nothing on the site.
#   3. The smoke check (scripts/deploy-smoke.sh) fails the deploy unless the
#      running container, the checkout, and the served bytes all agree.
#
# WHAT THE ABOVE STILL DID NOT ANSWER (bead now-lms-4bt, 2026-07-31)
# All three gaps above compare the checkout to itself. None of them asks whether
# the CHECKOUT matches the REPOSITORY. On 2026-07-31 this box sat 2 commits ahead
# of origin and 1 behind while the smoke check reported SMOKE OK — truthfully,
# because the checkout WAS what was running. Nobody had asked the other question.
# So step 0 below fetches and refuses to deploy a checkout that origin does not
# agree with, and both SHAs are printed so the receipt records repository state
# rather than only local state.
#
# Run ON the VPS, from anywhere: bash /srv/now-lms/scripts/deploy-vps.sh
#   --allow-divergent   deploy anyway, and say so in the receipt. For a genuine
#                       emergency only: it ships code that exists nowhere else.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

ALLOW_DIVERGENT=0
for arg in "$@"; do
    case "${arg}" in
        --allow-divergent) ALLOW_DIVERGENT=1 ;;
        *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
    esac
done

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "REFUSING to deploy: the checkout has uncommitted changes." >&2
    git status --short >&2
    exit 1
fi

# 0. The checkout agrees with the repository.
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "${BRANCH}" = "HEAD" ]; then
    echo "REFUSING to deploy: detached HEAD. There is no origin branch to compare against." >&2
    exit 1
fi
REMOTE_REF="origin/${BRANCH}"

echo "==> Fetching origin to compare the checkout against the repository"
if ! git fetch --quiet origin "${BRANCH}"; then
    echo "REFUSING to deploy: could not fetch origin/${BRANCH}." >&2
    echo "  A deploy that cannot see the repository cannot know whether it is current." >&2
    exit 1
fi

if ! git rev-parse --verify --quiet "${REMOTE_REF}^{commit}" >/dev/null; then
    echo "REFUSING to deploy: ${REMOTE_REF} does not exist. Is this branch pushed?" >&2
    exit 1
fi

BUILD_SHA="$(git rev-parse HEAD)"
ORIGIN_SHA="$(git rev-parse "${REMOTE_REF}")"
REPO_ROOT="$(pwd)"
# Three dots, not two: "A...B" is the SYMMETRIC difference, so --left-right --count
# prints "<commits only in A> <commits only in B>" -- i.e. ahead and behind in one
# call. "A..B" would give only one side and could not tell divergence from being
# merely behind.
read -r AHEAD BEHIND <<<"$(git rev-list --left-right --count "HEAD...${REMOTE_REF}")"

if [ "${AHEAD}" -ne 0 ] || [ "${BEHIND}" -ne 0 ]; then
    {
        echo "REFUSING to deploy: the checkout has diverged from ${REMOTE_REF}."
        echo "  checkout HEAD    ${BUILD_SHA}"
        echo "  ${REMOTE_REF}    ${ORIGIN_SHA}"
        echo "  ${AHEAD} commit(s) here and not on origin, ${BEHIND} commit(s) on origin and not here."
        echo
        if [ "${AHEAD}" -ne 0 ]; then
            echo "  ${AHEAD} local commit(s) exist NOWHERE ELSE. Deploying them would put code"
            echo "  into production that no PR reviewed and no other clone can reproduce."
            echo "  Push them, or reset to origin — see ops/ for the reset-only policy."
        fi
        if [ "${BEHIND}" -ne 0 ]; then
            echo "  Deploying now would ship code ${BEHIND} commit(s) stale. Run:"
            echo "      git -C \"${REPO_ROOT}\" fetch origin && git -C \"${REPO_ROOT}\" reset --hard \"${REMOTE_REF}\""
        fi
        echo
        echo "  Override with --allow-divergent only if you accept shipping unreproducible code."
    } >&2
    [ "${ALLOW_DIVERGENT}" -eq 1 ] || exit 1
    echo "==> --allow-divergent given; continuing with a DIVERGENT checkout." >&2
fi

export BUILD_SHA ORIGIN_SHA
if [ "${BUILD_SHA}" = "${ORIGIN_SHA}" ]; then
    echo "==> Deploying ${BUILD_SHA} ($(git log --format=%s -1))"
    echo "    in sync with ${REMOTE_REF}"
else
    echo "==> Deploying ${BUILD_SHA} ($(git log --format=%s -1))"
    echo "    DIVERGENT from ${REMOTE_REF} at ${ORIGIN_SHA} (+${AHEAD}/-${BEHIND})"
fi

echo "==> Building image (fails if BUILD_SHA were unset — that is the point)"
docker compose build app

echo "==> Starting stack"
docker compose up -d

echo "==> Waiting for the app container to be healthy"
for _ in $(seq 1 30); do
    state="$(docker inspect --format '{{.State.Health.Status}}' now-lms-app-1 2>/dev/null || echo starting)"
    [ "${state}" = "healthy" ] && break
    sleep 5
done

echo "==> Refreshing volume-shadowed templates and static assets from the image"
# cp -a source/. dest/ merges: files present in the image overwrite their stale
# volume copies; anything ONLY in the volume (user uploads under /app/data, e.g.
# files/public) is left untouched — same semantics as upstream's
# copytree(dirs_exist_ok=True), minus the empty-only guard that caused the trap.
docker compose exec -T app sh -c 'cp -a /app/now_lms/templates/. /app/themes/ && cp -a /app/now_lms/static/. /app/data/'

echo "==> Restarting app so Jinja/caches pick up the refreshed templates"
docker compose restart app

echo "==> Waiting for healthy after restart"
for _ in $(seq 1 30); do
    state="$(docker inspect --format '{{.State.Health.Status}}' now-lms-app-1 2>/dev/null || echo starting)"
    [ "${state}" = "healthy" ] && break
    sleep 5
done

echo "==> Smoke check"
bash scripts/deploy-smoke.sh

# AFTER the smoke check, and non-fatal. This is cosmetic cleanup; the smoke check is
# the deploy's only proof that the running container, the checkout and the served bytes
# agree. Run above it under `set -euo pipefail`, any non-zero exit here — a lock fight
# with live traffic, an OperationalError, a schema lag — aborts the deploy BEFORE that
# proof runs, while the new image is already serving. The operator would get a failure
# about demo content and no verification at all.
echo "==> Removing upstream demo content (idempotent; refuses anything in use)"
docker compose exec -T app /usr/bin/python3.12 scripts/seed_practice_tracks.py --only-remove-demo \
    || echo "WARN: demo-content cleanup failed; the deploy itself is verified and stands"

if [ "${BUILD_SHA}" = "${ORIGIN_SHA}" ]; then
    echo "==> Deploy of ${BUILD_SHA} verified (== ${REMOTE_REF})."
else
    echo "==> Deploy of ${BUILD_SHA} verified, but DIVERGENT from ${REMOTE_REF} (${ORIGIN_SHA})."
fi
