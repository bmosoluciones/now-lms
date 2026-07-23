# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.
"""
Tests unitarios y de integración para la gestión de programas de estudio (vistas/programs.py).
"""

from datetime import datetime
import pytest
from flask_login import login_user, logout_user
from now_lms.cache import cache
from now_lms.db import (
    database,
    Usuario,
    Curso,
    Programa,
    ProgramaCurso,
    ProgramaEstudiante,
    Categoria,
    Etiqueta,
    CategoriaPrograma,
    EtiquetaPrograma,
)
from now_lms.auth import proteger_passwd

@pytest.fixture
def prog_setup(app, db_session):
    """Configura usuarios, cursos y categorías para pruebas de programas."""
    admin = Usuario(
        usuario="admin_p",
        acceso=proteger_passwd("pass"),
        nombre="Admin",
        correo_electronico="admin_p@example.com",
        tipo="admin",
        activo=True,
    )
    instructor = Usuario(
        usuario="inst_p",
        acceso=proteger_passwd("pass"),
        nombre="Instructor",
        correo_electronico="inst_p@example.com",
        tipo="instructor",
        activo=True,
    )
    student = Usuario(
        usuario="stud_p",
        acceso=proteger_passwd("pass"),
        nombre="Student",
        correo_electronico="stud_p@example.com",
        tipo="student",
        activo=True,
        correo_electronico_verificado=True,
    )
    db_session.add_all([admin, instructor, student])

    curso1 = Curso(
        codigo="C01",
        nombre="Curso 1",
        descripcion_corta="desc1",
        descripcion="desc1",
        estado="open",
    )
    curso2 = Curso(
        codigo="C02",
        nombre="Curso 2",
        descripcion_corta="desc2",
        descripcion="desc2",
        estado="open",
    )
    db_session.add_all([curso1, curso2])

    cat = Categoria(nombre="Backend", descripcion="Web programming")
    tag = Etiqueta(nombre="python", color="blue")
    db_session.add_all([cat, tag])
    db_session.commit()

    return {
        "admin": admin,
        "instructor": instructor,
        "student": student,
        "curso1": curso1,
        "curso2": curso2,
        "categoria": cat,
        "etiqueta": tag,
    }

def test_routes_create_program(client, db_session, prog_setup):
    """Prueba la creación de un nuevo programa por un instructor."""
    # Login instructor
    client.post("/user/login", data={"usuario": "inst_p", "acceso": "pass"})

    response = client.post(
        "/program/new",
        data={
            "nombre": "Especialización Python",
            "descripcion": "Aprende python desde cero",
            "codigo": "PYSP01",
            "precio": "199.99",
            "categoria": str(prog_setup["categoria"].id),
            "etiquetas": [str(prog_setup["etiqueta"].id)],
            "certificado": True,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    # Verificar creación en DB
    prog = db_session.execute(database.select(Programa).filter_by(codigo="PYSP01")).scalars().first()
    assert prog is not None
    assert prog.nombre == "Especialización Python"

    # Verificar asociación de categoría y etiquetas
    cat_p = db_session.execute(database.select(CategoriaPrograma).filter_by(programa=prog.id)).scalars().first()
    assert cat_p is not None
    assert cat_p.categoria == prog_setup["categoria"].id

def test_routes_list_programs(client, db_session, prog_setup):
    """Prueba listar programas para instructor y admin."""
    # Crear programa de prueba
    prog = Programa(
        codigo="PROG_LIST",
        nombre="Programa List",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Clear cache before retrieving to avoid stale lists
    cache.clear()

    # Instructor login
    client.post("/user/login", data={"usuario": "inst_p", "acceso": "pass"})
    response_inst = client.get("/program/list")
    assert response_inst.status_code == 200
    assert b"Programa List" in response_inst.data

    # Admin login
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})
    response_admin = client.get("/program/list")
    assert response_admin.status_code == 200

def test_routes_edit_program(client, db_session, prog_setup):
    """Prueba editar programa como admin."""
    prog = Programa(
        codigo="PROG_EDIT",
        nombre="Programa Edit",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
        estado="draft",
    )
    db_session.add(prog)
    db_session.commit()

    # Login como admin
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})

    # Intentar editar
    response_edit = client.post(
        f"/program/{prog.id}/edit",
        data={
            "nombre": "Programa Edit Actualizado",
            "descripcion": "desc actualizada",
            "codigo": "PROG_EDIT",
            "precio": "50.0",
            "estado": "draft",
        },
        follow_redirects=True,
    )
    assert response_edit.status_code == 200
    db_session.refresh(prog)
    assert prog.nombre == "Programa Edit Actualizado"

