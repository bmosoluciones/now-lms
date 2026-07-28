"""Tests for the CCA-F prep-course importer (scripts/seed_cca_courses.py).

Covers the pure data-shaping helpers (no DB) plus an integration test of
``_create_course`` against the in-memory test database: it must build the full
row graph (course -> section -> text lesson -> evaluation -> questions ->
options), map ``answerIndex`` to the correct option's ``is_correct``, preserve
the ``source`` attribution in the explanation, and be idempotent (a second run
for an existing course code is a no-op).

**Only the bank-shape tests need the curriculum, which is not in this
repository.** Teaching content lives in the private
``intent-solutions-io/intent-curriculum`` repo (see
``scripts/seed_cca_courses.py``), so tests that read a real bank or lesson are
individually marked ``_content_required`` and skip unless ``CCA_CONTENT_DIR``
points at a checkout. Everything else — the pure helpers and the whole
``_create_course`` integration surface (graph build, idempotency, visibility
gating) — runs on synthetic bank-shaped fixtures so public CI keeps regression
coverage without touching private content.
"""

import importlib.util
import pathlib

import pytest

from now_lms.db import (
    Certificado,
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

# Applied per-test, NOT module-wide: only tests that read a real bank or lesson
# are content-dependent; the rest must keep running in public CI.
_content_required = pytest.mark.skipif(
    not (seed.BANKS_DIR.is_dir() and seed.LESSONS_DIR.is_dir()),
    reason=(
        "curriculum content not present; set CCA_CONTENT_DIR to a checkout of "
        "the private intent-curriculum repo to run these"
    ),
)

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


@_content_required
def test_load_bank_counts():
    assert len(seed._load_bank("questions-associate.json")) == 36
    assert len(seed._load_bank("questions-developer.json")) == 41
    assert len(seed._load_bank("questions-architect-professional.json")) == 36
    assert len(seed._load_bank("questions.json")) == 103


@_content_required
def test_weighted_mock_matches_cca_f_blueprint():
    general = seed._load_bank("questions.json")
    weights = {"agentic": 27, "claudecode": 20, "prompt": 20, "tools": 18, "context": 15}
    mock = seed._weighted_mock(general, weights, total=60)
    assert len(mock) == 60
    dist = {}
    for q in mock:
        dist[q["domainKey"]] = dist.get(q["domainKey"], 0) + 1
    assert dist == {"agentic": 16, "claudecode": 12, "prompt": 12, "tools": 11, "context": 9}


@_content_required
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


def test_weighted_exam_series_non_overlapping():
    # 300 synthetic questions, 60 per domain, weighted evenly -> whole exams of 50.
    questions = []
    for d, key in enumerate(["agentic", "claudecode", "prompt", "tools", "context"], start=1):
        for n in range(60):
            questions.append({"domainKey": key, "domain": d, "text": f"{key}-{n}", "id": f"{key}-{n}"})
    weights = {"agentic": 20, "claudecode": 20, "prompt": 20, "tools": 20, "context": 20}
    exams = seed._weighted_exam_series(questions, weights, per_exam=50, max_exams=5)
    assert len(exams) == 5  # 300 questions / 50 per exam
    assert all(len(e) == 50 for e in exams)
    ids = [q["id"] for e in exams for q in e]
    assert len(ids) == len(set(ids))  # no question reused across exams


@_content_required
def test_build_specs_includes_rick_practice_exams():
    """When Rick's bank is vendored, Course C gains full-length practice exams."""
    if not seed._load_bank_optional("rick-practice-exams.json"):
        pytest.skip("Rick practice-exam bank not vendored in this checkout")
    cca_f = {s["codigo"]: s for s in seed._build_specs()}["CCA-F"]
    assert len(cca_f["extra_exams"]) >= 1
    for exam in cca_f["extra_exams"]:
        assert len(exam["questions"]) == 60


# --------------------------------------------------------------------------- #
# Integration (in-memory DB via the self-contained cca_db fixture)
# --------------------------------------------------------------------------- #


@pytest.fixture
def cca_db(app):
    """App context for the importer against the suite's shared database.

    v2.0.0's conftest owns the schema lifecycle (session-scoped creation +
    TRUNCATE cleanup between tests), so this fixture must NOT create or drop
    anything: the previous self-managed ``create_all()``/``drop_all()`` pair
    destroyed tables the conftest expects but ``create_all()`` cannot rebuild
    (``system_info`` is not in the model metadata), cascading hundreds of
    failures through every later test file in a full-suite run.

    The one thing it guarantees: the ``default`` certificate template that
    ``Curso.plantilla_certificado``'s FK implicitly needs on PostgreSQL
    (get-or-create — v2's initial data may have seeded it already).
    """
    with app.app_context():
        existing_default = database.session.execute(
            database.select(Certificado).filter_by(code="default")
        ).scalar_one_or_none()
        if existing_default is None:
            database.session.add(
                Certificado(
                    code="default",
                    titulo="Default template",
                    descripcion="Certificate template required by Curso's FK default.",
                    tipo="course",
                    habilitado=False,
                    publico=False,
                )
            )
            database.session.commit()
        yield database.session


@pytest.fixture
def sample_questions():
    """Two synthetic bank-shaped questions with distinct answer positions.

    Synthetic rather than read from the associate bank so the integration tests
    run without the private curriculum checkout — the importer only cares about
    the bank SHAPE (text / options / answerIndex / rationale / source), which
    these reproduce.
    """
    return [
        {
            "text": "Which option is correct for the first question?",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": 1,
            "rationale": "beta is correct because of the documented behavior.",
            "source": "Synthetic fixture A",
        },
        {
            "text": "Which option is correct for the second question?",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": 3,
            "rationale": "delta is correct per the reference.",
            "source": "Synthetic fixture B",
        },
    ]


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
    # publico is False by design since the 2026-07-27 gating: the public catalog
    # is a doctrine teaser and members reach courses through enrollment, so a
    # reseed must never resurrect a publicly-listed course.
    assert curso.estado == "open" and curso.publico is False and curso.modalidad == "self_paced"

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


def test_create_course_gates_pre_gating_public_course(cca_db, sample_questions):
    """A reseed against a pre-gating database enforces publico=False.

    Simulates a database restored from a backup taken before the 2026-07-27
    gating SQL ran: the course (and a free-preview resource, which leaks the
    outline) sit at publico=True. Re-running the importer must flip both to
    False while leaving the structure untouched.
    """
    seed._create_course(database, MODELS, _spec_for("CCA-T3", sample_questions))
    curso = database.session.execute(database.select(Curso).filter_by(codigo="CCA-T3")).scalar_one()
    recurso = database.session.execute(database.select(CursoRecurso).filter_by(curso="CCA-T3")).scalars().first()
    curso.publico = True
    recurso.publico = True
    database.session.commit()

    seed._create_course(database, MODELS, _spec_for("CCA-T3", sample_questions))

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CCA-T3")).scalar_one()
    assert curso.publico is False
    resources = database.session.execute(database.select(CursoRecurso).filter_by(curso="CCA-T3")).scalars().all()
    assert all(r.publico is False for r in resources)
    secs = database.session.execute(database.select(CursoSeccion).filter_by(curso="CCA-T3")).scalars().all()
    assert len(secs) == 1  # structure untouched — visibility only
