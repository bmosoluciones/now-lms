# Founding-members beta provisioned on production — 2026-07-28 (executed from intent-os)

**Read this before touching prod accounts, enrollment tables, or mail config.**
The provisioning this platform was waiting for happened tonight — executed from the
**intent-os** session (owner order). This record is the now-lms side of the audit
trail, **redacted for the public repo**; the full evidence — member roster, named
operators, per-member delivery status, and host-level configuration detail — lives in
the private intent-os repo (PRs #269/#271/#272, cluster issue
intent-solutions-io/intent-os#270, bead epic `spine-e4j`).

## What is now live on prod

- **The owner-approved founding-member roster is provisioned** through the app's own
  ORM (in-container, mirrors `vistas/users.py::crear_usuario` exactly), including a
  small owner-designated admin group. Enrollment covers both launch courses, with
  per-resource `curso_recurso_avance` rows seeded per member — the bulk-enroll caveat
  handled member-owned, not actor-owned.
- **Owner login test passed** (panel + both courses visible). A rollback path exists
  and was rehearsed for the created-user path.
- **A weekly progress digest** runs on a schedule from estate infrastructure to the
  owner + course leads. Registered in intent-os `mission-control/automations.md`.

## Standing constraints for this repo's sessions

1. **Do not create/modify accounts or enrollments ad hoc** — the estate provisioning
   tool (see the private intent-os record) is the sanctioned path. Route new-member
   adds through it.
2. **LMS mail stays unconfigured.** All member email goes via the estate sender. Do
   not wire `MAIL_*` until the mail lane decides.
3. **Self-registration is closed at the ingress layer**, in host-level configuration
   that is *not* in this repo. Do not regenerate or hand-edit host ingress config for
   this site without reading the private intent-os ops record first — an uninformed
   regen can silently reopen it. `/user/login` must stay reachable.
4. **Members hold live credentials** — schema migrations / redeploys of the container
   are fine (accounts are DB rows), but anything touching `usuario`,
   `estudiante_curso`, `curso_recurso_avance`, or the launch course codes now has a
   full-cohort blast radius. Coordinate via `~/000-projects/CROSS-SESSION-LOG.md`.

## Mail context (matters until the MX cutover completes)

The estate mail provider is mid-cutover; delivery routing for the org domain is
transitional until the MX flip lands. Per-member delivery status and the exceptions
list are recorded in the private intent-os record — do not assume every member has
seen their credentials until that record says so.

- Jeremy Longshore
intentsolutions.io
