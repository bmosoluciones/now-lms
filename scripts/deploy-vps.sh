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
# Run ON the VPS, from anywhere: bash /srv/now-lms/scripts/deploy-vps.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "REFUSING to deploy: the checkout has uncommitted changes." >&2
    git status --short >&2
    exit 1
fi

BUILD_SHA="$(git rev-parse HEAD)"
export BUILD_SHA
echo "==> Deploying ${BUILD_SHA} ($(git log --format=%s -1))"

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

echo "==> Deploy of ${BUILD_SHA} verified."