def test_routes_explore_programs(client, db_session, prog_setup):
    """Prueba explorar programas públicos."""
    prog = Programa(
        codigo="PROG_EXP",
        nombre="Programa Explore",
        descripcion="desc",
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Ver lista de programas públicos
    response = client.get("/program/explore")
    assert response.status_code == 200
    assert b"Programa Explore" in response.data

def test_routes_enroll_and_take_program(client, db_session, prog_setup):
    """Prueba la inscripción y toma de un programa por un estudiante."""
    prog = Programa(
        codigo="PROG_TAKE",
        nombre="Programa Take",
        descripcion="desc",
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Login estudiante
    client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})

    # Inscribir
    response_enroll = client.post(f"/program/PROG_TAKE/enroll", follow_redirects=True)
    assert response_enroll.status_code == 200
    assert b"Te has inscrito exitosamente" in response_enroll.data

    # Tomar programa
    response_take = client.get(f"/program/PROG_TAKE/take")
    assert response_take.status_code == 200

def test_routes_manage_courses_and_admin_enroll(client, db_session, prog_setup):
    """Prueba asociar cursos a programas e inscripción administrativa."""
    prog = Programa(
        codigo="PROG_MAN",
        nombre="Programa Manage",
        descripcion="desc",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.commit()

    # Login como admin
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})

    # 1. Asociar un curso
    response_add = client.post(
        f"/program/PROG_MAN/courses/manage",
        data={"action": "add_course", "curso_codigo": "C01"},
        follow_redirects=True,
    )
    assert response_add.status_code == 200

    # Verificar que el curso está asociado
    pc = db_session.execute(database.select(ProgramaCurso).filter_by(programa="PROG_MAN", curso="C01")).scalars().first()
    assert pc is not None

    # 2. Inscripción administrativa
    response_enroll = client.post(
        f"/program/PROG_MAN/admin/enroll",
        data={"student_username": "stud_p", "bypass_payment": True, "notes": "Notas admin"},
        follow_redirects=True,
    )
    assert response_enroll.status_code == 200

    # Verificar enrolamiento
    pe = db_session.execute(database.select(ProgramaEstudiante).filter_by(programa=prog.id, usuario="stud_p")).scalars().first()
    assert pe is not None

    # Ver lista de enrollments
    response_list = client.get(f"/program/PROG_MAN/admin/enrollments")
    assert response_list.status_code == 200

    # 3. Desinscripción administrativa
    response_unenroll = client.post(
        f"/program/PROG_MAN/admin/unenroll/stud_p",
        follow_redirects=True,
    )
    assert response_unenroll.status_code == 200

    pe_deleted = db_session.execute(database.select(ProgramaEstudiante).filter_by(programa=prog.id, usuario="stud_p")).scalars().first()
    assert pe_deleted is None


