# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para la gestión de cupones de descuento.
"""

from datetime import datetime, timedelta, timezone
import pytest
from flask_login import login_user, logout_user
from now_lms.db import database, Usuario, Curso, DocenteCurso, Coupon, EstudianteCurso, Configuracion
from now_lms.auth import proteger_passwd
from now_lms.vistas.courses.coupons import (
    _validate_coupon_permissions,
    _validate_coupon_for_enrollment,
)

@pytest.fixture
def test_users(app, db_session):
    """Crea usuarios de prueba para roles de instructor, estudiante y admin."""
    admin = Usuario(
        usuario="admin_coupon",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_c@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_coupon",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_c@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_coupon",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_c@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, student])
    db_session.commit()
    return {"admin": admin, "instructor": instructor, "student": student}

@pytest.fixture
def test_courses(app, db_session):
    """Crea cursos pagados y gratuitos de prueba."""
    paid_course = Curso(
        codigo="PAID01",
        nombre="Paid Course",
        descripcion_corta="paid",
        descripcion="paid",
        estado="open",
        pagado=True,
        precio=100.0,
    )
    free_course = Curso(
        codigo="FREE01",
        nombre="Free Course",
        descripcion_corta="free",
        descripcion="free",
        estado="open",
        pagado=False,
    )
    db_session.add_all([paid_course, free_course])
    db_session.commit()
    return {"paid": paid_course, "free": free_course}

def test_validate_coupon_permissions_not_found(app, db_session, test_users):
    """Retorna error si el curso no existe."""
    course, error = _validate_coupon_permissions("NON_EXISTENT", test_users["instructor"])
    assert course is None
    assert error == "Curso no encontrado"

def test_validate_coupon_permissions_free_course(app, db_session, test_users, test_courses):
    """Los cupones no están disponibles para cursos gratuitos."""
    course, error = _validate_coupon_permissions("FREE01", test_users["instructor"])
    assert course is None
    assert error == "Los cupones solo están disponibles para cursos pagados"

def test_validate_coupon_permissions_unauthorized(app, db_session, test_users, test_courses):
    """Retorna error si el usuario no es admin ni instructor asignado."""
    course, error = _validate_coupon_permissions("PAID01", test_users["instructor"])
    assert course is None
    assert error == "Solo el instructor del curso puede gestionar cupones"

def test_validate_coupon_permissions_success_instructor(app, db_session, test_users, test_courses):
    """Debe permitir el acceso si el usuario es el instructor asignado."""
    docente_curso = DocenteCurso(
        curso="PAID01",
        usuario=test_users["instructor"].usuario,
        vigente=True,
    )
    db_session.add(docente_curso)
    db_session.commit()

    course, error = _validate_coupon_permissions("PAID01", test_users["instructor"])
    assert course is not None
    assert error is None
    assert course.codigo == "PAID01"

def test_validate_coupon_permissions_success_admin(app, db_session, test_users, test_courses):
    """Debe permitir el acceso si el usuario es administrador."""
    course, error = _validate_coupon_permissions("PAID01", test_users["admin"])
    assert course is not None
    assert error is None

def test_validate_coupon_for_enrollment_no_code(app, db_session, test_users):
    """Debe fallar si no se proporciona el código de cupón."""
    coupon, _, error = _validate_coupon_for_enrollment("PAID01", "", test_users["student"])
    assert coupon is None
    assert error == "No se proporcionó código de cupón"

def test_validate_coupon_for_enrollment_invalid_code(app, db_session, test_users):
    """Debe fallar si el cupón no existe."""
    coupon, _, error = _validate_coupon_for_enrollment("PAID01", "INVALID", test_users["student"])
    assert coupon is None
    assert error == "Código de cupón inválido"

def test_validate_coupon_for_enrollment_already_enrolled(app, db_session, test_users, test_courses):
    """Debe fallar si el estudiante ya está inscrito."""
    coupon_obj = Coupon(
        course_id="PAID01",
        code="PROMO50",
        discount_type="percentage",
        discount_value=50.0,
        created_by="inst_coupon",
    )
    db_session.add(coupon_obj)

    enrollment = EstudianteCurso(
        curso="PAID01",
        usuario=test_users["student"].usuario,
        vigente=True,
    )
    db_session.add(enrollment)
    db_session.commit()

    coupon, _, error = _validate_coupon_for_enrollment("PAID01", "PROMO50", test_users["student"])
    assert coupon is None
    assert error == "No puede aplicar cupón - ya está inscrito en el curso"

def test_validate_coupon_for_enrollment_validation_errors(app, db_session, test_users, test_courses):
    """Prueba diferentes estados inválidos del cupón."""
    # Expirado - usar datetime naive para compatibilidad con SQLite
    expired_coupon = Coupon(
        course_id="PAID01",
        code="EXPIRED",
        discount_type="percentage",
        discount_value=10.0,
        expires_at=datetime.utcnow() - timedelta(days=1),
        created_by="inst_coupon",
    )
    # Límite de usos alcanzado
    used_up_coupon = Coupon(
        course_id="PAID01",
        code="USEDUP",
        discount_type="percentage",
        discount_value=10.0,
        max_uses=1,
        current_uses=1,
        created_by="inst_coupon",
    )
    db_session.add_all([expired_coupon, used_up_coupon])
    db_session.commit()

    _, _, err1 = _validate_coupon_for_enrollment("PAID01", "EXPIRED", test_users["student"])
    assert err1 is not None

    _, _, err2 = _validate_coupon_for_enrollment("PAID01", "USEDUP", test_users["student"])
    assert err2 is not None

def test_validate_coupon_for_enrollment_unverified_email(app, db_session, test_users, test_courses):
    """Debe requerir correo verificado si el descuento es del 100% (gratuito) y el sistema lo exige."""
    coupon_obj = Coupon(
        course_id="PAID01",
        code="FREE100",
        discount_type="percentage",
        discount_value=100.0,
        created_by="inst_coupon",
    )
    db_session.add(coupon_obj)

    # Obtener configuración existente o crear una si no existe
    config = db_session.execute(database.select(Configuracion)).scalar_one_or_none()
    if not config:
        config = Configuracion(
            titulo="Test LMS",
            verify_user_by_email=True,
            r=b"salt_salt_salt_123"
        )
        db_session.add(config)
    else:
        config.verify_user_by_email = True
    db_session.commit()

    # Usuario con correo no verificado
    unverified_student = Usuario(
        usuario="unver_coupon",
        acceso=proteger_passwd("pass"),
        nombre="Unver",
        correo_electronico="unver_c@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=False,
    )
    db_session.add(unverified_student)
    db_session.commit()

    coupon, _, error = _validate_coupon_for_enrollment("PAID01", "FREE100", unverified_student)
    assert coupon is None
    assert "Debe verificar su correo electrónico" in error

def test_routes_list_and_manage_coupons(client, db_session, test_users, test_courses):
    """Prueba las rutas de listar, crear, editar y eliminar cupones."""
    # Asignar instructor al curso
    docente_curso = DocenteCurso(
        curso="PAID01",
        usuario=test_users["instructor"].usuario,
        vigente=True,
    )
    db_session.add(docente_curso)
    db_session.commit()

    # Login como instructor
    client.post("/user/login", data={"usuario": "inst_coupon", "acceso": "pass"})

    # 1. Crear un cupón via POST
    response_create = client.post(
        "/course/PAID01/coupons/new",
        data={
            "code": "PROMO50",
            "discount_type": "percentage",
            "discount_value": "50.0",
            "max_uses": "10",
        },
        follow_redirects=True,
    )
    assert response_create.status_code == 200

    # Verificar cupón creado en la DB
    coupon = db_session.execute(database.select(Coupon).filter_by(code="PROMO50")).scalar_one_or_none()
    assert coupon is not None
    assert coupon.discount_value == 50.0

    # 2. Listar cupones
    response_list = client.get("/course/PAID01/coupons/")
    assert response_list.status_code == 200
    assert b"PROMO50" in response_list.data

    # 3. Editar el cupón
    response_edit = client.post(
        f"/course/PAID01/coupons/{coupon.id}/edit",
        data={
            "code": "PROMO50_NEW",
            "discount_type": "percentage",
            "discount_value": "40.0",
            "max_uses": "5",
        },
        follow_redirects=True,
    )
    assert response_edit.status_code == 200
    db_session.refresh(coupon)
    assert coupon.code == "PROMO50_NEW"
    assert coupon.discount_value == 40.0

    # 4. Eliminar el cupón
    response_delete = client.post(
        f"/course/PAID01/coupons/{coupon.id}/delete",
        follow_redirects=True,
    )
    assert response_delete.status_code == 200
    coupon_deleted = db_session.execute(database.select(Coupon).filter_by(code="PROMO50_NEW")).scalar_one_or_none()
    assert coupon_deleted is None
