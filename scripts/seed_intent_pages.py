#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Replace the upstream boilerplate footer pages with Intent Solutions' own.

Two problems with the seeded defaults this fixes:

1. **They are upstream's text.** The shipped privacy page names no company, no
   jurisdiction and no contact route that reliably exists — it tells members to
   use "our contact form", which 404s whenever ``enable_contact`` is off. A page
   that makes claims on Intent Solutions' behalf without naming Intent Solutions
   is worse than no page.
2. **They are seeded per language and never corrected.**
   ``crear_paginas_estaticas_predeterminadas()`` reads ``Configuracion.lang`` and
   guards on ``if not existing``, so a deployment seeded in the wrong language
   keeps Spanish or Portuguese titles forever, and changing the language
   afterwards does nothing. That is why the preview footer read "Política de
   Privacidad" while the database said ``lang = 'en'``.

This script UPSERTS instead: it corrects an existing row rather than skipping it,
so it is safe to re-run and it repairs drift. Idempotent by content — running it
twice reports no change the second time.

**What this page is and is not.** The data-handling description below is factual
and derived from the schema: every category listed is something this application
demonstrably stores. The formal legal terms — the entity, the governing law, the
retention schedule, the rights procedure — are NOT invented here. They are marked
as outstanding on the page itself, because a privacy policy that states an
unverified jurisdiction is a worse liability than one that admits it is pending.
Jeremy owns those facts; see the OUTSTANDING block below.

Usage::

    DATABASE_URL=... python3 scripts/seed_intent_pages.py
    DATABASE_URL=... python3 scripts/seed_intent_pages.py --dry-run
"""

from __future__ import annotations

import argparse
import sys

# Everything below is checkable against the schema. Nothing here is aspirational.
PRIVACY = """
<h2>What this page covers</h2>
<p>
  Intent Solutions Learn is the private learning platform for the Intent Solutions
  cohort. This page describes what the platform stores about you, who can see it,
  and what happens to it. It is written from the platform's own data model, so it
  describes what actually happens rather than what a template says usually happens.
</p>

<h2>What the platform stores</h2>
<p><strong>Your account.</strong> Your name, email address, and whether that email
  has been verified. Your password is stored only as a hash and cannot be read back
  by anyone, including staff. If you fill them in, your profile may also hold a
  title, biography, date of birth, gender, profile photo, and links to your own
  website, LinkedIn, GitHub, X, Facebook or YouTube. Every one of those profile
  fields is optional and blank unless you enter it.</p>

<p><strong>Your learning.</strong> Which courses you are enrolled in, which
  resources you have completed, your percentage progress in each course, your
  evaluation attempts including the answers you selected and the scores you
  received, and any certificates issued to you.</p>

<p><strong>Credentials you record.</strong> If you use the prior-credentials page,
  the credential name, its issuer verification link, the date, and any certificate
  image you upload. Uploaded images are stored outside the public files directory
  and served only through an access-checked route.</p>

<p><strong>What you write.</strong> Community posts and replies, which posts you
  have liked, messages you send through the platform, and anything you submit
  through the access-request or contact forms.</p>

<p><strong>Technical records.</strong> Your last sign-in time, your session, and
  ordinary web server logs. If you pay for something, the payment is processed by
  PayPal and the platform stores the resulting payment record; card details never
  reach this platform.</p>

<h2>Who can see it</h2>
<p><strong>Other members</strong> see your name and anything you deliberately
  publish: your community posts, your replies, and the fact that a post has a
  number of likes. <em>Who</em> liked a post is never shown to anyone, including
  staff, and no page or export exposes that list. Your email address is never shown
  to other members. If you set your profile to not visible, your name still appears
  on what you wrote — attribution is how a discussion stays useful — but it does not
  link to a profile page.</p>

<p><strong>Instructors, moderators and administrators</strong> can see the same
  member-visible content, plus your enrolment and progress, your evaluation
  attempts, credentials you have recorded, and the moderation history of any post.
  Staff can hide a post from other members; hiding is reversible, always records a
  reason, and never deletes what you wrote.</p>

