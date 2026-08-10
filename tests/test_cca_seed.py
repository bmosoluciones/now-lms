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

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Certificado,
    Curso,
    CursoRecurso,
    CursoSeccion,
    EstudianteCurso,
    Evaluation,
    EvaluationAttempt,
    Question,
    QuestionOption,
    Usuario,
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
    "EstudianteCurso": EstudianteCurso,
    "EvaluationAttempt": EvaluationAttempt,
}


# --------------------------------------------------------------------------- #
# Pure helpers (no DB)
# --------------------------------------------------------------------------- #


def test_truncate_clips_and_marks():
    assert seed._truncate("abcdef", 10) == "abcdef"
    out = seed._truncate("abcdefghij", 5)
    assert len(out) == 5 and out.endswith("…")
    assert seed._truncate(None, 5) == ""


def test_correct_positions_reads_single_and_multi_answer_items():
    """Both bank encodings resolve, and ``answerIndexes`` wins when both are present."""
    opts = ["a", "b", "c", "d", "e"]
    assert seed._correct_positions({"id": "q", "options": opts, "answerIndex": 1}) == {1}
    # position 0 must survive: an `if not answer_index` style check would drop it.
    assert seed._correct_positions({"id": "q", "options": opts, "answerIndex": 0}) == {0}
    assert seed._correct_positions({"id": "q", "options": opts, "answerIndexes": [1, 3]}) == {1, 3}
    assert seed._correct_positions({"id": "q", "options": opts, "answerIndexes": [1, 3], "answerIndex": None}) == {1, 3}


def test_correct_positions_refuses_an_unanswerable_item():
    """The regression this helper exists for.

    The importer previously computed ``is_correct=(position == item.get("answerIndex"))``.
    A multi-correct item encodes ``answerIndex: null``, so ``position == None`` was False
    for EVERY option: the question imported with no correct answer at all, looked normal
    in the UI, and could not be answered correctly by anyone — silently. Refusing at seed
    time is the only honest outcome for a certification-prep exam.
    """
    opts = ["a", "b", "c", "d"]
    with pytest.raises(ValueError, match="no correct answer"):
        seed._correct_positions({"id": "MP-1.7", "options": opts, "answerIndex": None})
    with pytest.raises(ValueError, match="no correct answer"):
        seed._correct_positions({"id": "q", "options": opts})
    with pytest.raises(ValueError, match="no correct answer"):
        seed._correct_positions({"id": "q", "options": opts, "answerIndexes": []})
    with pytest.raises(ValueError, match="outside"):
        seed._correct_positions({"id": "q", "options": opts, "answerIndex": 9})
    with pytest.raises(ValueError, match="outside"):
        seed._correct_positions({"id": "q", "options": opts, "answerIndex": -1})
    with pytest.raises(TypeError):
        seed._correct_positions({"id": "q", "options": opts, "answerIndexes": ["B"]})
    # bool is an int subclass, so `answerIndexes: [true]` would otherwise mean position 1.
    with pytest.raises(TypeError):
        seed._correct_positions({"id": "q", "options": opts, "answerIndexes": [True]})
    # An item with no options at all reports THAT, rather than a confusing
    # "outside its 0 options" (raised in review of PR #76).
    with pytest.raises(ValueError, match="no options"):
        seed._correct_positions({"id": "q", "options": [], "answerIndex": 0})
    # A bare int instead of a list must name the offending bank item, not die on
    # Python's native "'int' object is not iterable" (raised in review of PR #76).
    with pytest.raises(TypeError, match="must be a list"):
        seed._correct_positions({"id": "q", "options": opts, "answerIndexes": 1})


def test_create_course_validates_answers_before_writing_any_row(cca_db):
    """A malformed item must not leave a half-imported course behind.

    ``_correct_positions`` raises, and the Question row is committed to obtain its id, so
    the resolve has to happen FIRST. Otherwise a bad bank aborts partway and leaves an
    orphan Question with no options attached. Raised in review of PR #76.
    """
    broken = [
        {
            "text": "This item has no resolvable answer.",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": None,
            "rationale": "n/a",
            "source": "Synthetic fixture D",
        }
    ]
    with pytest.raises(ValueError, match="no correct answer"):
        seed._create_course(database, MODELS, _spec_for("CCA-TBROKEN", broken))

    # The evaluation may exist (it is created before the question loop), but no orphan
    # Question row may have been written for the item that failed validation.
    orphans = database.session.execute(
        database.select(Question).filter(Question.text == broken[0]["text"])
    ).scalars().all()
    assert orphans == [], "a question row was written for an item that failed validation"


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


