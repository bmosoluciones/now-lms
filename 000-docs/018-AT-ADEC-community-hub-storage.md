# ADR-8 — Build the Community Hub on native forum storage, with three sidecar tables for the metadata, reactions and moderation trail the platform cannot represent

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-8 |
| **Title** | Build the Community Hub on native forum storage, with three sidecar tables for the metadata, reactions and moderation trail the platform cannot represent |
| **Status** | **Accepted** |
| **Date** | 2026-08-08 |
| **Ruled** | 2026-08-08 by Max Sheahan — Option §4.4 (native bodies and replies plus three sidecar tables). §4.2, the upstream-shaped alternative, remains the named V2 target under the §6 triggers. |
| **Author** | Filed ahead of the implementation on `feat/community-hub` |
| **Note on numbering** | ADR-6 (short-answer evaluations) is claimed by the open PR #37. ADR-7 is `014-AT-ADEC`. This decision takes ADR-8 and document number `015`, the next free slot on `deploy/now-lms-fixed`. |

## 1. Decision Summary

> **We will** build a private Community Hub as a fork-local `/community`
> blueprint that stores post bodies and the reply tree in the native
> `foro_mensaje` table, adding three new sidecar tables —
> `comunidad_publicacion` (title, post type, moderation state, pinning),
> `comunidad_reaccion` (likes, with a database uniqueness constraint on
> `(mensaje_id, usuario)`), and `comunidad_evento_moderacion` (an append-only
> report and moderator-action trail) — **in order to** give the cohort a durable,
> searchable home for Questions, Builds and Success Stories that replaces
> WhatsApp as the system of record, **accepting that** three bespoke tables are a
> deliberate deviation from ADR-1's native-first rule, carried fork-local until
> the design is generalised upstream.

`ForoMensaje` itself is **not modified**. Existing course forums are unaffected
by construction, not by testing.

## 2. Context

Cohort knowledge currently dies in WhatsApp. Three Intent Solutions groups carry
the traffic, and every useful answer in them is unsearchable, unattributable and
lost to the next member who asks the same question. The retired `cohort-hub`
prototype named this as its third stated purpose and as a team success criterion,
then shipped its community surface as an inert UI shell with a disabled composer
and zero server-side code. Nothing was ever built.

The platform ships a forum. It is genuinely close: `ForoMensaje` already carries
a course-scoped root post, a self-referential `parent_id` for replies, an
`abierto`/`cerrado` thread lock, and a markdown-to-sanitised-HTML render path.
Post bodies and threading need no new code and no new storage.

What the platform does not have, verified by search rather than recollection:

- **No title.** A forum message is a body and nothing else.
- **No post type.** Nothing distinguishes a question from a build log.
- **No moderation state.** No hiding, no restoring, no reporting, no pinning,
  and no audit trail. `Message.is_reported` exists on the deprecated private-
  messaging model, not on the forum.
- **No reaction of any kind.** Searched `like`, `likes`, `reaction`, `reaccion`,
  `voto`, `vote`, `upvote`, `favorito`, `marcador`, `kudos`, `bookmark`, `star`,
  `rating`, plus a class scan of `now_lms/db/__init__.py`. Every hit is a SQL
  `LIKE` operator, English prose in a comment, or a decorative `bi-bookmark`
  icon. There is no model, column, table, route or template.
- **No ranking.** Nothing orders anything by engagement anywhere.

The likes requirement is what forces this decision. One member, one like is a
uniqueness constraint over a pair, and a uniqueness constraint needs rows. The
brief that commissioned this work rules out every representation that would avoid
them — sentinel replies, a content prefix, a mutable counter — and rules them out
correctly: none can be enforced under concurrent writes, and each turns a
data-integrity requirement into a convention that the first double-click breaks.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Data integrity (one member, one like) | High | Not satisfiable without a table and a unique constraint. This is the driver that decides the ADR |
| Native-first rule (ADR-1) | High | Argues against this decision. See §4.1 |
| Blast radius on existing course forums | High | `ForoMensaje` is shared. Leaving it untouched converts "we tested for regressions" into "a regression is not expressible" |
| Privacy and authorization | High | Member-authored content in a public repository's application, on a platform whose self-registration gate lives outside this repo |
| Sync cost | Medium | Three tables and a blueprint must be re-applied at every upstream sync until upstream takes the feature |
| Query performance | Medium | A feed with per-post like and reply counts is where N+1 lives. The native forum already has this bug at `templates/forum/forum_list.html:76` |

## 4. Alternatives Considered

### 4.1 Native storage only, metadata in a content prefix (the ADR-4 pattern) — rejected

