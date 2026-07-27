# Upstream v2.0.0 sync — migration map

**Status:** planning only. Nothing in this document has been executed.
**Measured:** 2026-07-26, fork `deploy/now-lms-fixed` @ `4755503` vs `upstream/main` @ `b7bc8cf`
(third pass — first used `3fec727`, second `0c9eb75` after our four PRs merged, third after
upstream's security-headers series landed the same day).
**Tracking:** intent-solutions-io/now-lms#12. Deploy prerequisites: #14.

Every number here was measured, not estimated. Where it contradicts the earlier
plan, the earlier figure is quoted alongside so the difference is visible rather
than silently corrected.

---

## 1. The headline: this sync is much smaller than it looks

Divergence is **41 ahead / 111 behind** (35 of the 41 are non-merge commits). The 111 includes
the four commits upstream took from us today, so the *surviving* fork set shrinks by three once
they are dropped (§2). The last four upstream commits are the security-headers series (their
#213 line: global security headers + CSP/HSTS hardening + a README fix) — measured against them,
the conflict surface is **unchanged at 61 files with zero new conflicts**: that work merges
cleanly over this fork. Its one behavioral consequence for us is the CSP item in §7.

A test merge of `upstream/main` into `deploy/now-lms-fixed` produces **61
conflicted files** — all content conflicts, no rename/delete conflicts.
(The earlier plan said 84; 61 is the measured figure at `3fec727`.)

Of those 61:

| Source | Files | Share |
|---|---:|---:|
| Touched by the 4 dead i18n commits | **60** | 98% |
| Everything else (`Dockerfile` alone) | 1 | 2% |

**The entire conflict surface is the retired i18n layer.** The `Dockerfile`
conflict comes from `a3af0c4`, which is itself already fixed upstream. So the
conflict count for the work we actually want to keep is **zero**.

### But you cannot get there by merging and reverting

Measured: attempting to revert the four i18n commits fails — `9cf46a2`,
`8abbee2` and `1bd8cfd` all conflict on revert, because later fork commits build
on top of them. Only `706460c` reverts cleanly. A "merge then drop" approach
leaves 56 conflicts still to hand-resolve.

### Recommended strategy: rebuild, don't merge

Branch from `upstream/main` and cherry-pick only the must-survive set. The dead
i18n commits are never replayed, so their 60 conflicts cannot occur *by
construction* — rather than being resolved 60 times by hand, each resolution an
opportunity to reintroduce a Spanish string or drop an upstream fix.

```
git switch -c sync/v2.0.0 upstream/main
# cherry-pick the MUST SURVIVE set from §2, oldest first
```

Chosen over `git rebase --onto` because the dead commits need *dropping*, not
replaying, and over a merge because 98% of the conflicts are in files where we
want upstream's version verbatim.

---

## 2. Commit triage (all 35 non-merge commits)

> ⚠️ The earlier plan's triage table had **shuffled commit hashes**. Three
> corrections are called out inline. Verify against this table, not that one.

### DIES — already upstream or obsolete (6)

| Commit | Subject | Why it dies |
|---|---|---|
| `9cf46a2` | TEMPORARY English catalog bridge | Superseded by upstream v2.0.0 catalogs. Marked RETIRED in `FORK.md`. |
| `8abbee2` | complete the English catalog + hardcoded chrome | Same. |
| `1bd8cfd` | internationalize 62 authoring templates + forms | Same. Largest single conflict source (64 files). |
| `706460c` | internationalize 27 view files | Same. |
| `a3af0c4` | copy `package-lock.json` before `npm ci` | **Fixed upstream** — `Dockerfile:14` already copies the lockfile before the `npm ci` at line 16. ⚠️ *The earlier plan listed this hash as "compose — must survive". It is the docker lockfile fix and it dies.* |
| — | *(no sixth: see the `55900ed` correction below)* | |

### UPSTREAM FIRST, THEN DROP (3) — **all four PRs MERGED 2026-07-26; the drop is now unblocked**

| Commit | Upstream PR | Status |
|---|---|---|
| `a5ae792` | [#214](https://github.com/bmosoluciones/now-lms/pull/214) — `ProxyFix` uses undefined `app` | **merged** (12/12 checks passed) |
| `ab7a1fe` | [#215](https://github.com/bmosoluciones/now-lms/pull/215) — `NOW_LMS_TRUSTED_PROXY` | **merged** (12/12) |
| `ba1b5de` | [#216](https://github.com/bmosoluciones/now-lms/pull/216) — assets populate under custom data dir | **merged** (12/12) |

Verified present in `upstream/main` @ `0c9eb75`: `now_lms/__init__.py:536` now reads
`ProxyFix(flask_app.wsgi_app, …)`, `now_lms/db/initial_data.py:1653` carries the
`node_modules` guard, and `dev/lint.sh` no longer calls the deleted script.

⚠️ *The earlier plan listed `e457135` as the third Track C commit. `e457135` is
the docker-compose deploy wiring and **must survive**; the assets fix is
`ba1b5de`.*

A fourth PR, [#217](https://github.com/bmosoluciones/now-lms/pull/217)
(`dev/lint.sh` calls a deleted script), has no fork commit — it fixes an upstream
paper-cut directly.

Drop these three from the fork **only after** the corresponding PR merges. Until
then they must survive, or production regresses.

### MUST SURVIVE (26)

**Theme / front door (12)** — `cf4f06c`, `38a1e1b`, `ab05535`, `ece11c8`,
`63328f1`, `ebdc11e`, `8422991`, `aa9c0fa`, `5bafd93`, `ddb2213`, `cf74186`,
`a5993b6`. The whole 07-23 composition series, including the Google-Fonts-CDN
removal (a privacy improvement — do not regress it) and its test.

**Auth + catalog branding (2)** — `49b1ed3` (login/register/password rebrand),
`ea9fa6f` (course-detail branding).

**CCA-F curriculum (6)** — `8e184e3` → `47f5f9b` → `90b0d3e` → `ddd1b87` →
`5d41f43` → `884aaef`. Includes Rick Hightower's documented reuse grant; losing
`ddd1b87` loses the permission record.

**Deploy wiring (2)** — `e457135` (docker-compose for the VPS), `bcec165`
(healthcheck sends `X-Forwarded-Proto` so `FORCE_HTTPS` can't hang it).

**Governance / tooling (3)** — `0f70592` (`FORK.md` + `CODEOWNERS`), `c897582`
(MiniMax AI reviewer on the deploy line), `061bf68` (locale-tooling helper +
"adding a language" guide).

**Plus, corrected out of the "dies" bucket (1):**

| Commit | Subject | Correction |
|---|---|---|
| `a3f68fe` | translate password-reset email + PayPal JS to English (Max's #6) | **Not superseded.** See §3. |

**And one more, corrected out of the "dies" bucket:**

| Commit | Subject | Correction |
|---|---|---|
| `55900ed` | bootstrap a fresh PostgreSQL database correctly on first boot | **Not in upstream.** See §4. ⚠️ *The earlier plan listed this hash as "docker — fixed upstream". It is the PG bootstrap fix and it must survive.* |

Also must survive: **`ce1d2cb`** (the `mailto:` address fix, fork PR #13) — newer
than this triage, on `fix/mailto-address-encoding`.

---

## 3. Correction: Max's PR #6 is *not* superseded

The earlier plan had `a3f68fe` dying in the sync on the grounds that "upstream now
covers those strings via catalogs." **Measured otherwise.**

Upstream v2.0.0 `now_lms/auth.py:367` still reads:

```python
subject="Recuperación de Contraseña - NOW LMS",
...
<h1>Recuperación de Contraseña</h1>
<p>Hola {user.nombre},</p>
```

and `now_lms/static/js/paypal.js:42` still reads:

```javascript
showPaymentMessage('Procesando pago...', 'info');
```

Neither string is wrapped in `_()`. **Strings that are not gettext-wrapped cannot
be reached by a translation catalog**, no matter how complete that catalog is. So
upstream's i18n work — which is real and did supersede the 62-template layer —
does not touch these two files.

Consequence: dropping `a3f68fe` silently reverts the production password-reset
email and every PayPal payment message to Spanish. It must survive.

**Better follow-up:** the upstream-correct fix is to wrap those strings in `_()`
so the catalogs can translate them, rather than hardcoding English as the fork
did. That is a clean, small upstream contribution and would let us drop
`a3f68fe` legitimately later. Worth offering.

---

## 4. Correction: the PG bootstrap fix is *not* in upstream v2.0.0

PR [#179](https://github.com/bmosoluciones/now-lms/pull/179) reports
`merged=true` (merge commit `b63ca91`), which is why the earlier plan retired
`55900ed`. But:

- `b63ca91` is **not an ancestor of `upstream/main`**.
- `alembic.stamp()` appears nowhere in upstream `now_lms/**` (only in a test).
- `tests/test_fresh_database_bootstrap.py`, which #179 added, is **absent** from
  `upstream/main`.

So the fix was merged and then lost — reverted, or dropped in a later
rebase/force-push. The maintainer's #185 (identical title, opened two minutes
after #179 closed, closed six seconds later) suggests a re-land attempt that also
did not survive.

**Consequence:** dropping `55900ed` reintroduces the fresh-database bootstrap
failure that originally crash-looped this deployment. It must survive.

The fuller version of this fix — 40 lines plus a 180-line test, more complete
than the fork's 9-line `55900ed` — is preserved on
`origin/fix/postgresql-fresh-database-bootstrap` @ `ecc85d5`. That is the branch
to re-offer upstream, and the reason it was rescued rather than deleted.

---

## 5. Database migration analysis — lower risk than expected

Production is PostgreSQL 16 (`now-lms-db-1`). Measured live state:

| Fact | Value |
|---|---|
| `alembic_version` | `1780403775` |
| `static_pages` | exists; `custom_pages` does not |
| `configuracion.r` | exists; `csrf_seed` does not |
| `style.theme` | `intent_learn`, `varchar(15)`, nullable |
| `programa` tables | `programa`, `programa_curso`, `programa_estudiante` all exist |

`1780403775` **is** in upstream's chain, so the upgrade path resolves. Six
migrations will run, in order:

```
1780403775 (current)
  → 20260120_120000  make pago.curso nullable, add pago.programa
  → 20260724_120000  programa.nombre 20 → 150
  → 20260724_180000  pago.monto → Numeric(10,2)
  → 20260725_120000  configuracion.r → csrf_seed; increase theme length
  → 20260725_130000  style.theme NOT NULL default 'now_lms'
  → 20260726_000000  static_pages → custom_pages
```

### The structural hazard, and why it is contained

Production's schema was built by `create_all()` from the 07-21 **models**, then
stamped at `1780403775` — a revision *behind* several migrations whose effects
`create_all()` had already produced. The `programa` tables exist even though the
migration that references them has not run. Normally that combination is where
`alembic.upgrade()` dies on "already exists".

**All six migrations are guarded.** Each one inspects the live schema and returns
early or skips the step when the change is already present — verified by reading
every one:

- `20260120_120000` — `if "programa" not in columns` before `add_column`; index
  creation behind `if "ix_pago_programa" not in indexes`. Despite its name it
  does **not** create the `programa` tables, so their pre-existence is harmless.
- `20260724_120000` — returns if `programa` absent; alters only when
  `length != 150`.
- `20260724_180000` — returns if `pago`/`monto` absent; returns if already
  `Numeric(10,2)`.
- `20260725_120000` — branches on whether `r` / `csrf_seed` exist.
- `20260725_130000` — only rewrites `theme IS NULL` rows. **`intent_learn`
  survives** (12 chars, and the preceding migration widens the column).
- `20260726_000000` — renames only `if "static_pages" in tables and
  "custom_pages" not in tables`. Reversible.

So the expected outcome is a clean upgrade, not a fight. The risk is *residual*
(idempotence against a `create_all()` schema is a property to demonstrate, not
assume) rather than *expected*.

### Execution gate — still mandatory

Restore a production snapshot and run the upgrade against **that** before the
merge goes anywhere near the VPS:

1. `pg_dump` production → restore into a scratch database.
2. Run `alembic upgrade head` from v2.0.0 code against the restored copy.
3. Assert: `alembic_version` at head; `custom_pages` present and row-count
   matches the old `static_pages`; `configuracion.csrf_seed` present and
   preserving `r`'s value; `style.theme` still `intent_learn`.
4. Exercise the app against the migrated copy — front door, course list, course
   detail, login — before touching production.

Reason it stays mandatory despite the guards: `20260725_120000` moves a live
`csrf_seed` value, and a bad rename there invalidates sessions.

---

## 6. Sequencing

1. **Do not start until #14 is resolved.** The deploy is currently unprovable and
   theme files are shadowed by a stale Docker volume — shipping a sync through
   that blind spot means being unable to tell whether it worked.
2. Land upstream PRs #214 / #215 / #216 (#217 is independent), then drop
   `a5ae792`, `ab7a1fe`, `ba1b5de` from the fork.
3. Build `sync/v2.0.0` from `upstream/main` by cherry-picking the 26-commit
   must-survive set + `ce1d2cb`.
4. Run the §5 migration gate against a production snapshot.
5. `dev/lint.sh` + `dev/test.sh` green. Note `dev/lint.sh` fails on upstream
   today until #217 merges, and `black --check` already fails on
   `20260725_120000_rename_r_and_increase_theme_length.py` on unmodified
   `upstream/main` — pre-existing, not ours.
6. Re-`pybabel compile -d now_lms/translations`.
7. Verify the `intent_learn` theme against the new page model, then deploy.
8. Record the sync in `FORK.md`'s fork changelog.

---

## 7. Open items

- **`static_pages` → `custom_pages` in fork code — audit done, fixes deferred to
  sync time.** Four coupling points, all in files the theme copied verbatim from
  the built-in theme and which therefore inherited merge-base-era names:

  | File | Today (fork) | Required at v2.0.0 |
  |---|---|---|
  | `themes/intent_learn/footer.j2:1` | `get_footer_pages()` | `get_custom_pages()` |
  | `themes/intent_learn/footer.j2:13` | `url_for('static_pages.view_page')` | `custom_pages.view_page` |
  | `themes/intent_learn/footer.j2:43` | `url_for('static_pages.contact')` | `contact.contact_form` |
  | `themes/intent_learn/navbar.j2:80` | `url_for('static_pages.contact')` | `contact.contact_form` |

  ⛔ **These must land WITH the sync, not before it.** The fork registers
  `static_pages` (`now_lms/__init__.py:258`) and defines `get_footer_pages()`
  (`vistas/_helpers.py:97`); upstream v2.0.0 registers `custom_pages` (`:261`) and
  `get_custom_pages()` (`_helpers.py:117`). Renaming today raises
  `BuildError`/`UndefinedError` on every page load, because the new names do not
  exist on this side yet. The theme customises neither file, so the fix at sync
  time is simply to re-copy both from v2.0.0.

- **`theme.yml` — DONE** (PR #16). Upstream v2.0.0 gates `list_themes()` on the
  file's existence; without it `intent_learn` silently vanishes from admin →
  Settings → Appearance. Added early because it is inert on the current branch.

- **Favicon brand leak — DONE** (PR #16). The theme pointed its raster favicon
  fallback at core `static/icons/favicon/*` and seven upstream binaries had been
  overwritten in place, so all eight other bundled themes rendered the Intent
  Solutions mark. Marks moved into the theme's own directory; core restored
  byte-identical to upstream.
- **Re-offer `ecc85d5` upstream** (§4) — the full PG bootstrap fix with tests.
- **Offer gettext-wrapping for `auth.py` + `paypal.js`** (§3) so `a3f68fe` can
  eventually be retired legitimately.
- **`MAIL_USE_TLS` / `MAIL_USE_SSL` never coerce to booleans** in upstream
  `now_lms/mail.py`: `.capitalize()` yields `"True"`/`"False"` but the `match`
  arms compare against `"TRUE"`/`"FALSE"`, so they never match and the value
  stays a truthy string. Both transports read as enabled simultaneously.
  Candidate fifth upstream PR; tracked in #14.
- **Test gate on the deploy line — SHIPPED advisory, flips to blocking at the
  sync** (PR #18, bead `now-lms-dbq`). The gate's first-ever PostgreSQL run
  surfaced ~40 pre-existing suite failures: SQLite-masked strictness bugs
  (varchar-too-long, fixture FK violations — the suite had never run on the
  production engine) and i18n assertion drift (fork code emits English, inherited
  tests assert Spanish). Both classes are replaced wholesale by this sync, which
  is exactly why the pytest step is `continue-on-error` until then — lint is
  blocking today. Two fixture bugs live in fork-owned test files that survive the
  sync and need fixing regardless: `test_cca_seed.py` references a `default`
  certificate it never seeds (Postgres enforces the FK), and the front-door
  `lang="en"` assertion (fixed on the PR #13 branch).

- **CSP will silently break ionicons at the sync** (bead `now-lms-fzl`).
  Upstream's new global Content-Security-Policy allows scripts only from `'self'`,
  PayPal, and cdnjs — and the theme's `base.j2` loads ionicons from **unpkg.com**.
  Post-sync, browsers refuse both scripts and every ionicon on inner pages
  vanishes with console-only errors. Fix: vendor ionicons into the theme's static
  dir (matches the 07-23 Google-Fonts-removal privacy posture) and add the same
  no-CDN test guard. Safe to do **before** the sync — it is inert. Everything
  else in the theme survives the new CSP: inline styles are allowed
  (`'unsafe-inline'`), fonts and images are self-hosted; ionicons is the only
  external resource hit.
