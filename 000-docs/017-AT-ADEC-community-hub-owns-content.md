# ADR-10 — The Community Hub owns its own content (supersedes ADR-8)

## ADR Metadata

| Field | Value |
|---|---|
| **ADR Number** | ADR-10 |
| **Title** | The Community Hub owns its own content |
| **Status** | Accepted |
| **Date** | 2026-08-09 |
| **Supersedes** | ADR-8 (`018-AT-ADEC-community-hub-storage.md`), which stays readable per the Nygard pattern |
| **Ruled** | 2026-08-09 by Max Sheahan |
| **Note on numbering** | ADR-6 is claimed by open PR #37; ADR-9 is `016-AT-ADEC` (member dashboard). This takes ADR-10 and document number `017`. |

## 1. Decision Summary

> **We will** give `ComunidadPublicacion` its own `contenido`, `usuario` and
> self-referential `parent_id`, so the Community Hub owns its posts and replies
> outright, **in order to** remove the container course that ADR-8 required and
> the silent data-loss path that came with it, **accepting that** member-authored
> prose now lives in a fork-local table carried across every upstream sync.

Three tables either way. ADR-8 traded no table for real complexity.

## 2. Context — why ADR-8 is being superseded one day after it was accepted

ADR-8 kept post bodies in the native `ForoMensaje` with a metadata sidecar. It
was implemented, tested and working. It is superseded because three of its load
-bearing arguments do not survive inspection.

**The table count is identical.** ADR-8's central claim was that native storage
avoids a table. It does not. If `comunidad_publicacion` owns the body and a
self-FK, the sidecar *is* the post table — three tables in both designs. The
container course, the JOIN on every query, the invisibility machinery, the
`foro_habilitado = False` coupling and the cascade exposure were bought for
nothing.

**Its rollback argument was false, not merely weak.** ADR-8 §5 offered as a
benefit that unregistering the blueprint leaves posts readable through the
course forum. Reading them requires `foro_habilitado = True` on the container —
the exact flag ADR-8 set to `False` because the native forum route renders Hub
posts with no moderation filter and would therefore show hidden posts. The
document claimed as a benefit the thing its own security design forbids.

**The blast radius was real and concrete.** `ForoMensaje.curso_id` is
`ondelete="CASCADE"`. Deleting the container row silently deletes every post,
reply and like in the Hub. That is not hypothetical: the 2026-08-07 audit's C1
critical finding is that `--reset=CODE` is the only way to change a course, and
that `_delete_course` documents a "no learner data yet" precondition it does not
enforce — it deletes and prints success. ADR-8's implementation had to add a
bespoke guard to that script. Writing protective code around a row that exists
for no product reason is the tell that the row should not exist.

**And the native model was barely being used.** The Hub has its own sanitizer
(because `forum.py`'s permits `<img src>` with no host restriction, a tracking
pixel in every post), its own queries, its own lock semantics, its own feed, and
it disables the native forum route. Native storage supplied five columns.

The record also already favoured this shape: `cohort-hub/public/proposal.html:293`,
Max's July proposal, says *"A posts table and endpoints, the composer switched on
for members."* No course, no container.

## 3. Decision Drivers

| Driver | Weight | Note |
|---|---|---|
| Silent data loss | High | The container's cascade could take the whole Hub through a script already flagged C1 |
| Honest accounting | High | Equal table count means ADR-8 was paying complexity for a slogan |
| Simplicity | High | Single-table selects, no JOIN, no seeder, no invisibility tests, no delete guard |
| Native-first (ADR-1) | Medium | Argues for ADR-8, but the exception was already spent on three tables; there is no native cohort feed to use |
| Sync cost | Medium | The same three tables either way; a new table in a new module is the lowest-conflict divergence available |

## 4. Alternatives Considered

### 4.1 Keep ADR-8's native bodies plus a sidecar — superseded

Stated fairly, because it is what was accepted yesterday: it keeps member prose
in a table upstream maintains, and it inherits the reply tree and thread lock for
free. Those are real.

They are outweighed. The reply tree and lock are roughly fifteen lines — a
self-FK with `ondelete=CASCADE` and a status column, both written here. The
"upstream maintains it" benefit cuts the other way too: the sidecar carried a
foreign key *into* `foro_mensaje.id`, so an upstream change there broke us
regardless. We were coupled either way, and more coupled with the sidecar.

### 4.2 A separate `comunidad_respuesta` table for replies — rejected

Cleaner typing (a reply genuinely has no title or type) at the cost of two
queries for every thread and a union for the trending reply count. The nullable
columns are the cheaper trade.

### 4.3 `ComunidadPublicacion` owns bodies and replies (chosen)

`parent_id` NULL is a root post, non-NULL is a reply. `titulo` and `tipo` are
nullable because they belong to a root post.

## 5. Consequences

**Positive:** no container course, no seeder, no `foro_habilitado` coupling, no
self-paced validator dance, no invisibility tests, no delete guard, no JOIN on
any feed query. The cascade now runs *inside* the Hub, where deleting a post
correctly takes its replies, likes and moderation trail with it — a scoped
blast radius replacing an unscoped one. `ForoMensaje` remains untouched, so
course forums are unaffected under this ADR exactly as under ADR-8.

**Negative / accepted:** member-authored prose lives in a fork-local table
re-applied at every upstream sync. Note this line was already crossed by ADR-8 —
`comunidad_reaccion` and `comunidad_evento_moderacion` hold member-authored
content — so this widens an existing exposure rather than creating one.
`titulo` and `tipo` are nullable on a table where a root post always has both;
that invariant lives in the route rather than the schema.

**Unchanged from ADR-8, and still true:** likes are two idempotent endpoints
arbitrated by `UNIQUE(publicacion_id, usuario)`; there is exactly one reaction
and no polarity column, so a thumbs-down is a schema *and* product change;
Trending is computed live with per-member weights and refuses to rank on thin
data; reporting never hides; nothing hard-deletes; the Hub's own sanitiser drops
images entirely and hardens every anchor.

**Migration:** the ADR-8 revision was never pushed, so it was replaced in place
rather than layered. One head, upgrade and downgrade both rehearsed.

## 6. Review Triggers

- Upstream ships a real cohort-wide feed → reassess with a superseding ADR.
- Replies need their own type, title or attachments → revisit §4.2.
- A second surface needs reactions → generalise `comunidad_reaccion` and offer
  it upstream, the retirement path ADR-8 §4.2 named and this ADR inherits.
- Likes on replies, or a second reaction type → superseding ADR, because the
  no-thumbs-down ruling is encoded in the absence of a polarity column.

## 7. Related

- ADR-8 (`015-AT-ADEC`) — superseded by this decision; left readable.
- ADR-1 (`002-AT-ADEC`) — the native-first rule both ADRs deviate from.
- ADR-9 (`016-AT-ADEC`) — the member dashboard the feed lands on.
- `FORK.md` — the divergence row.