<p><strong>Nobody outside the platform.</strong> Every page described here requires
  you to be signed in. The community is not indexed by search engines and is not
  visible to the public web.</p>

<h2>Your account, in your hands</h2>
<p>You can edit or clear any optional profile field yourself at any time. To ask
  for a copy of your data, to correct something you cannot edit, or to have your
  account closed, use the contact route below and say so plainly; a person will
  answer you.</p>

<h2>What is still being finalised</h2>
<p>
  Intent Solutions is finalising the formal terms that belong in a privacy policy:
  the legal entity and its jurisdiction, the retention periods for each category
  above, the named contact for data requests, and the full list of infrastructure
  providers involved in running this platform. Those are not stated on this page
  yet because stating them before they are settled would be worse than admitting
  they are pending. This page will be replaced when they are.
</p>
<p>
  In the meantime, everything described above is accurate about how the platform
  behaves today, and any question about your data will be answered by a person
  rather than a policy document.
</p>
""".strip()

ABOUT = """
<h2>Intent Solutions Learn</h2>
<p>
  This is the private learning platform for the Intent Solutions cohort: the
  courses, the practice material, and the community where members ask questions,
  show what they have built, and share what worked.
</p>
<p>
  Access is by invitation. If you are not a member and would like to be, use the
  access request link in the footer.
</p>
""".strip()

PAGINAS = [
    {"slug": "privacy-policy", "title": "Privacy Policy", "content": PRIVACY, "footer": True},
    {"slug": "about-us", "title": "About Us", "content": ABOUT, "footer": True},
]

# Facts this script deliberately does NOT assert. Printed on every run so they
# cannot quietly become someone's assumption that the page is complete.
OUTSTANDING = [
    "Legal entity name and form, and the governing jurisdiction",
    "Retention period per data category",
    "Named contact (and postal address, if one is required) for data requests",
    "Whether GDPR / UK GDPR / CCPA apply, given where cohort members actually live",
    "The infrastructure and sub-processor list for this deployment",
    "Whether intentsolutions.io/privacy (currently an empty stub) becomes the canonical policy",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Upsert the Intent Solutions footer pages.")
    parser.add_argument("--dry-run", action="store_true", help="report what would change and exit")
    args = parser.parse_args()

    from now_lms import app, database
    from now_lms.db import CustomPage

    with app.app_context():
        cambios = []
        for pagina in PAGINAS:
            fila = database.session.execute(
                database.select(CustomPage).filter_by(slug=pagina["slug"])
            ).scalars().first()

            if fila is None:
                cambios.append(f"create {pagina['slug']}")
                if not args.dry_run:
                    database.session.add(
                        CustomPage(
                            slug=pagina["slug"],
                            title=pagina["title"],
                            content=pagina["content"],
                            is_active=True,
                            mostrar_en_footer=pagina["footer"],
                        )
                    )
                continue

            # UPSERT, not skip: the upstream seeder guards on existence, which is
            # why a row seeded in the wrong language stays wrong forever.
            diferencias = []
            if fila.title != pagina["title"]:
                diferencias.append(f"title {fila.title!r} -> {pagina['title']!r}")
            if fila.content != pagina["content"]:
                diferencias.append(f"content ({len(fila.content)} -> {len(pagina['content'])} chars)")
            if not fila.is_active:
                diferencias.append("is_active -> True")
            if fila.mostrar_en_footer != pagina["footer"]:
                diferencias.append(f"footer -> {pagina['footer']}")

            if diferencias:
                cambios.append(f"update {pagina['slug']}: " + "; ".join(diferencias))
                if not args.dry_run:
                    fila.title = pagina["title"]
                    fila.content = pagina["content"]
                    fila.is_active = True
                    fila.mostrar_en_footer = pagina["footer"]

        if not args.dry_run:
            database.session.commit()

        if cambios:
            for c in cambios:
                print(("would " if args.dry_run else "") + c)
        else:
            print("No change: pages already match.")

    print("\nSTILL OWED BY INTENT SOLUTIONS before this page is a real privacy policy:", file=sys.stderr)
    for punto in OUTSTANDING:
        print(f"  - {punto}", file=sys.stderr)


if __name__ == "__main__":
    main()
