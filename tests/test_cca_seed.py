"""Tests for the CCA-F prep-course importer (scripts/seed_cca_courses.py).

Covers the pure data-shaping helpers (no DB) plus an integration test of
``_create_course`` against the in-memory test database: it must build the full
row graph (course -> section -> text lesson -> evaluation -> questions ->
options), map ``answerIndex`` to the correct option's ``is_correct``, preserve
the ``source`` attribution in the explanation, and be idempotent (a second run
for an existing course code is a no-op).
"""

import importlib.util
import pathlib

import pytest

from now_lms.db import (
    Curso,
    CursoRecurso,
    CursoSeccion,
    Evaluation,
    Question,
    QuestionOption,
    database,
)

# Import the standalone importer by path (it lives in scripts/, not the package).
_SEED_PATH = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "seed_cca_courses.py"
_spec = importlib.util.spec_from_file_location("seed_cca_courses", _SEED_PATH)
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

MODELS = {
    "Curso": Curso,
    "CursoSeccion": CursoSeccion,
    "CursoRecurso": CursoRecurso,
    "Evaluation": Evaluation,
    "Question": Question,
    "QuestionOption": QuestionOption,
}


# --------------------------------------------------------------------------- #
# Pure helpers (no DB)
# --------------------------------------------------------------------------- #


def test_truncate_clips_and_marks():
    assert seed._truncate("abcdef", 10) == "abcdef"
    out = seed._truncate("abcdefghij", 5)
    assert len(out) == 5 and out.endswith("…")
    assert seed._truncate(None, 5) == ""


def test_group_by_domain_orders_and_buckets():
    questions = [
        {"domain": 2, "domainName": "B", "domainKey": "b", "text": "q"},
        {"domain": 1, "domainName": "A", "domainKey": "a", "text": "q"},
        {"domain": 1, "domainName": "A", "domainKey": "a", "text": "q"},
    ]
    grouped = seed._group_by_domain(questions)
    assert [g[2] for g in grouped] == ["a", "b"]  # ordered by domain number
    assert len(grouped[0][3]) == 2 and len(grouped[1][3]) == 1


def test_load_bank_counts():
    assert len(seed._load_bank("questions-associate.json")) == 36
    assert len(seed._load_bank("questions-developer.json")) == 41
    assert len(seed._load_bank("questions-architect-professional.json")) == 36
    assert len(seed._load_bank("questions.json")) == 103


def test_weighted_mock_matches_cca_f_blueprint():
    general = seed._load_bank("questions.json")
    weights = {"agentic": 27, "claudecode": 20, "prompt": 20, "tools": 18, "context": 15}
    mock = seed._weighted_mock(general, weights, total=60)
    assert len(mock) == 60
    dist = {}
    for q in mock:
        dist[q["domainKey"]] = dist.get(q["domainKey"], 0) + 1
    assert dist == {"agentic": 16, "claudecode": 12, "prompt": 12, "tools": 11, "context": 9}


def test_build_specs_shapes():
    specs = seed._build_specs()
    by_code = {s["codigo"]: s for s in specs}
    assert set(by_code) == {"IS-START", "CCA-A", "CCA-B", "CCA-F"}
    # No section may fall back to the authoring stub.
    for spec in specs:
        for section in spec["sections"]:
            assert "being authored" not in section["lesson"], f"stub lesson in {spec['codigo']}"
    assert len(by_code["CCA-A"]["sections"]) == 7
    assert len(by_code["CCA-B"]["sections"]) == 8
    assert len(by_code["CCA-F"]["sections"]) == 6  # 5 official domains + pro-scenarios
    assert by_code["CCA-F"]["mock_questions"] and len(by_code["CCA-F"]["mock_questions"]) == 60


# --------------------------------------------------------------------------- #
# Integration (in-memory DB via the self-contained cca_db fixture)
# --------------------------------------------------------------------------- #


@pytest.fixture
def cca_db():
    """Self-contained in-memory DB context for the importer.

    Deliberately does NOT reuse the suite's ``app``/``db_session`` fixtures:
    those run ``init_app()``, which stamps Alembic instead of creating the
    schema and leaves some tables (e.g. ``ad_sense``) missing on a fresh SQLite
    ``:memory:`` DB. We only need the ORM tables the importer touches, so we
    create the full schema with ``create_all()`` and tear it down after.
    """
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    import now_lms

    app = now_lms.lms_app
    with app.app_context():
        database.create_all()
        try:
            yield database.session
        finally:
            database.session.remove()
            database.drop_all()


@pytest.fixture
def sample_questions():
    """Two associate-bank questions with distinct answer positions."""
    bank = seed._load_bank("questions-associate.json")
    return bank[:2]


def _spec_for(code, questions):
    return {
        "codigo": code,
        "nombre": "Test course",
        "nivel": 1,
        "duracion": 1,
        "descripcion_corta": "short",
        "descripcion": "long",
        "sections": [
            {"nombre": "Domain one", "descripcion": "d", "lesson": "# Lesson\n\nbody", "questions": questions}
        ],
        "mock_questions": None,
    }


def test_create_course_builds_full_graph(cca_db, sample_questions):
    seed._create_course(database, MODELS, _spec_for("CCA-T1", sample_questions))

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CCA-T1")).scalar_one_or_none()
    assert curso is not None
    assert curso.estado == "open" and curso.publico is True and curso.modalidad == "self_paced"

    secs = database.session.execute(database.select(CursoSeccion).filter_by(curso="CCA-T1")).scalars().all()
    assert len(secs) == 1 and secs[0].estado is True

    rec = database.session.execute(database.select(CursoRecurso).filter_by(seccion=secs[0].id)).scalars().all()
    assert len(rec) == 1 and rec[0].tipo == "text" and rec[0].text

    ev = database.session.execute(database.select(Evaluation).filter_by(section_id=secs[0].id)).scalar_one()
    assert ev.is_exam is False and ev.passing_score == 72.0 and ev.max_attempts is None

    questions = database.session.execute(
        database.select(Question).filter_by(evaluation_id=ev.id).order_by(Question.order)
    ).scalars().all()
    assert len(questions) == 2

    # answerIndex must map to exactly the correct option's is_correct, and the
    # source attribution must be preserved in the explanation.
    for q, src in zip(questions, sample_questions):
        opts = database.session.execute(
            database.select(QuestionOption).filter_by(question_id=q.id)
        ).scalars().all()
        correct_positions = [i for i, o in enumerate(opts) if o.is_correct]
        assert correct_positions == [src["answerIndex"]]
        assert "Source:" in (q.explanation or "")


def test_create_course_is_idempotent(cca_db, sample_questions):
    seed._create_course(database, MODELS, _spec_for("CCA-T2", sample_questions))
    first = database.session.execute(database.select(database.func.count(Curso.id))).scalar()
    # Re-running for the same code must add nothing.
    seed._create_course(database, MODELS, _spec_for("CCA-T2", sample_questions))
    second = database.session.execute(database.select(database.func.count(Curso.id))).scalar()
    assert first == second
    secs = database.session.execute(database.select(CursoSeccion).filter_by(curso="CCA-T2")).scalars().all()
    assert len(secs) == 1  # not duplicated
