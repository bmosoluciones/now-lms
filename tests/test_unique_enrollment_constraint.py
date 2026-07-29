# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""One enrollment per (usuario, curso), enforced by the database.

The enrollment paths upsert, so duplicates should never reach the table — this
covers the case where something gets past them anyway.

The migration's dedup path (collapsing duplicates that already exist, and
repointing anything referencing a discarded row) is exercised against real
PostgreSQL rather than here: SQLite is too permissive about constraints and
foreign keys for that to prove anything. See the PR for that run.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from now_lms.auth import proteger_passwd
from now_lms.db import Curso, EstudianteCurso, Usuario, database


@pytest.fixture()
def enrolled_student(app):
    """A student with exactly one enrollment in a free course."""
    with app.app_context():
        s = database.session
        s.add(
            Curso(
                nombre="Unique constraint course",
                codigo="UQCHK",
                descripcion="Unique-constraint test course.",
                descripcion_corta="Unique check.",
                estado="open",
                publico=True,
                pagado=False,
                auditable=False,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        s.add(
            Usuario(
                usuario="uq@example.test",
                acceso=proteger_passwd("uq-test-pw-123"),
                nombre="Unique",
                apellido="Check",
                correo_electronico="uq@example.test",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
                creado_por="test",
            )
        )
        s.flush()
        s.add(EstudianteCurso(curso="UQCHK", usuario="uq@example.test", vigente=True, creado_por="test"))
        s.commit()
    return "uq@example.test", "UQCHK"


def test_the_model_declares_the_constraint(app):
    """The constraint has to be on the model, or a fresh install will not have it."""
    names = {constraint.name for constraint in EstudianteCurso.__table__.constraints}
    assert "uq_estudiante_curso_usuario_curso" in names


def test_a_second_enrollment_row_is_rejected(app, enrolled_student):
    """The point of the constraint: the same pair cannot be inserted twice."""
    usuario, curso = enrolled_student
    with app.app_context():
        database.session.add(EstudianteCurso(curso=curso, usuario=usuario, vigente=True, creado_por="test"))
        with pytest.raises(IntegrityError):
            database.session.commit()
        database.session.rollback()


def test_the_same_student_can_still_join_another_course(app, enrolled_student):
    """The constraint is on the pair, not on either column alone."""
    usuario, _ = enrolled_student
    with app.app_context():
        s = database.session
        s.add(
            Curso(
                nombre="Second course",
                codigo="UQCHK2",
                descripcion="Second course.",
                descripcion_corta="Second.",
                estado="open",
                publico=True,
                pagado=False,
                auditable=False,
                certificado=False,
                modalidad="self_paced",
                creado_por="test",
            )
        )
        s.flush()
        s.add(EstudianteCurso(curso="UQCHK2", usuario=usuario, vigente=True, creado_por="test"))
        s.commit()

        rows = s.execute(database.select(EstudianteCurso).filter_by(usuario=usuario)).scalars().all()
        assert len(rows) == 2