def test_program_free_enrollment_auto_enroll_courses(client, db_session, prog_setup):
    """Verifica que la inscripción a un programa gratuito inscriba al estudiante en todos sus cursos."""
    prog = Programa(
        codigo="PROG_FREE",
        nombre="Programa Gratis",
        descripcion="un programa gratis",
        precio=0.0,
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.flush()

    # Asociar cursos al programa
    pc1 = ProgramaCurso(programa="PROG_FREE", curso="C01", creado_por=prog_setup["instructor"].usuario)
    pc2 = ProgramaCurso(programa="PROG_FREE", curso="C02", creado_por=prog_setup["instructor"].usuario)
    db_session.add_all([pc1, pc2])
    db_session.commit()

    # Login estudiante
    client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})

    # Inscribirse al programa
    response = client.post("/program/PROG_FREE/enroll", follow_redirects=True)
    assert response.status_code == 200

    db_session.rollback()

    # Verificar que el estudiante está inscrito en el programa
    pe = db_session.execute(database.select(ProgramaEstudiante).filter_by(usuario="stud_p", programa=prog.id)).scalar_one_or_none()
    assert pe is not None

    # Verificar que el estudiante está inscrito en los dos cursos asociados con un Pago completado
    from now_lms.db import EstudianteCurso, Pago
    ec1 = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C01", vigente=True)).scalar_one_or_none()
    ec2 = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C02", vigente=True)).scalar_one_or_none()
    assert ec1 is not None
    assert ec2 is not None

    p1 = db_session.execute(database.select(Pago).filter_by(id=ec1.pago)).scalar_one_or_none()
    p2 = db_session.execute(database.select(Pago).filter_by(id=ec2.pago)).scalar_one_or_none()
    assert p1 is not None
    assert p1.estado == "completed"
    assert p1.monto == 0
    assert p2 is not None
    assert p2.estado == "completed"
    assert p2.monto == 0


def test_program_paid_enrollment_creates_pending_pago(client, db_session, prog_setup):
    """Verifica que la inscripción a un programa de pago cree un Pago pendiente."""
    prog = Programa(
        codigo="PROG_PAID",
        nombre="Programa de Pago",
        descripcion="un programa de pago",
        precio=150.0,
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)

    # Crear configuración de PayPal de prueba para habilitar PayPal pagos
    from now_lms.db import PaypalConfig, Configuracion
    paypal_cfg = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if not paypal_cfg:
        paypal_cfg = PaypalConfig(enable=True, sandbox=True, paypal_sandbox="fake_client")
        db_session.add(paypal_cfg)
    else:
        paypal_cfg.enable = True
    db_session.commit()

    # Login estudiante
    client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})

    # Inscribirse al programa
    response = client.post("/program/PROG_PAID/enroll", follow_redirects=True)
    assert response.status_code == 200
    assert b"Pago" in response.data or b"Procesar Pago" in response.data or b"PayPal" in response.data

    db_session.rollback()
    prog_db = db_session.execute(database.select(Programa).filter_by(codigo="PROG_PAID")).scalar_one()

    # Verificar Pago pendiente creado
    from now_lms.db import Pago
    pago = db_session.execute(database.select(Pago).filter_by(usuario="stud_p", programa=prog_db.id, estado="pending")).scalar_one_or_none()
    assert pago is not None
    assert float(pago.monto) == 150.0


