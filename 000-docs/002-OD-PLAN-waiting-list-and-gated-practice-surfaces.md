# Waiting list + gated practice surfaces — doctrine-aligned public site

> Execution plan, locked 2026-07-27 (Jeremy). Built on branch `feat/request-access`.
> The superseded bespoke design (original §A) is preserved in Appendix A so nobody
> builds the dead design. Copy and decisions in this document are founder-approved
> word-by-word; do not rephrase public-surface copy without a new approval.

## Context

The landing page is doctrine-perfect and stays untouched. But one click deeper breaks the
model: the public catalog (`/course/explore`) lists vendor-named courses plus demo junk to
anonymous visitors, course detail pages render fully without login, and `/contact` is a
zombie — disabled in settings yet still serving a generic off-brand form whose submissions
go nowhere (mail was never configured; neither fork nor upstream honors `enable_contact`
in the route).

Jeremy's direction (2026-07-27): courses get **gated**; the click-deeper pages get
**descriptive doctrine-voice copy** about what's inside instead of course listings; and
instead of killing the contact path, people must be able to **join a waiting list** —
stored durably, **pinged to the existing Slack contact-form channel**, and presented on the
site "in a polished, casual manner." All public vocabulary comes from the practice doctrine
(`claude-partner-network/000-docs/007-PP-PLAN`), translated by a marketing-copy pass that
Jeremy reviewed word-by-word. Inside the login gate, language rules relax ("speak
freely"); the doctrine governs only public surfaces.

## Governing rule (native-first)

`learning-platform/DECISION-now-lms-adopt-and-mature.md` (Jeremy, 2026-07-21):
**"Use the native features as they ship. Gaps → upstream contributions (maturing the
project), never bespoke one-offs. 'I'm not building custom' is the governing rule."**

The platform already ships the native machinery: contact submissions store to
`contact_messages` (status workflow, admin notes) with a complete admin surface at
`/admin/contact-messages` + dashboard unseen-badge. So the build is native-first:

- **Storage: the native `ContactMessage` table as-is.** Access requests store with an
  ASCII discriminator subject prefix `[ACCESS] ` (never gettext-wrapped, name truncated
  to fit `String(200)`); the vetting fields (links / building / role / source) compose
  into `message` in a fixed labeled template, trivially parseable. Canonical query:
  `WHERE subject LIKE '[ACCESS] %'`.
- **Route: one thin fork route** (`/request-access`) in a NEW file
  `now_lms/vistas/request_access.py` (zero imports from `static_pages.py`, which dies at
  the v2.0.0 sync) that renders the themed page and on POST writes a `ContactMessage` +
  fires the Slack webhook. The *model*, *admin*, and *status workflow* are all native;
  only presentation + the ping are ours. No new table, **no migration at all**.
