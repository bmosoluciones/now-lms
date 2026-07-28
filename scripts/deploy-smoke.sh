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

# The access CTA lands on the stored intake, not the raw mailto (which moved to
# /request-access as the secondary path).
grep -q 'href="/request-access"' <<<"${page}" || fail "front door has no /request-access CTA"

# The volume refresh actually landed: the served page must carry a marker that
# exists only in the checked-out template, not in the stale volume copy.
grep -q 'embedded_badge' <<<"${page}" || fail "Credly badge missing — volume-shadowed template still serving"

# No CDN scripts (the no-CDN rule, enforced at serve time too).
if grep -Eq 'unpkg\.com|cdn\.jsdelivr\.net' <<<"${page}"; then
    fail "a third-party CDN reference is being served"
fi

# 4. The intake serves anonymously, and its secondary mailto carries a literal @
#    (RFC 6068; the %40 form was the live bug that motivated the old check).
ra="$(curl -fsS --max-time 20 -H 'X-Forwarded-Proto: https' http://127.0.0.1:8080/request-access)" \
    || fail "/request-access did not serve — a sync deploy must not pass without the intake"
grep -q 'isl-ra-form' <<<"${ra}" || fail "/request-access did not render the intake form"
grep -qo 'mailto:[^"]*' <<<"${ra}" || fail "no secondary mailto: link on /request-access"
if grep -o 'mailto:[^"?]*' <<<"${ra}" | grep -q '%40'; then
    fail "mailto address is still percent-encoded (%40)"
fi

# The Slack ping is optional by env contract, but on THIS deployment it must be
# wired: an unset var silently drops the alert path for real leads.
webhook="$(docker compose exec -T app printenv SLACK_WEBHOOK_LEADS_CONTACT 2>/dev/null || true)"
[ -n "${webhook}" ] || fail "SLACK_WEBHOOK_LEADS_CONTACT is empty inside the app container"

# 5. The catalog is the doctrine teaser: no course cards, no vendor names.
teaser="$(curl -fsS --max-time 20 -H 'X-Forwarded-Proto: https' http://127.0.0.1:8080/course/explore)"
grep -q 'isl-tracks-list' <<<"${teaser}" || fail "/course/explore is not serving the practice-tracks teaser"
if grep -Eq 'isl-course-grid|CCA-|Claude|Anthropic' <<<"${teaser}"; then
    fail "/course/explore is leaking course cards or vendor names to the public"
fi

# 6. The contact zombie stays dead while enable_contact is off in settings.
contact_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -H 'X-Forwarded-Proto: https' http://127.0.0.1:8080/contact)"
[ "${contact_code}" = "404" ] || fail "/contact returned ${contact_code}, expected 404 (enable_contact is off)"

# 7. Every gated course redirects anonymous visitors to the intake.
for code in CCA-A CCA-B CCA-F free IS-START now postgresql python resources details lms-training; do
    course_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 -H 'X-Forwarded-Proto: https' "http://127.0.0.1:8080/course/${code}/view")"
    case "${course_code}" in
        302) : ;;
        404) : ;;  # course absent on this deploy — absence also does not leak
        *) fail "/course/${code}/view returned ${course_code} anonymously, expected 302 to the intake" ;;
    esac
done

echo "SMOKE OK: ${want} is built, running, healthy, and serving its own bytes."
