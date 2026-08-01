#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Seed the Intent Solutions practice tracks as placeholder courses.

Why this exists
---------------
A fresh install seeds four upstream demo courses — "OnLine Teaching 101",
"Course Details", "Free Course" and a Spanish "Complete Guide to NOW LMS". They
are sample data for a platform demo, not Intent Solutions content, and a member
landing on a dashboard full of them learns the wrong thing about what this place
is. One of them is in Spanish.

This seeds the three practice tracks already published on the public catalog page
(`themes/intent_learn/overrides/course_list.j2`), so the front door and the
signed-in surfaces finally describe the same product.

The house core is deliberately NOT a fourth course. It is the shared method every
track teaches — "all members begin with the shared house core, regardless of
track" describes a foundation the three tracks hold in common, not a module to
enroll in separately. It appears as a closing line in each track's description
instead.

These are PLACEHOLDERS. Every course says so in its own description and carries a
single placeholder lesson. Nobody should be able to open one and mistake it for
authored curriculum. Real curriculum lives in the private `intent-curriculum`
repo and is seeded by `seed_cca_courses.py` / `seed_module_courses.py`.

Usage
-----
    python scripts/seed_practice_tracks.py                  # create, skip existing
    python scripts/seed_practice_tracks.py --reset          # rebuild the three
    python scripts/seed_practice_tracks.py --remove-demo    # also drop upstream demo courses

All three tracks sit at the same level. They are peers — three ways to prove the
same house method — not a ladder, so ranking one above another would be a claim
the practice does not make.

`--remove-demo` refuses to delete a course that has enrollments, so it cannot
take a real member's course out from under them.

Note on lesson bodies: the body goes in `descripcion`, not `text`. The renderer
(`learning/resources/type_text.html`) reads `descripcion` and never reads `text`,
so a lesson written to `text` alone stores fine and renders as a blank page.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from now_lms import lms_app
from now_lms.db import Curso, CursoRecurso, CursoSeccion, EstudianteCurso, database

# Upstream's demo seed data. Codes come from now_lms/db/initial_data.py.
#
# "lms-training" is deliberately NOT in this list. It is not demo content: it is
# upstream's operator manual, "Guía Completa de NOW LMS" — how to run the LMS as
# an administrator or instructor. Upstream gates it accordingly, in its own code:
#
#     now_lms/vistas/courses/base.py:120   (William Moreno, 1b3857f, 2026-07-21)
#     if course_code == "lms-training" and current_user.is_authenticated:
#         if current_user.tipo in ("admin", "instructor"):
#
# Deleting it removes staff documentation, not sample data — and it would go
# unnoticed: scripts/deploy-smoke.sh asserts /course/lms-training/view returns
# 302 anonymously, but by that file's own comment a course that does not exist
# ALSO returns 302, so the smoke check cannot tell the two apart.
#
# Bead now-lms-4vf.
DEMO_COURSE_CODES = ["now", "details", "free", "resources"]

HOUSE_CORE_NOTE = (
    "All members begin with the shared house core, regardless of track. "
    "The house method travels with you."
)

TRACKS = [
    {
        "codigo": "IS-ARCH",
        "nombre": "Production architecture",
        "descripcion_corta": "System design, risk judgment, and technical decision-making under constraints.",
        "descripcion": (
            "System design, risk judgment, and technical decision-making under constraints. Members "
            "practice architecture patterns, postmortems, governance frameworks, and cost/reliability "
            "tradeoffs. " + HOUSE_CORE_NOTE
        ),
        "nivel": 2,
        "lesson": "Architecture patterns and the tradeoffs they hide",
    },
    {
        "codigo": "IS-AGENT",
        "nombre": "Agent building & orchestration",
        "descripcion_corta": "Tools, context, handoffs, and failure modes.",
        "descripcion": (
            "Tools, context, handoffs, and failure modes. Members build real agents, debug evals, and "
            "ship systems that fail gracefully beyond a single impressive prompt. " + HOUSE_CORE_NOTE
        ),
        "nivel": 2,
        "lesson": "What a single impressive prompt does not get you",
    },
    {
        "codigo": "IS-EVAL",
        "nombre": "Evaluation & governance",
        "descripcion_corta": "Evidence, policy, auditability, and release confidence.",
        "descripcion": (
            "Evidence, policy, auditability, and release confidence. Members design evals that separate "
            "demonstrated behavior from confident claims, and operate systems with clear ownership when "
            "the model is wrong. " + HOUSE_CORE_NOTE
        ),
        "nivel": 2,
        "lesson": "Separating demonstrated behavior from confident claims",
    },
]