- **Upstream contributions (the real fix, the #214–#217 lane):** see the upstream PR
  queue below. Once the generic webhook feature merges upstream, the fork's ping code
  is dropped.

## Architecture

### B. Public catalog becomes a "practice tracks" teaser (theme-only)

- `overrides/course_list.j2` (ours): `/course/explore` serves the doctrine-voice tracks
  page to **everyone** (members' real course grid would be empty anyway —
  `_course_explore_query` filters `publico` with no auth branch, `courses/base.py:172`).
  Three role-shaped track descriptions + house-core note + the locked honesty sentence +
  request-access CTA — **no course names, no vendor names**. Authenticated visitors get a
  "your courses live in your panel" line; members' real path = dashboard +
  `/course/<code>/view` (enrollment check at `_check_course_access` keeps their access).
- Course detail pages: anonymous GET on a gated course 302s to `/request-access`
  (the visitor most primed to convert), not a bare 403. Authenticated-without-enrollment
  keeps 403.

### C. Contact zombie fixed

- Fork: `static_pages.contact` route gets the `enable_contact` check → 404 while
  disabled. (This fork file dies at the v2.0.0 sync anyway — upstream split it into
  `contact.py` — so the edit is deliberately disposable.)
- The same flag-not-honored bug exists in upstream `contact.py`; offered upstream (U1).
- Landing "Request access" buttons (nav, hero, final CTA) point to `/request-access`
  instead of the raw `mailto:`. The mailto (`hello@intentsolutions.io`) remains offered
  on the request-access page as a secondary "prefer email?" path.
- Footer fallback contact link (ungated in `footer.j2`) points at `/request-access` so
  the 404 fix doesn't put a dead link in every page's footer.

### D. Gate the courses (data change, reversible, executed at deploy)

```sql
UPDATE curso SET publico=false WHERE codigo IN
  ('CCA-A','CCA-B','CCA-F','free','IS-START','now','postgresql','python','resources','details','lms-training');
UPDATE curso_recurso SET publico=false;   -- free-preview resources leak the outline otherwise
UPDATE programa SET publico=false;
```

Rollback = same statements with `true`, scoped to the pre-flip `true` set (recorded at
execution). Verify the CCA seed script's idempotency guard so a reseed can't resurrect
`publico=true`. Members access courses via enrollment/dashboard (admin-enrolled —
matches invite-only).

### E. Visual alignment of deeper pages

Bring `overrides/course_list.j2` styling up to the 07-23 landing composition (paper
tokens, hairlines, no radius, kicker typography) so clicking deeper no longer changes
design language. CSS additions live in the `front-door.css` namespace.

## Copy (LOCKED — Jeremy approved 2026-07-27)

### Request Access page (`/request-access`)

- **Title:** Request Access
- **Intro (soft review promise):** "Show us one system you've shipped and where you want
  sharper production judgment. A person reads every request. When the room has space, we
  reach out — until then your request holds its place on the waiting list."
- **Waiting-list line:** "Admissions run in small waves. If the room is full, your
  request joins the waiting list and holds its place — we'll reach out when a seat
  opens."
- **Form fields:** Your name (req) · Email (req) · Links to your work (req, one per
  line) · What are you building? Where do you want sharper production judgment? (req) ·
  Current role or company (opt) · How did you find us? (opt)
- **Button:** "Request access"
- **Post-submit:** "Got it — you're on the list. A person reads every request; no
  timelines promised, because fit beats speed. If email suits you better:
  hello@intentsolutions.io."
- **Privacy line:** "We store what you submit and use it only to review your request."
  (links the Privacy Policy)

### Practice Tracks page (`/course/explore`)

- **Kicker:** Inside the practice · **Headline:** One practice. Several ways to prove it.
- **Intro:** "Everyone shares the Intent Solutions house core — systems thinking, agentic
  delivery, evaluation, governance, production operations, peer review. From there,
  members pursue role-shaped practice. Credentials are optional proof paths within the
  tracks, not the membership itself."
- **Tracks:** Production architecture · Agent building & orchestration · Evaluation &
  governance (descriptions as shipped in the template).
- **House-core note:** "All members begin with the shared house core, regardless of
  track. The house method travels with you."
- **Credentials note:** "Proof paths can include credentials — shipping well remains a
  first-class path."
- **Honesty sentence (founder-approved doctrine amendment, DECISION 2):** "Some members
  are invited onto client work that comes through Intent Solutions. That invitation is
  earned, not sold."
- **CTA:** "Request access →" (links `/request-access`)

## DECISIONS LOCKED (Jeremy, 2026-07-27)

1. **Review promise: SOFT version.** No member-hours committed. The full "Review"
   service is a future upgrade, gated on a dedicated session.
2. **Honesty line: SOFT sentence, on the tracks page** (text above). This is a
   founder-approved amendment to the doctrine's "never the homepage" clause; 007 gets a
   one-line addendum (pre-deploy blocker bead — it transcribes a decision already locked
   here with date + quote; needs no session).
3. **Panel follow-ups (patterns / write-ups / ritual / shepherd month): each gets its
   own dedicated session with Jeremy — DO NOT build any of them from this plan.** One
   bead files the agenda; nothing else is created.

## Slack wiring (verified)

- Channel `#leads-contact` (private, intent-solutions-io workspace), already receiving
  `intentsolutions.io` contact-form pings from the VPS `forms-api` service. Env name:
  `SLACK_WEBHOOK_LEADS_CONTACT` — SOPS source of truth
  `intent-os/ops/host/secrets/secrets.prod.sops.yaml` (`slack_webhook_leads_contact`),
  materialized on the VPS at `/etc/intentsolutions/notify.env`.
- Mechanism: direct webhook POST from Flask after the DB commit, short timeout, inside
  try/except — Slack down never breaks a submission; the DB row is the durability.
  Optional env: ping skipped with a log warning if unset (deploys must not fail on a
  notification var). Value flows into `/srv/now-lms/.env` at deploy.
- Ping hardening: Block Kit `plain_text`, `unfurl_links: false`, no `<!channel>`, sends
  name + snippet + admin deep-link — NOT the applicant's email/employer.
- Rejected: relaying through forms-api (loopback bind, 3/hour/IP rate limit shared
  across one egress IP, schema can't carry vetting fields).
- Flagged to the SOPS-cutover owner: this adds a second consumer of the VPS plaintext
  `notify.env`.

## Security ship-gate (all P0 adopted)

1. **Real rate limiter** on `POST /request-access` (the repo's own `check_rate_limit` is
   a silent no-op under NullCache) + a Caddy `rate_limit` outer wall at deploy.
2. **Autoescaping**: the new page is `request_access.html` (not `.j2` — `.j2` templates
   are NOT autoescaped).
3. **CSRF** emitted in the form; test runs with `WTF_CSRF_ENABLED=True` (the TESTING
   default makes a naive test vacuous).
4. **Length caps before insert** — `[ACCESS] <name>` truncated to `String(200)`; every
   field capped server-side; email format validation + CRLF strip.
5. **`curso_recurso.publico` flips in the same deploy SQL** (free-preview resources
   render the outline to anon with zero regard for `Curso.publico`).
6. **`/course/slide_show/<id>` has no access check** — accepted in deploy SQL scope; the
   route guard is the upstream fix (U8).
7. Honeypot + signed-timestamp min-time-to-submit.
8. `SESSION_COOKIE_SECURE` in compose; confirm whether self-registration (`/user/logon`)
   is enabled in prod config before deploy.
9. P1 at deploy: Caddy deny-matchers for gated-code asset paths
   (`/static/files/public/images/<code>/…`, `/_uploads/*`); certificate-lookup
   disclosure → upstream (U9), P1 if any CCA certs issued.

## Upstream PR queue

| # | PR | Type |
|---|---|---|
| U1 | `contact` route honors `enable_contact` (404 when disabled) | bug |
| U2 | Webhook-notify on new contact message (generic `CONTACT_WEBHOOK_URL`, best-effort POST) | feature |
| U3 | Re-offer the lost fresh-PostgreSQL bootstrap fix (branch `ecc85d5`, rebased) | bug |
| U4 | `MAIL_USE_TLS`/`MAIL_USE_SSL` dead `match` arms — boolean coercion | bug |
| U5 | `_()` → `_l()` on ~83 WTForms labels (import-time locale freeze) | bug |
| U6 | Remove dead ionicons CDN loads from 9 bundled themes | cleanup |
| U7 | Resource free-preview gate ignores `Curso.publico` | **security bug** |
| U8 | `/course/slide_show/<id>` has no authorization check | **security bug** |
| U9 | Certificate lookup discloses student + course names, no auth, 7 routes | **security bug** |
| U10 | View-cache key ignores user identity (`auth|anon` only) | **security bug** |

U7–U10 jump the queue — responsible disclosure to the maintainer first (private
heads-up, then the PRs). Rules: one PR per fix, regression test each,
`dev/lint.sh`+`dev/test.sh` locally, DCO sign-off, no IS branding, 2–3 per week.

## Sync-survival notes (G1)

- The route lives in NEW `now_lms/vistas/request_access.py`; at the v2.0.0 sync,
  `static_pages.py` dies (upstream split it into `contact.py`) — re-apply the
  `enable_contact` fix against upstream `contact.py` and verify the `ContactMessage`
  import path under v2.
- `scripts/deploy-smoke.sh` asserts `/request-access` 200, so a sync deploy physically
  cannot pass without the route.
- Append the new fork commit hashes to migration map §2
  (`000-docs/001-OD-PLAN-upstream-v2-sync-migration-map.md`).

## Operational loop (G7)

Slack is the alert path; Jeremy (or designee) reviews the admin list
(`/admin/contact-messages?q=[ACCESS]`) weekly; outreach is manual email from hello@
until the MXroute wiring (bead `now-lms-kyv`) lands. Smoke verifies the webhook var is
set inside the container.

## Verification

- pytest: new request-access tests + updated front-door contract tests green.
- Anonymous curl sweep: `/` (unchanged), `/course/explore` (teaser, zero vendor
  strings), every `/course/<code>/view` (302 → /request-access), every preview-resource
  URL, `/course/slide_show/<id>`, `/program/explore`, `/program/<codigo>`,
  `/masterclass/`, `/request-access` (form), `/contact` (404).
- One real submission end-to-end: DB row + Slack message in `#leads-contact` → test row
  deleted.
- Logged-in member check: enrolled course opens.

## Out of scope

- Payments/Stripe (bead `now-lms-bc2`, post-sync).
- The v2.0.0 sync itself.
- Any change to the landing page copy beyond swapping CTA hrefs.
- Building any panel follow-up content (patterns, write-ups, ritual, shepherd month) —
  dedicated sessions with Jeremy first.
- Prod cache is NullCache today (no stale-teaser risk); flag for the Redis/sync session.
- Retention policy for access-request rows — P2 bead.

---

## Appendix A — superseded bespoke design (do not build)

The original design created a dedicated `WaitingList` model + Alembic migration + a
`waitlist` blueprint + a cloned admin surface. It was superseded 2026-07-27 by the
native-first approach above when the Explore sweep found the platform already ships the
exact pattern (`contact_messages` + `/admin/contact-messages`). Recorded here so the
dead design is never re-derived:

- `now_lms/vistas/waitlist.py`: blueprint `waitlist`, routes `GET/POST /request-access`,
  FlaskForm + honeypot.
- Model `WaitingList` in `now_lms/db/__init__.py`: `id (ulid)`, `name`, `email`,
  `links (Text)`, `building (Text)`, `role_context`, `source`,
  `status (new → reviewing → invited/declined)`, `notes`, `creado` — BaseTabla idiom.
- Guarded additive Alembic migration `CREATE TABLE waiting_list`.
- Admin view cloned from the contact-messages views (list, detail, status, notes,
  unseen badge).

## Appendix B — panel findings (reference)

Three-seat panel (37signals school · pattern-community/apprenticeship school ·
proven-models research) answered "is there a proven model?": **yes — visible standard →
real work as curriculum → permanent community, with intake that reviews actual shipped
work.** Unanimous: the mailto was the right question wired to the wrong pipe (work-sample
intake is the fix); scarcity must be real and stated in numbers, never adjectives; the
house method must exist as written artifacts; and the hidden-ladder risk (stated purpose
"practice" vs actual driver "bench") is the #1 program-killer — reconciled by making
"we'd run this even if we weren't hiring" true, with how much goes public being Jeremy's
call (resolved as DECISION 2, the soft honesty sentence). Full seat-by-seat findings live
in the planning transcript and the four follow-up sessions carry them forward (agenda
bead). Nothing beyond the locked copy above was built from the panel.
