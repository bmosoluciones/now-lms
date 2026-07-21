#!/usr/bin/env python3.12
"""Idempotent seeder for the preliminary CCA-F prep curriculum on NOW-LMS.

Builds four courses (see ``COURSES`` below) from the vendored Intent Solutions
question banks (``content/cca/banks/*.json``) and the authored lesson prose
(``content/cca/lessons/<course-dir>/<domainKey>.md``):

  * Course 0 — Getting Started on Intent Solutions Learn (onboarding, no exam)
  * Course A — Claude Foundations (Associate onramp)
  * Course B — Building with Claude (Developer)
  * Course C — Claude Certified Architect — Foundations (CCA-F) prep

Each quiz course becomes a ``Curso`` with one ``CursoSeccion`` per question-bank
domain; every section carries a ``text`` lesson resource (the authored markdown)
plus a practice ``Evaluation`` (unlimited attempts) seeded from that domain's
questions. Every course also gets a final mock-exam section (``is_exam=True``,
``passing_score=72.0``); Course C's mock mirrors the CCA-F blueprint — ~60
questions weighted across the five official domains.

The importer is a pure DB operation and is **idempotent**: it guards on the
course ``codigo`` already existing and skips that whole course, so re-running
adds nothing. Each course is committed independently.

Run it in the app container exactly like the demo-course seed::

    docker compose exec -T app python3.12 scripts/seed_cca_courses.py

Question shape (per bank item): ``{id, domain, domainName, domainKey, text,
options[], answerIndex, rationale, source}``. Mapping onto NOW-LMS:
``answerIndex`` -> the matching ``QuestionOption.is_correct``; ``rationale`` (+
appended ``source`` attribution) -> ``Question.explanation``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Repo root is scripts/.. — resolve content paths relative to it, not cwd, so
# the script works from any working directory inside the container.
REPO_ROOT = Path(__file__).resolve().parent.parent
BANKS_DIR = REPO_ROOT / "content" / "cca" / "banks"
LESSONS_DIR = REPO_ROOT / "content" / "cca" / "lessons"

# Column limits from now_lms/db/__init__.py (Question.text 1000, explanation
# 1000, QuestionOption.text 500). The current banks fit, but guard anyway so a
# future bank edit degrades gracefully instead of raising a DB error.
MAX_QUESTION_TEXT = 1000
MAX_EXPLANATION = 1000
MAX_OPTION_TEXT = 500


def _truncate(value: str, limit: int) -> str:
    """Clip ``value`` to ``limit`` chars, appending an ellipsis if clipped."""
    if value is None:
        return ""
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _load_bank(filename: str) -> list[dict]:
    """Load a vendored question bank and return its ``questions`` list."""
    path = BANKS_DIR / filename
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data["questions"] if isinstance(data, dict) else data


def _load_lesson(course_dir: str, stem: str, fallback_title: str) -> str:
    """Return authored lesson markdown, or a minimal stub if the file is absent.

    Lessons are keyed by the bank's ``domainKey`` (quiz courses) or an explicit
    stem (Getting Started), so the mapping is deterministic. A missing file must
    never crash the import — the section still seeds with a stub the team can
    fill in on the follow-on authoring pass.
    """
    path = LESSONS_DIR / course_dir / f"{stem}.md"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return (
        f"# {fallback_title}\n\n"
        "_Lesson prose for this section is being authored. Use the practice "
        "questions below and the Further reading links in the course sources._"
    )


def _group_by_domain(questions: list[dict]) -> list[tuple[int, str, str, list[dict]]]:
    """Group bank questions by domain, preserving first-seen order.

    Returns ``[(domain_number, domain_name, domain_key, [questions...]), ...]``
    ordered by the integer ``domain`` field so sections come out 1..N.
    """
    buckets: dict[str, dict] = {}
    for question in questions:
        key = question.get("domainKey") or str(question.get("domain"))
        bucket = buckets.setdefault(
            key,
            {
                "domain": question.get("domain", 0),
                "name": question.get("domainName", key),
                "key": key,
                "questions": [],
            },
        )
        bucket["questions"].append(question)
    ordered = sorted(buckets.values(), key=lambda b: (b["domain"], b["name"]))
    return [(b["domain"], b["name"], b["key"], b["questions"]) for b in ordered]


def _weighted_mock(questions: list[dict], weights: dict[str, int], total: int) -> list[dict]:
    """Deterministically pick ~``total`` questions weighted by domain.

    ``weights`` maps a ``domainKey`` to that domain's CCA-F percentage; we scale
    those to ``total`` and take the first K questions of each domain (order
    preserved), so the selection is stable across re-runs (no RNG).
    """
    by_key: dict[str, list[dict]] = {}
    for question in questions:
        by_key.setdefault(question.get("domainKey"), []).append(question)
    weight_sum = sum(weights.values()) or 1
    selected: list[dict] = []
    for key, weight in weights.items():
        take = round(total * weight / weight_sum)
        selected.extend(by_key.get(key, [])[:take])
    return selected


# ---------------------------------------------------------------------------
# Persistence helpers (each commits independently for crash-safe partial runs)
# ---------------------------------------------------------------------------


def _add_section(db, models, curso_codigo: str, indice: int, nombre: str, descripcion: str):
    """Create one published section and return it."""
    seccion = models["CursoSeccion"](
        curso=curso_codigo,
        nombre=_truncate(nombre, 100),
        descripcion=_truncate(descripcion, 250),
        indice=indice,
        estado=True,  # published (Boolean: True == public)
    )
    db.session.add(seccion)
    db.session.commit()
    return seccion


def _add_lesson_resource(db, models, curso_codigo: str, section_id: str, nombre: str, markdown: str):
    """Attach the authored markdown as a ``text`` resource on the section."""
    recurso = models["CursoRecurso"](
        curso=curso_codigo,
        seccion=section_id,
        tipo="text",
        nombre=_truncate(f"Lesson: {nombre}", 150),
        descripcion=_truncate(f"Reading for {nombre}", 500),
        indice=1,
        publico=False,
        requerido="required",
        text=markdown,
    )
    db.session.add(recurso)
    db.session.commit()


def _add_evaluation(db, models, section_id: str, title: str, description: str, is_exam: bool,
                    passing_score: float, questions: list[dict]) -> int:
    """Create an evaluation on a section and import its questions.

    ``answerIndex`` -> the matching option's ``is_correct``; ``rationale`` +
    appended ``source`` attribution -> ``explanation``. Returns the number of
    questions imported.
    """
    evaluation = models["Evaluation"](
        section_id=section_id,
        title=_truncate(title, 200),
        description=_truncate(description, 1000),
        is_exam=is_exam,
        passing_score=passing_score,
        max_attempts=None,  # unlimited (practice and first-pass mock alike)
    )
    db.session.add(evaluation)
    db.session.commit()

    imported = 0
    for order, item in enumerate(questions, start=1):
        rationale = (item.get("rationale") or "").strip()
        source = (item.get("source") or "").strip()
        explanation = rationale + (f"\n\nSource: {source}" if source else "")
        question = models["Question"](
            evaluation_id=evaluation.id,
            type="multiple",
            text=_truncate(item["text"], MAX_QUESTION_TEXT),
            explanation=_truncate(explanation, MAX_EXPLANATION),
            order=order,
        )
        db.session.add(question)
        db.session.commit()  # flush so question.id is available for options

        answer_index = item.get("answerIndex")
        for position, option_text in enumerate(item.get("options", [])):
            db.session.add(
                models["QuestionOption"](
                    question_id=question.id,
                    text=_truncate(option_text, MAX_OPTION_TEXT),
                    is_correct=(position == answer_index),
                )
            )
        db.session.commit()
        imported += 1
    return imported


def _create_course(db, models, spec: dict) -> None:
    """Create one course + its sections/lessons/evaluations, or skip if it exists."""
    Curso = models["Curso"]
    existing = db.session.execute(
        db.select(Curso).filter_by(codigo=spec["codigo"])
    ).scalar_one_or_none()
    if existing is not None:
        print(f"  [skip] course '{spec['codigo']}' already exists — no changes")
        return

    curso = Curso(
        nombre=_truncate(spec["nombre"], 150),
        codigo=spec["codigo"],
        descripcion_corta=_truncate(spec["descripcion_corta"], 280),
        descripcion=_truncate(spec["descripcion"], 1000),
        estado="open",
        publico=True,
        modalidad="self_paced",
        nivel=spec["nivel"],
        duracion=spec.get("duracion", 4),
        certificado=False,
        auditable=False,
        pagado=False,
        limitado=False,
        foro_habilitado=False,
        portada=False,
    )
    db.session.add(curso)
    db.session.commit()

    indice = 1
    total_questions = 0

    # --- Content sections (each: lesson + optional practice evaluation) ---
    for section in spec["sections"]:
        seccion = _add_section(
            db, models, spec["codigo"], indice, section["nombre"], section["descripcion"]
        )
        _add_lesson_resource(db, models, spec["codigo"], seccion.id, section["nombre"], section["lesson"])
        if section.get("questions"):
            total_questions += _add_evaluation(
                db,
                models,
                seccion.id,
                title=f"Practice quiz — {section['nombre']}",
                description="Unlimited-attempt practice. Rationale shown after each question.",
                is_exam=False,
                passing_score=72.0,
                questions=section["questions"],
            )
        indice += 1

    # --- Final mock exam section (if this course has one) ---
    if spec.get("mock_questions"):
        seccion = _add_section(
            db,
            models,
            spec["codigo"],
            indice,
            "Final mock exam",
            "Timed-style mock exam. Passing score 72% mirrors the CCA-F scale.",
        )
        _add_lesson_resource(
            db,
            models,
            spec["codigo"],
            seccion.id,
            "Final mock exam",
            "# Final mock exam\n\nThis exam mirrors the real assessment's shape. "
            "Passing is **72%**. Take it under exam-like conditions once you have "
            "worked through every section's practice quiz.",
        )
        total_questions += _add_evaluation(
            db,
            models,
            seccion.id,
            title=f"Mock exam — {spec['nombre']}",
            description="Final mock exam. Passing score 72%.",
            is_exam=True,
            passing_score=72.0,
            questions=spec["mock_questions"],
        )
        indice += 1

    print(
        f"  [ok]   course '{spec['codigo']}' — {indice - 1} sections, "
        f"{total_questions} questions imported"
    )


def _build_specs() -> list[dict]:
    """Assemble the course specifications from the vendored banks + lessons."""
    associate = _load_bank("questions-associate.json")
    developer = _load_bank("questions-developer.json")
    architect = _load_bank("questions-architect-professional.json")
    general = _load_bank("questions.json")

    specs: list[dict] = []

    # --- Course 0: Getting Started (onboarding, no exam) ---
    getting_started_lessons = [
        ("student-login", "Signing in as a student", "Create your account, verify your email, and log in."),
        ("admin-and-roles", "Roles, admin & instructor access", "How the four roles work and how staff reach the admin panel."),
        ("enrolling-and-progress", "Enrolling and tracking progress", "Find a course, enroll, and complete resources."),
        ("password-reset", "Resetting your password", "Recover access with the forgot-password flow."),
    ]
    specs.append({
        "codigo": "IS-START",
        "nombre": "Getting Started on Intent Solutions Learn",
        "descripcion_corta": "How to sign in, enroll, track progress, and (for staff) run the platform.",
        "descripcion": "A short onboarding module for every new learner and instructor: student "
                       "sign-in and email verification, enrolling and tracking progress, password reset, "
                       "and the admin/instructor roles and panel. Start here before any prep course.",
        "nivel": 0,
        "duracion": 1,
        "sections": [
            {
                "nombre": title,
                "descripcion": desc,
                "lesson": _load_lesson("getting-started", stem, title),
            }
            for stem, title, desc in getting_started_lessons
        ],
    })

    # --- Course A: Associate onramp ---
    specs.append({
        "codigo": "CCA-A",
        "nombre": "Claude Foundations (Associate onramp)",
        "descripcion_corta": "Foundational Claude skills: prompting, evaluation, product selection, workflows, governance.",
        "descripcion": "The associate-level onramp toward the Claude Certified Architect path. Covers "
                       "prompting and task execution, output evaluation, product and model selection, "
                       "workflow integration, configuration, responsible use, and troubleshooting.",
        "nivel": 1,
        "duracion": 4,
        "sections": [
            {
                "nombre": name,
                "descripcion": f"{name} — lesson and practice quiz.",
                "lesson": _load_lesson("course-a-associate", key, name),
                "questions": qs,
            }
            for _num, name, key, qs in _group_by_domain(associate)
        ],
        "mock_questions": associate,
    })

    # --- Course B: Developer ---
    specs.append({
        "codigo": "CCA-B",
        "nombre": "Building with Claude (Developer)",
        "descripcion_corta": "Developer-level Claude: agents, integration, Claude Code, eval, tools & MCP, security.",
        "descripcion": "The developer-level course: building agents and workflows, application integration, "
                       "Claude Code, evaluation and debugging, model selection, prompt and context engineering, "
                       "security, and tools & MCP.",
        "nivel": 2,
        "duracion": 5,
        "sections": [
            {
                "nombre": name,
                "descripcion": f"{name} — lesson and practice quiz.",
                "lesson": _load_lesson("course-b-developer", key, name),
                "questions": qs,
            }
            for _num, name, key, qs in _group_by_domain(developer)
        ],
        "mock_questions": developer,
    })

    # --- Course C: CCA-F prep (five official domains from the general bank) ---
    # CCA-F domain weights (percent) keyed by the general bank's domainKey.
    cca_f_weights = {
        "agentic": 27,    # Agentic Architecture
        "claudecode": 20,  # Claude Code Workflows
        "prompt": 20,      # Prompt Engineering
        "tools": 18,       # Tool Design & MCP
        "context": 15,     # Context Management
    }
    cca_sections = [
        {
            "nombre": name,
            "descripcion": f"{name} — lesson and practice quiz.",
            "lesson": _load_lesson("course-c-cca-f", key, name),
            "questions": qs,
        }
        for _num, name, key, qs in _group_by_domain(general)
    ]
    # Architect-professional bank feeds an extra professional-scenario practice section.
    cca_sections.append({
        "nombre": "Professional-level scenario practice",
        "descripcion": "Architect Professional scenario bank — extra practice beyond the five domains.",
        "lesson": _load_lesson("course-c-cca-f", "professional-scenarios", "Professional-level scenario practice"),
        "questions": architect,
    })
    specs.append({
        "codigo": "CCA-F",
        "nombre": "Claude Certified Architect — Foundations (CCA-F) prep",
        "descripcion_corta": "Prep for the CCA-F credential: the five official domains + a weighted 60-question mock.",
        "descripcion": "Preliminary preparation toward Anthropic's Claude Certified Architect (CCA) — "
                       "Foundations credential. One section per official domain (Agentic Architecture, "
                       "Claude Code Workflows, Prompt Engineering, Tool Design & MCP, Context Management) "
                       "with a practice quiz each, plus a weighted 60-question mock exam at the 72% pass mark. "
                       "This course prepares you for the real Anthropic exam; it is not the exam itself.",
        "nivel": 3,
        "duracion": 6,
        "sections": cca_sections,
        "mock_questions": _weighted_mock(general, cca_f_weights, total=60),
    })

    return specs


def main() -> int:
    """Seed all four courses inside the app context. Returns a shell exit code."""
    # When run as a script, sys.path[0] is this file's directory (scripts/), not
    # the repo root, so the ``now_lms`` package next to it isn't importable.
    # Put the repo root first so ``import now_lms`` resolves regardless of cwd.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from now_lms import app
    from now_lms.db import (
        Curso,
        CursoRecurso,
        CursoSeccion,
        Evaluation,
        Question,
        QuestionOption,
        database,
    )

    models = {
        "Curso": Curso,
        "CursoSeccion": CursoSeccion,
        "CursoRecurso": CursoRecurso,
        "Evaluation": Evaluation,
        "Question": Question,
        "QuestionOption": QuestionOption,
    }

    with app.app_context():
        print("Seeding CCA-F preliminary prep curriculum...")
        specs = _build_specs()
        for spec in specs:
            _create_course(database, models, spec)
        print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