def test_program_paypal_payment_confirmation(client, db_session, prog_setup):
    """Verifica que la confirmación del pago de PayPal complete el pago e inscriba al usuario."""
    prog = Programa(
        codigo="PROG_PAY",
        nombre="Programa de Pago con PayPal",
        descripcion="un programa de pago",
        precio=200.0,
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.flush()

    # Asociar un curso
    pc = ProgramaCurso(programa="PROG_PAY", curso="C01", creado_por=prog_setup["instructor"].usuario)
    db_session.add(pc)
    db_session.commit()

    # Crear configuración de PayPal de prueba
    from now_lms.db import PaypalConfig, Configuracion
    from now_lms.auth import proteger_secreto
    paypal_cfg = db_session.execute(database.select(PaypalConfig)).scalars().first()
    if not paypal_cfg:
        paypal_cfg = PaypalConfig(enable=True, sandbox=True, paypal_sandbox="fake_client", paypal_sandbox_secret=proteger_secreto("fake_secret"))
        db_session.add(paypal_cfg)
    else:
        paypal_cfg.enable = True
        paypal_cfg.sandbox = True
        paypal_cfg.paypal_sandbox = "fake_client"
        paypal_cfg.paypal_sandbox_secret = proteger_secreto("fake_secret")

    config_site = db_session.execute(database.select(Configuracion)).scalars().first()
    if not config_site:
        config_site = Configuracion(titulo="NOW LMS", moneda="USD")
        db_session.add(config_site)

    # Crear pago pendiente para el programa
    from now_lms.db import Pago
    pago = Pago(
        usuario="stud_p",
        programa=prog.id,
        curso=None,
        moneda="USD",
        monto=200.0,
        estado="pending",
        metodo="paypal",
        nombre="Student",
        apellido="LMS",
        correo_electronico="stud_p@example.com",
    )
    db_session.add(pago)
    db_session.commit()

    # Mock PayPal SDK token and order verification
    import unittest
    import unittest.mock as mock
    with unittest.mock.patch("now_lms.vistas.paypal.get_paypal_access_token", return_value="fake_access_token"), \
         unittest.mock.patch("now_lms.vistas.paypal.verify_paypal_payment", return_value={
             "verified": True,
             "status": "COMPLETED",
             "amount": "200.00",
             "currency": "USD",
             "payer_id": "fake_payer_id",
         }):

        # Login estudiante
        client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})

        # Confirmar pago
        response = client.post(
            "/paypal_checkout/confirm_payment",
            json={
                "orderID": "fake_order_123",
                "payerID": "fake_payer_id",
                "courseCode": "PROG_PAY",
                "amount": "200.00",
                "currency": "USD"
            }
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        db_session.rollback()
        prog_db = db_session.execute(database.select(Programa).filter_by(codigo="PROG_PAY")).scalar_one()

        # Verificar Pago completado
        pago_db = db_session.execute(database.select(Pago).filter_by(id=pago.id)).scalar_one()
        assert pago_db.estado == "completed"
        assert pago_db.referencia == "fake_order_123"

        # Verificar inscripciones creadas
        pe = db_session.execute(database.select(ProgramaEstudiante).filter_by(usuario="stud_p", programa=prog_db.id)).scalar_one_or_none()
        assert pe is not None

        from now_lms.db import EstudianteCurso
        ec = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C01", vigente=True)).scalar_one_or_none()
        assert ec is not None


def test_program_course_add_remove_edge_cases(client, db_session, prog_setup):
    """Verifica que agregar/eliminar un curso a un programa asocie/desasocie a los estudiantes existentes."""
    prog = Programa(
        codigo="PROG_EDGE",
        nombre="Programa Edge Cases",
        descripcion="programa de prueba de casos borde",
        precio=0.0,
        publico=True,
        estado="open",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)
    db_session.flush()

    # Asociar primer curso
    pc1 = ProgramaCurso(programa="PROG_EDGE", curso="C01", creado_por=prog_setup["instructor"].usuario)
    db_session.add(pc1)
    db_session.commit()

    # Login estudiante e inscribirse al programa
    client.post("/user/login", data={"usuario": "stud_p", "acceso": "pass"})
    client.post("/program/PROG_EDGE/enroll", follow_redirects=True)

    db_session.rollback()

    # Verificar inscripción al curso C01
    from now_lms.db import EstudianteCurso
    ec1 = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C01", vigente=True)).scalar_one_or_none()
    assert ec1 is not None

    # Login como admin
    client.get("/user/logout")
    client.post("/user/login", data={"usuario": "admin_p", "acceso": "pass"})

    # 1. Agregar nuevo curso C02 al programa PROG_EDGE
    response_add = client.post(
        "/program/PROG_EDGE/courses/manage",
        data={"action": "add_course", "curso_codigo": "C02"},
        follow_redirects=True,
    )
    assert response_add.status_code == 200

    db_session.rollback()

    # Verificar que el estudiante se inscribió automáticamente en C02
    ec2 = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C02", vigente=True)).scalar_one_or_none()
    assert ec2 is not None

    # 2. Eliminar curso C01 del programa PROG_EDGE
    response_remove = client.post(
        "/program/PROG_EDGE/courses/manage",
        data={"action": "remove_course", "curso_codigo": "C01"},
        follow_redirects=True,
    )
    assert response_remove.status_code == 200

    db_session.rollback()

    # Verificar que el estudiante fue desinscrito (vigente=False) de C01
    ec1_deleted = db_session.execute(database.select(EstudianteCurso).filter_by(usuario="stud_p", curso="C01")).scalar_one_or_none()
    assert ec1_deleted is not None
    assert ec1_deleted.vigente is False


def test_program_certificate_snapshot(app, client, db_session, prog_setup):
    """Verifica que el certificado de programa cree un snapshot estático e independiente de los cursos."""
    from now_lms.db import Certificado, Certificacion, CertificacionPrograma
    from now_lms.vistas.programs import _emitir_certificado_programa

    prog = Programa(
        codigo="PROG_SNAP",
        nombre="Programa Snapshot",
        descripcion="programa de snapshot",
        precio=0.0,
        publico=True,
        estado="open",
        certificado=True,
        plantilla_certificado="plat_p",
        creado_por=prog_setup["instructor"].usuario,
    )
    db_session.add(prog)

    # Crear plantilla de certificado
    plat = Certificado(
        code="plat_p",
        titulo="Plantilla de Prueba",
        html="""
            <html>
                <body>
                    <h1>Certificado de Programa</h1>
                    {% set cursos_completados = certificacion_programa.get_cursos_completados() %}
                    {% for curso_codigo in cursos_completados %}
                        {% set curso = database.session.execute(database.select(Curso).filter_by(codigo=curso_codigo)).scalar_one_or_none() %}
                        <div>{{ curso_codigo }}: {{ curso.nombre if curso else 'No encontrado' }}</div>
                    {% endfor %}
                </body>
            </html>
        """,
        css="",
    )
    db_session.add(plat)

    # Cursos asociados
    pc1 = ProgramaCurso(programa="PROG_SNAP", curso="C01", creado_por=prog_setup["instructor"].usuario)
    pc2 = ProgramaCurso(programa="PROG_SNAP", curso="C02", creado_por=prog_setup["instructor"].usuario)
    db_session.add_all([pc1, pc2])
    db_session.commit()

    # Emitir certificado de programa para stud_p within a request context since it uses flash()
    with app.test_request_context():
        _emitir_certificado_programa("PROG_SNAP", "stud_p", "plat_p")

    db_session.rollback()
    prog_db = db_session.execute(database.select(Programa).filter_by(codigo="PROG_SNAP")).scalar_one()

    # Verificar certificado creado con cursos_snapshot correcto
    cert_prog = db_session.execute(database.select(CertificacionPrograma).filter_by(usuario="stud_p", programa=prog_db.id)).scalar_one_or_none()
    assert cert_prog is not None
    assert cert_prog.cursos_snapshot is not None
    assert "C01" in cert_prog.cursos_snapshot
    assert "C02" in cert_prog.cursos_snapshot

    # Renderizar el certificado
    response = client.get(f"/certificate/program/view/{cert_prog.id}/")
    assert response.status_code == 200
    assert b"C01: Curso 1" in response.data
    assert b"C02: Curso 2" in response.data

    # CASO BORDE DE SNAPSHOT: si eliminamos el curso C01 de la base de datos o lo desasociamos,
    # el certificado debe SEGUIR renderizando C01 con su nombre correcto ("Curso 1") porque es un snapshot!
    db_session.delete(prog_setup["curso1"])
    db_session.commit()

    response_after = client.get(f"/certificate/program/view/{cert_prog.id}/")
    assert response_after.status_code == 200
    # Sigue renderizando "Curso 1" gracias a nuestro DatabaseSnapshotWrapper!
    assert b"C01: Curso 1" in response_after.data