PLACEHOLDER_BODY = (
    "### This track is not built yet\n\n"
    "The outline above describes where this track is going. The lessons are not written.\n\n"
    "**What is real today:** the track description, and the house core every member shares.\n\n"
    "**What is not:** any lesson content in this course. Nothing here has been reviewed or "
    "graded, and no part of it should be treated as Intent Solutions curriculum.\n\n"
    "This placeholder exists so the platform shows the practice as it is actually organised "
    "rather than a set of sample courses shipped with the software."
)


def _stamp(row, who: str = "seed_practice_tracks"):
    row.creado = datetime.now(timezone.utc).date()
    row.creado_por = who
    return row


def remove_demo_courses(db) -> None:
    """Delete upstream's demo courses, refusing any that a member is enrolled in."""
    for code in DEMO_COURSE_CODES:
        curso = db.session.execute(db.select(Curso).filter_by(codigo=code)).scalars().first()
        if curso is None:
            continue
        enrolled = (
            db.session.execute(db.select(EstudianteCurso).filter_by(curso=code)).scalars().all()
        )
        if enrolled:
            print(f"[keep] {code}: {len(enrolled)} enrollment(s) — refusing to delete")
            continue
        for model in (CursoRecurso, CursoSeccion):
            for row in db.session.execute(db.select(model).filter_by(curso=code)).scalars().all():
                db.session.delete(row)
        db.session.delete(curso)
        print(f"[drop] {code}")
    db.session.commit()


def seed(db, reset: bool) -> None:
    for spec in TRACKS:
        code = spec["codigo"]
        existing = db.session.execute(db.select(Curso).filter_by(codigo=code)).scalars().first()

        if existing and not reset:
            print(f"[skip] {code} already exists")
            continue

        if existing:
            enrolled = db.session.execute(db.select(EstudianteCurso).filter_by(curso=code)).scalars().all()
            if enrolled:
                print(f"[keep] {code}: {len(enrolled)} enrollment(s) — refusing to reset")
                continue
            for model in (CursoRecurso, CursoSeccion):
                for row in db.session.execute(db.select(model).filter_by(curso=code)).scalars().all():
                    db.session.delete(row)
            db.session.delete(existing)
            db.session.flush()

        curso = Curso(
            nombre=spec["nombre"],
            codigo=code,
            descripcion_corta=spec["descripcion_corta"][:280],
            descripcion=spec["descripcion"][:1000],
            nivel=spec["nivel"],
            estado="open",
            publico=False,          # gated: the catalog is a doctrine teaser, not a listing
            modalidad="self_paced",
            pagado=False,           # free self-enroll for admitted members
            auditable=False,
            certificado=False,
            foro_habilitado=False,
            limitado=False,
            promocionado=False,
        )
        db.session.add(_stamp(curso))
        db.session.flush()

        seccion = CursoSeccion(
            curso=code,
            nombre="Track outline",
            descripcion="What this track covers once it is built.",
            indice=1,
            estado=True,
        )
        db.session.add(_stamp(seccion))
        db.session.flush()

        recurso = CursoRecurso(
            curso=code,
            seccion=seccion.id,
            tipo="text",
            nombre=spec["lesson"][:150],
            # descripcion is what type_text.html renders. text is written too so the
            # platform's own authoring form round-trips, but it is not the display field.
            descripcion=PLACEHOLDER_BODY,
            text=PLACEHOLDER_BODY,
            indice=1,
            publico=False,
            requerido="optional",
        )
        db.session.add(_stamp(recurso))
        print(f"[seed] {code}  {spec['nombre']}")

    db.session.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="rebuild tracks that already exist")
    parser.add_argument("--remove-demo", action="store_true", help="delete upstream's demo courses")
    args = parser.parse_args()

    with lms_app.app_context():
        if args.remove_demo:
            remove_demo_courses(database)
        seed(database, reset=args.reset)

        codes = [c.codigo for c in database.session.execute(database.select(Curso)).scalars().all()]
        print(f"\ncourses now present: {sorted(codes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
