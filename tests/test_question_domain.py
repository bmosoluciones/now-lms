# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Questions carry the domain their bank declares.

Until this landed, `_build_specs` read each item's `domainKey` only to group
questions into sections and then threw it away. A full-length exam draws items from
every domain into ONE evaluation, so nothing recorded which item examined what — a
result could not be scored per domain, and no bank could be drilled one domain at a
time.

The importer's own synthetic fixtures are used rather than a real bank so these run
without the private curriculum checkout; a separate content-gated test asserts the
real banks actually populate.
"""

import importlib.util
import pathlib

import pytest

from now_lms.db import CursoSeccion, Evaluation, Question, database

# `cca_db` builds the in-memory row graph these tests need, and MODELS is the
# importer's model map. Bound by assignment rather than imported: pytest still
# discovers the fixture in this module's namespace, and ruff does not read it as a
# redefinition every time a test declares it as a parameter (F811).
from tests import test_cca_seed as _seed_tests

MODELS = _seed_tests.MODELS
cca_db = _seed_tests.cca_db

_SEED_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "seed_cca_courses.py"
_spec = importlib.util.spec_from_file_location("seed_cca_courses_domain", _SEED_PATH)
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

_content_required = pytest.mark.skipif(
    not (seed.BANKS_DIR / "questions-associate.json").is_file(),
    reason="curriculum content not present; set CCA_CONTENT_DIR to a checkout",
)


def test_the_model_exposes_both_domain_columns():
    """A column typo here would silently drop the value the seeder writes."""
    columns = {column.name for column in Question.__table__.columns}
    assert "domain_key" in columns
    assert "domain_name" in columns
    assert Question.__table__.c.domain_key.nullable, "existing questions have no domain"
    assert Question.__table__.c.domain_name.nullable
    assert Question.__table__.c.domain_key.index, "the only reason to store it is to group by it"


@_content_required
def test_every_item_in_every_bank_declares_a_domain():
    """The seeder's fallback should never actually be needed by the real curriculum.

    If a future bank arrives without `domainKey`, this fails here rather than showing
    up later as an unlabelled slice on a member's result page.
    """
    unlabelled = {}
    for path in sorted(seed.BANKS_DIR.glob("*.json")):
        missing = [
            item.get("id", "<no id>")
            for item in seed._load_bank(path.name)
            if not (item.get("domainKey") or "").strip()
        ]
        if missing:
            unlabelled[path.name] = missing
    assert not unlabelled, f"banks with items missing domainKey: {unlabelled}"


def test_seeded_questions_carry_the_bank_domain(cca_db):
    """The end the whole feature rests on: the value reaches the row."""
    questions = [
        {
            "text": "A question from the first domain.",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": 1,
            "rationale": "beta is correct.",
            "source": "Synthetic fixture",
            "domainKey": "assoc-prompting",
            "domainName": "Prompting and Task Execution",
        },
        {
            "text": "A question from the second domain.",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": 2,
            "rationale": "gamma is correct.",
            "source": "Synthetic fixture",
            "domainKey": "assoc-governance",
            "domainName": "Governance, Risk, and Responsible Use",
        },
    ]
    seed._create_course(database, MODELS, _spec_for("CCA-DOM1", questions))

    rows = {question.text: question for question in _questions_for("CCA-DOM1")}
    first = rows["A question from the first domain."]
    second = rows["A question from the second domain."]
    assert first.domain_key == "assoc-prompting"
    assert first.domain_name == "Prompting and Task Execution"
    assert second.domain_key == "assoc-governance"
    assert second.domain_name == "Governance, Risk, and Responsible Use"


def test_one_evaluation_can_hold_several_domains(cca_db):
    """A full-length exam is the case sections could never represent.

    Grouping by section was the old proxy for a domain. It cannot describe a mock exam,
    where every domain appears inside a single evaluation — which is precisely the
    surface a member is asked to prove proficiency on.
    """
    questions = [
        {
            "text": f"Item {index} of the mock.",
            "options": ["alpha", "beta", "gamma", "delta"],
            "answerIndex": 0,
            "rationale": "alpha is correct.",
            "source": "Synthetic fixture",
            "domainKey": key,
            "domainName": key.replace("-", " ").title(),
        }
        for index, key in enumerate(["d-one", "d-two", "d-one", "d-three"])
    ]
    spec = _spec_for("CCA-DOM2", None)
    spec["mock_questions"] = questions
    seed._create_course(database, MODELS, spec)

    seeded = _questions_for("CCA-DOM2")
    assert len(seeded) == 4
    assert {question.domain_key for question in seeded} == {"d-one", "d-two", "d-three"}
    assert sum(1 for question in seeded if question.domain_key == "d-one") == 2


def test_an_item_with_only_a_numeric_domain_still_gets_labelled(cca_db):
    """Older bank shapes carry `domain` as an integer and no `domainKey`.

    Falling back keeps those usable instead of silently unlabelled — an unlabelled item
    is invisible on a per-domain result, which reads as a scoring bug rather than as
    missing metadata.
    """
    questions = [
        {
            "text": "An item from a bank that predates domainKey.",
            "options": ["alpha", "beta"],
            "answerIndex": 0,
            "rationale": "alpha is correct.",
            "source": "Synthetic fixture",
            "domain": 3,
        }
    ]
    seed._create_course(database, MODELS, _spec_for("CCA-DOM3", questions))
    questions_seeded = _questions_for("CCA-DOM3")
    assert len(questions_seeded) == 1
    question = questions_seeded[0]
    assert question.domain_key == "3"
    assert question.domain_name is None


def _questions_for(code):
    """Every question under one course code.

    Scoped deliberately: `cca_db` does not roll back between tests in a session, so a
    query over the whole `question` table returns rows other tests seeded and the
    assertion drifts with test ordering.
    """
    section_ids = [
        section.id
        for section in database.session.execute(database.select(CursoSeccion).filter_by(curso=code)).scalars()
    ]
    evaluation_ids = [
        evaluation.id
        for evaluation in database.session.execute(
            database.select(Evaluation).filter(Evaluation.section_id.in_(section_ids))
        ).scalars()
    ]
    return list(
        database.session.execute(
            database.select(Question).filter(Question.evaluation_id.in_(evaluation_ids))
        ).scalars()
    )


def _spec_for(code, questions):
    return {
        "codigo": code,
        "nombre": "Domain test course",
        "nivel": 1,
        "duracion": 1,
        "descripcion_corta": "short",
        "descripcion": "long",
        "sections": (
            [{"nombre": "Section", "descripcion": "d", "lesson": "# Lesson\n\nbody", "questions": questions}]
            if questions
            else [{"nombre": "Section", "descripcion": "d", "lesson": "# Lesson\n\nbody"}]
        ),
        "mock_questions": None,
    }