This is the strongest argument against the decision and deserves stating
plainly, because it is also what this project's own most recent community
decision recommended. On 2026-08-02 the recorded recommendation was a fork-local
`/feed` blueprint on the native `foro_mensaje` table, over both a config-only
Community course and a new `feed_post` model, on the reasoning that *"new routes
on native storage are fork-permanent, new tables are not."* ADR-4 had already
blessed exactly this shape for `/request-access`, storing a waiting list in
`contact_messages` behind an ASCII subject prefix: zero tables, zero migrations,
a native admin surface, nothing to rehearse against a production snapshot,
nothing to re-apply at a sync.

That reasoning was sound and it still is — for everything except likes. It is
rejected here on one ground and one only: **a text prefix cannot carry a
uniqueness constraint.** Title and post type could live in a prefix. Moderation
state could live in a prefix. One member, one like cannot, because enforcing it
means the database refusing a second row, and there is no second row to refuse.
Every workaround is worse than the table it avoids:

- *A sentinel reply per like* pollutes the reply tree that the same feature
  depends on for its reply count, and de-duplicating it requires reading every
  reply on every write.
- *A mutable counter column* is a lost update under concurrency and cannot
  answer "have I already liked this," which is the only question the UI asks.
- *A delimited list of usernames in the body* is a read-modify-write race, is
  unbounded, and puts the private liker list into the rendered content.

ADR-7 §4.1 already articulates the escape from ADR-4's pattern, in the same
words that apply here: *"the waiting list never needed to aggregate, and this
does."* A feed aggregates, ranks and de-duplicates. The waiting list did none of
those things.

**This ADR therefore strikes the no-new-table clause of the 2026-08-02
recommendation and preserves the rest of it.** The recommendation's substance —
a fork-local route, post bodies and replies on native `foro_mensaje`, no
`feed_post` model owning content — is adopted in full. Only its "no new tables"
conclusion falls, and it falls because the likes requirement was added on
2026-08-08, six days after it was written. The reason changed; the decision's
core did not. The original wording is preserved in the daily record rather than
rewritten, so the substitution is auditable.

### 4.2 Extend `ForoMensaje` itself: add `titulo`, `tipo` and `estado_moderacion` columns, plus a generic `foro_reaccion` table — deferred to V2, not rejected

This is the most ADR-1-compliant option available and the only one with a real
retirement path. *"Forum threads gain an optional title and a type; forum
messages gain reactions"* is a plausible generic upstream feature that benefits
every NOW-LMS deployment, and it is exactly the shape ADR-6 chose for
short-answer evaluations — author it upstream rather than fork-locally. It also
removes the join, removes the possibility of a root post without its metadata
row, and removes the transactional invariant that Option 4.4 has to hold.

It is deferred rather than rejected, on two grounds. First, it edits the
`ForoMensaje` class inside `now_lms/db/__init__.py`, a file upstream actively
maintains: a test merge of `upstream/main` into `deploy/now-lms-fixed` already
produced 61 conflicted files, and a mid-class edit is the highest-conflict
location available. Second, it changes the shape of a model every existing course
forum shares, so "no course-forum regression" becomes something to prove by
testing rather than something that cannot happen. It also asks every ordinary
forum message — one posted to a course forum with no title and no type — to carry
three NULL columns forever.

**This is the named V2 target.** See §6 for the triggers that should promote it.

### 4.3 A new `community_post` model owning bodies and replies — rejected

Explicitly ruled out on 2026-08-02, and correctly. It discards the native reply
tree, the native `estado` thread lock and the whole native-first posture, in
exchange for nothing that 4.4 does not already provide.

### 4.4 Native bodies and replies, plus three sidecar tables (chosen)

Three models appended to `now_lms/db/__init__.py`, one guarded Alembic revision,
one blueprint, four themed pages. `ForoMensaje` untouched.

## 5. Consequences

**Positive:** post bodies, the reply tree and thread lock/unlock stay native, so
the 2026-08-02 decision's substance holds. `ForoMensaje` is unmodified, so course
forums cannot regress. One member, one like is enforced by the database rather
than by application convention. Rollback is non-destructive: unregistering the
blueprint removes the Hub while every member post remains in `foro_mensaje`, and
the migration's `downgrade()` drops only the three new tables, so no member
content is reachable by it.

**Negative / accepted:** three bespoke tables and a bespoke blueprint, the thing
ADR-1 exists to prevent. They must be re-applied at every upstream sync until
upstream takes the feature, and as designed they have no retirement path — the
post-type vocabulary and the trending contract are Intent-specific. §6 names the
triggers for converting this into the upstream-shaped 4.2 design, which does have
one. A feed page also carries a join to the metadata sidecar and aggregate
subqueries for the counts; the mitigation is a hard budget of four queries per
feed page, asserted in the test suite rather than assumed.

**A deliberate asymmetry, recorded so it is not read as a bug:** the like count
displayed on a post counts every reaction row, while the trending calculation
counts only reactions from members with `activo = True`. A displayed count that
silently dropped when an unrelated account was deactivated would be confusing;
a ranking that a deactivated account could still prop up would be gameable. The
two numbers answer different questions and are allowed to differ.

