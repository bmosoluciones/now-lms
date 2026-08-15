# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""Practice is its own area, keyed by certification and outside courses.

Course was the wrong key and the data proved it: CCA-F alone carries questions for
two credentials, so a course-scoped view showed a member 12 domains — the 5 for
Architect Foundations mashed together with the 7 for Architect Professional. Worse,
Architect Professional had no course of its own at all, so its domains were
unreachable.

Exercised through the URL, not the helper: the decorators, the 404s and the rendered
page are the parts a refactor silently breaks.
"""

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import CursoSeccion, Curso, Evaluation, Question, QuestionOption, Usuario, database

PASSWORD = "practice-cert-pass"
COURSE = "PCT-1"


def _user(usuario):
    existing = database.session.execute(database.select(Usuario).filter_by(usuario=usuario)).scalars().first()
    if existing is not None:
        return existing
    user = Usuario(
        usuario=usuario,
        acceso=proteger_passwd(PASSWORD),
        nombre="Cert",
        apellido="Tester",
        correo_electronico=f"{usuario}@example.invalid",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    database.session.add(user)
    database.session.commit()
    return user


@pytest.fixture
def two_certifications(app):
    """One course carrying questions for TWO certifications — the real CCA-F shape."""
    with app.app_context():
        if database.session.execute(database.select(Curso).filter_by(codigo=COURSE)).scalars().first() is None:
            database.session.add(
                Curso(
                    nombre="Mixed course",
                    codigo=COURSE,
                    descripcion_corta="s",
                    descripcion="l",
                    estado="open",
                    publico=False,
                    modalidad="self_paced",
                    nivel=1,
                    duracion=1,
                    pagado=False,
                    auditable=False,
                    certificado=False,
                )
            )
            database.session.commit()
            seccion = CursoSeccion(curso=COURSE, nombre="S", descripcion="d", indice=1, estado=True)
            database.session.add(seccion)
            database.session.commit()
            ev = Evaluation(
                section_id=seccion.id, title="Q", description="d", is_exam=False, passing_score=72.0, max_attempts=None
            )
            database.session.add(ev)
            database.session.commit()

            rows = [
                ("Foundations item.", "found-arch", "Agentic Architecture", "CCA-F", "Architect — Foundations"),
                ("Professional item.", "pro-integration", "Integration", "CCA-P", "Architect — Professional"),
            ]
            for index, (text, dkey, dname, ckey, cname) in enumerate(rows, start=1):
                q = Question(
                    evaluation_id=ev.id,
                    type="multiple",
                    text=text,
                    explanation="Because.",
                    order=index,
                    domain_key=dkey,
                    domain_name=dname,
                    certification_key=ckey,
                    certification_name=cname,
                )
                database.session.add(q)
                database.session.commit()
                database.session.add(QuestionOption(question_id=q.id, text="right", is_correct=True))
                database.session.add(QuestionOption(question_id=q.id, text="wrong", is_correct=False))
                database.session.commit()
        yield


def _login(client, usuario):
    client.post("/user/login", data={"usuario": usuario, "acceso": PASSWORD}, follow_redirects=False)


def test_the_two_certifications_are_listed_separately(app, client, two_certifications):
    with app.app_context():
        _user("cert-member")
    _login(client, "cert-member")

    body = client.get("/practice").get_data(as_text=True)

    assert "Architect — Foundations" in body
    assert "Architect — Professional" in body


def test_a_certification_shows_only_its_own_domains(app, client, two_certifications):
    """The defect this design exists to fix: one course, two credentials, mashed."""
    with app.app_context():
        _user("cert-split")
    _login(client, "cert-split")

    body = client.get("/practice/CCA-P").get_data(as_text=True)

    assert "Integration" in body
    assert "Agentic Architecture" not in body, "another certification's domain must not appear"


def test_a_drill_serves_that_domains_questions(app, client, two_certifications):
    with app.app_context():
        _user("cert-drill")
    _login(client, "cert-drill")

    body = client.get("/practice/CCA-P/pro-integration").get_data(as_text=True)

    assert "Professional item." in body
    assert "Foundations item." not in body


def test_no_course_enrollment_is_required(app, client, two_certifications):
    """Practice sits outside courses: a member enrolled in nothing still gets in."""
    with app.app_context():
        _user("cert-unenrolled")
    _login(client, "cert-unenrolled")

    assert client.get("/practice").status_code == 200
    assert client.get("/practice/CCA-P").status_code == 200


def test_unknown_certification_and_domain_are_404(app, client, two_certifications):
    with app.app_context():
        _user("cert-404")
    _login(client, "cert-404")

    assert client.get("/practice/NOPE").status_code == 404
    assert client.get("/practice/CCA-P/nope").status_code == 404


def test_an_anonymous_visitor_is_sent_to_login(client, two_certifications):
    response = client.get("/practice", follow_redirects=False)
    assert response.status_code in (302, 401)
