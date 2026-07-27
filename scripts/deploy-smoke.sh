#!/bin/bash
# Refuse to call a deploy successful unless the running container, the checkout,
# and the bytes actually served all agree. Fork issue #14: this is the check that
# would have caught the July three-way drift on the day it happened.
#
# Run ON the VPS: bash /srv/now-lms/scripts/deploy-smoke.sh
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail() { echo "SMOKE FAIL: $*" >&2; exit 1; }

# 1. The image knows which commit it is, and it matches the checkout.
want="$(git rev-parse HEAD)"
got="$(docker compose exec -T app cat /app/BUILD_SHA 2>/dev/null || true)"
[ -n "${got}" ] || fail "container has no /app/BUILD_SHA — image predates the provable-deploy work"
[ "${want}" = "${got}" ] || fail "running container is ${got} but the checkout is ${want}"

# 2. The container is healthy.
state="$(docker inspect --format '{{.State.Health.Status}}' now-lms-app-1)"
[ "${state}" = "healthy" ] || fail "app container is ${state}, not healthy"

# 3. The served bytes match the checkout — assert on markers the current commit
#    guarantees, fetched through the same loopback+header path Caddy uses.
page="$(curl -fsS --max-time 20 -H 'X-Forwarded-Proto: https' http://127.0.0.1:8080/)"

# Front door renders at all.
grep -q 'isl-hero-copy' <<<"${page}" || fail "front door did not render (no isl-hero-copy)"

# The access-request address carries a literal @ (RFC 6068); the %40 form was the
# live bug that motivated all of this.
grep -qo 'mailto:[^"]*' <<<"${page}" || fail "no mailto: link on the front door"
if grep -o 'mailto:[^"?]*' <<<"${page}" | grep -q '%40'; then
    fail "mailto address is still percent-encoded (%40)"
fi

# The volume refresh actually landed: the served page must carry a marker that
# exists only in the checked-out template, not in the stale volume copy.
grep -q 'embedded_badge' <<<"${page}" || fail "Credly badge missing — volume-shadowed template still serving"

# No CDN scripts (the no-CDN rule, enforced at serve time too).
if grep -Eq 'unpkg\.com|cdn\.jsdelivr\.net' <<<"${page}"; then
    fail "a third-party CDN reference is being served"
fi

echo "SMOKE OK: ${want} is built, running, healthy, and serving its own bytes."