def test_create_course_marks_every_correct_option_for_a_multi_answer_item(cca_db):
    """A "select TWO" item must land TWO correct options in the row graph.

    This is the end of the chain the helper starts: the platform already grades
    multi-correct (``_answer_is_correct`` compares ``set(selected_ids) == correct_ids``
    for ``type="multiple"``, which is what every seeded question is), so proving the
    IMPORTER marks both options is what makes such an item answerable at all.
    """
    multi = [
        {
            "text": "Which TWO options are correct?",
            "options": ["alpha", "beta", "gamma", "delta", "epsilon"],
            "answerIndexes": [1, 3],
            "answerIndex": None,
            "rationale": "beta and delta together.",
            "source": "Synthetic fixture C",
        }
    ]
    seed._create_course(database, MODELS, _spec_for("CCA-TMULTI", multi))

    secs = database.session.execute(database.select(CursoSeccion).filter_by(curso="CCA-TMULTI")).scalars().all()
    ev = database.session.execute(database.select(Evaluation).filter_by(section_id=secs[0].id)).scalar_one()
    question = database.session.execute(database.select(Question).filter_by(evaluation_id=ev.id)).scalar_one()

    # type="multiple" is what routes grading to the set-comparison branch.
    assert question.type == "multiple"
    opts = database.session.execute(database.select(QuestionOption).filter_by(question_id=question.id)).scalars().all()
    correct_positions = sorted(i for i, o in enumerate(opts) if o.is_correct)
    assert correct_positions == [1, 3], "a select-TWO item must have exactly two correct options"


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


# --------------------------------------------------------------------------- #
# --reset destructive-guard (fork finding C1: --reset silently deleted every
# member's enrollment and evaluation-attempt history with no check and no
# way to say no)
# --------------------------------------------------------------------------- #


def _make_learner(username):
    user = Usuario(
        usuario=username,
        acceso=proteger_passwd("x"),
        nombre="Reset",
        apellido="Guard",
        correo_electronico=f"{username}@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
        creado_por="test",
    )
    database.session.add(user)
    database.session.commit()
    return user


def test_count_learner_data_is_zero_for_a_fresh_course(cca_db, sample_questions):
    seed._create_course(database, MODELS, _spec_for("CCA-RESET1", sample_questions))
    enrollments, attempts = seed._count_learner_data(database, MODELS, "CCA-RESET1")
    assert (enrollments, attempts) == (0, 0)


def test_count_learner_data_counts_enrollments_and_attempts(cca_db, sample_questions):
    seed._create_course(database, MODELS, _spec_for("CCA-RESET2", sample_questions))
    _make_learner("reset-guard-learner")
    database.session.add(EstudianteCurso(usuario="reset-guard-learner", curso="CCA-RESET2", vigente=True))
    database.session.commit()

    ev = database.session.execute(
        database.select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == "CCA-RESET2")
    ).scalar_one()
    database.session.add(EvaluationAttempt(evaluation_id=ev.id, user_id="reset-guard-learner", score=80.0, passed=True))
    database.session.add(EvaluationAttempt(evaluation_id=ev.id, user_id="reset-guard-learner", score=60.0, passed=False))
    database.session.commit()

    enrollments, attempts = seed._count_learner_data(database, MODELS, "CCA-RESET2")
    assert (enrollments, attempts) == (1, 2)


def test_required_ack_flag_names_the_exact_counts():
    assert seed._required_ack_flag(0, 0) == "--i-know-this-deletes-0-enrollments-and-0-attempts"
    assert seed._required_ack_flag(3, 7) == "--i-know-this-deletes-3-enrollments-and-7-attempts"


def test_main_refuses_reset_with_learner_data_and_no_ack_flag(monkeypatch, cca_db, sample_questions):
    """The gate the audit asked for, exercised through main() itself: a
    --reset against a course with learner data must refuse, and must do so
    BEFORE deleting anything — the course, the enrollment, and the attempt
    must all still exist afterward."""
    seed._create_course(database, MODELS, _spec_for("CCA-RESET3", sample_questions))
    _make_learner("guarded-learner")
    database.session.add(EstudianteCurso(usuario="guarded-learner", curso="CCA-RESET3", vigente=True))
    database.session.commit()

    monkeypatch.setattr(seed, "_require_content_dir", lambda: None)
    monkeypatch.setattr(seed.sys, "argv", ["seed_cca_courses.py", "--reset=CCA-RESET3"])

    with pytest.raises(SystemExit) as exc_info:
        seed.main()
    assert exc_info.value.code == 3

    # Nothing was touched: the refusal happens before _delete_course runs.
    curso = database.session.execute(database.select(Curso).filter_by(codigo="CCA-RESET3")).scalar_one_or_none()
    assert curso is not None
    enrollments, _attempts = seed._count_learner_data(database, MODELS, "CCA-RESET3")
    assert enrollments == 1