**Security posture shipped with it:**

- Every mutating route goes through a `FlaskForm` and `validate_on_submit()`.
  This application does not install `CSRFProtect`, so `csrf_token()` is not a
  template global and a hand-rolled POST form would carry no CSRF protection at
  all. Note that the native forum's close and open POSTs are hand-rolled and
  therefore unprotected today; that is a separate upstream fix, not something
  this feature copies.
- The Hub uses its own bleach allow-list rather than importing the forum's.
  **`img` is dropped entirely.** All three existing sanitisers permit `<img src>`
  with no scheme or host restriction, which makes any member post a tracking
  pixel that leaks every reader's IP, User-Agent and referrer. Media hosting is
  an explicit non-goal for V1, so images have no legitimate use here.
- `a` is permitted with `href`, `title` and `rel`, and a post-sanitise pass sets
  `rel="noopener noreferrer nofollow"` on every anchor. The forum's allow-list
  strips `rel`, so its links cannot be hardened at render time at all.
- The optional build link is validated to `https` with a hostname, reusing the
  shape of `_valid_verification_url` from ADR-7's implementation.
- A hidden post returns 404 rather than 403, and a malformed identifier returns
  the same 404 with an identical body, so no response confirms that a post
  exists.
- The liker list is private. No route returns it and no template renders it;
  only the aggregate count is exposed.
- Rate limits are enforced by an in-process sliding window keyed on the member's
  username, following `vistas/request_access.py`. The repo's `check_rate_limit`
  helper is deliberately **not** used: it is a silent no-op under `NullCache`,
  which is the production cache configuration's fallback.
- Every Hub response carries `X-Robots-Tag: noindex, nofollow`.
- Post bodies, titles and moderation reasons are length-capped in the form. The
  native forum has no length validator and `contenido` is unbounded `Text`.

**Access model.** Membership is not enrollment. Every active Intent Solutions
member is a Hub member by the owner's ruling, so the gate is an active account
with a verified email and a real role, checked on every route. Because
`ForoMensaje.curso_id` is `NOT NULL`, posts still need a container: one canonical
private Community course serves as it, with `foro_habilitado = False`. That flag
is deliberate and does three things at once — it closes the native forum route on
that course so nobody can reach Hub posts through `/course/<code>/forum` and
bypass the moderation filter, it keeps the forum link off the course page, and it
never trips the validator that forbids `foro_habilitado` on a `self_paced`
course. Cross-cohort disclosure is prevented structurally rather than by
filtering: there is exactly one Hub, everyone is in it, and every query is scoped
to one course code at the query level, never hidden in a template.

**A dependency worth naming.** Self-registration is closed at the host ingress
layer, outside this repository, so "having an account" equals "being a member"
only while that host configuration holds. The Hub does not rely on it: it checks
`activo` and email verification itself.

**Compliance note.** A member reply is not official guidance. Staff replies carry
an explicit role badge and member replies do not, and the composer carries the
standing recommendation-versus-requirement line. Partner-policy and certification
questions continue to route to one person in one batch, per the existing rule.

## 6. Review Triggers

- **Promote to the §4.2 upstream design** when any of these fires: upstream
  expresses interest in forum reactions or thread titles; a second surface in
  this fork needs reactions; or the next upstream sync makes the cost of
  carrying three fork-local tables visible in conflict count.
- Cohort growth makes the live trending query a measurable cost → revisit with a
  **superseding ADR, not a quiet migration**.
- The Hub needs to remove a member without removing them from the whole platform
  → build Hub-scoped suspension. The V1 break-glass is `Usuario.activo = False`,
  which is deliberately blunt; the first time that is the wrong remedy is the
  trigger.
- Likes are wanted on replies, or a second reaction type is proposed → superseding
  ADR. The owner has ruled that there is **no thumbs-down, dislike or downvote
  affordance**, and the schema encodes exactly one reaction with no polarity
  column, so adding one is a schema change and a product change together.
- Anonymous posting is requested → superseding ADR. It was considered and
  rejected for V1: a durable knowledge base needs attribution, and anonymity
  inside a small named cohort is mostly illusory while making moderation harder.

## 7. Related

- ADR-1 (`002-AT-ADEC`) — the native-first rule this decision deviates from.
- ADR-4 (`009-AT-ADEC`) — the native-reuse precedent argued against in §4.1.
- ADR-5 (`010-AT-ADEC`) — the gating posture the Hub's privacy stance extends.
- ADR-7 (`014-AT-ADEC`) — the precedent for a deliberate, recorded new-table
  deviation, and the source of the security checklist reused above.
- `FORK.md` — the fork-local carries table, where this feature is registered with
  its upstream path and retirement condition.