def test_main_proceeds_with_reset_when_the_exact_ack_flag_is_given(monkeypatch, cca_db, sample_questions):
    """The other half of the gate: the correctly-named flag lets a real
    --reset through, the course is actually rebuilt, and both the enrollment
    and the evaluation attempt are gone afterward (cascaded by the DB, not
    left orphaned).

    Covers both learner-data shapes in one course: an EstudianteCurso
    enrollment AND an EvaluationAttempt. Deleting a Curso with an enrolled
    student used to crash here (Curso.inscripciones had no passive_deletes,
    so the ORM tried to NULL a NOT NULL FK instead of trusting the DB's own
    ON DELETE CASCADE) — fixed in now_lms/db/__init__.py; this test is what
    proves it rather than working around it.
    """
    seed._create_course(database, MODELS, _spec_for("CCA-RESET4", sample_questions))
    _make_learner("acking-learner")
    database.session.add(EstudianteCurso(usuario="acking-learner", curso="CCA-RESET4", vigente=True))
    ev = database.session.execute(
        database.select(Evaluation).join(CursoSeccion).filter(CursoSeccion.curso == "CCA-RESET4")
    ).scalar_one()
    database.session.add(EvaluationAttempt(evaluation_id=ev.id, user_id="acking-learner", score=90.0, passed=True))
    database.session.commit()

    enrollments, attempts = seed._count_learner_data(database, MODELS, "CCA-RESET4")
    assert (enrollments, attempts) == (1, 1)
    ack_flag = seed._required_ack_flag(enrollments, attempts)

    # _build_specs() reads the private curriculum content this test env does
    # not have; stub it to an empty rebuild so the gate is what's under test,
    # not the content pipeline.
    monkeypatch.setattr(seed, "_require_content_dir", lambda: None)
    monkeypatch.setattr(seed, "_build_specs", lambda: [])
    monkeypatch.setattr(seed.sys, "argv", ["seed_cca_courses.py", "--reset=CCA-RESET4", ack_flag])

    result = seed.main()
    assert result == 0

    curso = database.session.execute(database.select(Curso).filter_by(codigo="CCA-RESET4")).scalar_one_or_none()
    assert curso is None, "an acknowledged --reset must actually delete the course"
    orphaned_enrollment = database.session.execute(
        database.select(EstudianteCurso).filter_by(curso="CCA-RESET4")
    ).scalar_one_or_none()
    assert orphaned_enrollment is None, "the enrollment row must be cascade-deleted, not left orphaned"


def test_reset_refuses_when_learner_data_changes_after_the_check(app, db_session, monkeypatch, capsys):
    """The acknowledged numbers must be enforced at DELETE time, not only at check time.

    `_count_learner_data` reads, then `_delete_course` deletes. Nothing stopped a
    learner enrolling in between, and that record would have been destroyed without
    ever appearing in the count the operator acknowledged. Locking the Curso row does
    not close it either, because a new enrollment inserts into EstudianteCurso, which
    that lock does not cover.

    Simulated by making the second count return more than the first, which is exactly
    what a concurrent enrolment looks like from inside this script. Greptile, PR #78.
    """
    llamadas = {"n": 0}

    def contando(db, models, code):
        llamadas["n"] += 1
        # First pass (the gate) sees 1 enrollment. Second pass (the re-check, inside
        # the deleting transaction) sees a second learner arrive.
        return (1, 0) if llamadas["n"] == 1 else (2, 0)

    # main() calls _require_content_dir() first, and content/cca is gitignored
    # (it lives in the private intent-curriculum repo), so without this the
    # script exits 2 on the missing directory long before it reaches the
    # re-check this test exists to exercise. Both sibling tests that drive
    # main() stub it the same way.
    monkeypatch.setattr(seed, "_require_content_dir", lambda: None)

    monkeypatch.setattr(seed, "_count_learner_data", contando)

    borrados = []
    monkeypatch.setattr(seed, "_delete_course", lambda *a, **k: borrados.append(a) or True)

    monkeypatch.setattr(
        seed.sys,
        "argv",
        ["seed_cca_courses.py", "--reset=CCA-RACE", "--i-know-this-deletes-1-enrollments-and-0-attempts"],
    )

    with pytest.raises(SystemExit) as exc_info:
        seed.main()

    assert exc_info.value.code == 4, f"expected the delete-time refusal (exit 4), got {exc_info.value.code}"
    assert borrados == [], "a course was deleted even though the counts had moved"
    err = capsys.readouterr().err
    assert "changed between the check and the delete" in err
    assert "Nothing was deleted" in err
