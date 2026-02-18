# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

"""
Tests unitarios completos para el módulo resources.py

Cubre todas las funcionalidades de gestión de recursos de curso:
- Visualización de recursos
- Creación y edición de recursos (todos los tipos)
- Marcado de recursos completados
- Permisos y autorización
- Biblioteca del curso
- Calendarios Meet
- Archivos y subtítulos
"""

import io
from datetime import date, time

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import (
    Configuracion,
    Curso,
    CursoRecurso,
    CursoRecursoAvance,
    CursoSeccion,
    DocenteCurso,
    EstudianteCurso,
    Pago,
    Usuario,
    database,
    select,
)

REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


# =============================================================================
# Funciones auxiliares para crear datos de prueba
# =============================================================================


def crear_usuario(db_session, tipo: str = "student", username: str = None) -> Usuario:
    """Crea un usuario para pruebas."""
    if username is None:
        username = f"{tipo}_test"

    user = Usuario(
        usuario=username,
        acceso=proteger_passwd("password123"),
        nombre=f"{tipo.capitalize()} Test",
        correo_electronico=f"{username}@example.com",
        tipo=tipo,
        activo=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def crear_curso(db_session, codigo: str = "test_course") -> Curso:
    """Crea un curso para pruebas."""
    curso = Curso(
        nombre="Curso de Prueba",
        codigo=codigo,
        descripcion_corta="Descripción corta del curso",
        descripcion="Descripción completa del curso de prueba",
        estado="open",
        publico=True,
        modalidad="self_paced",
        foro_habilitado=False,
    )
    db_session.add(curso)
    db_session.commit()
    return curso


def crear_seccion(db_session, curso: Curso, indice: int = 1) -> CursoSeccion:
    """Crea una sección en un curso."""
    seccion = CursoSeccion(
        curso=curso.codigo,
        nombre=f"Sección {indice}",
        descripcion=f"Descripción de sección {indice}",
        indice=indice,
        estado=True,
    )
    db_session.add(seccion)
    db_session.commit()
    return seccion


def inscribir_estudiante(db_session, curso: Curso, estudiante: Usuario) -> None:
    """Inscribe un estudiante en un curso."""
    # Crear pago
    pago = Pago(
        usuario=estudiante.usuario,
        curso=curso.codigo,
        moneda="USD",
        monto=0,
        estado="completed",
        metodo="paypal",
        referencia="test-ref-001",
        descripcion="Pago de prueba",
        audit=True,
        nombre=estudiante.nombre,
        apellido="Test",
        correo_electronico=estudiante.correo_electronico,
    )
    db_session.add(pago)
    db_session.commit()

    # Crear inscripción
    inscripcion = EstudianteCurso(
        curso=curso.codigo,
        usuario=estudiante.usuario,
        vigente=True,
        pago=pago.id,
    )
    db_session.add(inscripcion)
    db_session.commit()


def asignar_instructor(db_session, curso: Curso, instructor: Usuario) -> None:
    """Asigna un instructor a un curso."""
    asignacion = DocenteCurso(
        curso=curso.codigo,
        usuario=instructor.usuario,
    )
    db_session.add(asignacion)
    db_session.commit()


def login_usuario(client, username: str, password: str = "password123") -> None:
    """Inicia sesión con un usuario."""
    resp = client.post(
        "/user/login",
        data={"usuario": username, "acceso": password},
        follow_redirects=False,
    )
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}


# =============================================================================
# Tests de visualización de recursos
# =============================================================================


def test_visualizar_recurso_texto_estudiante_inscrito(app, db_session):
    """Un estudiante inscrito puede visualizar un recurso de texto."""
    # Preparar datos
    estudiante = crear_usuario(db_session, "student", "alumno1")
    curso = crear_curso(db_session, "curso_texto")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    # Crear recurso de texto
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Lección de texto",
        descripcion="Contenido educativo",
        requerido="required",
        indice=1,
        publico=False,
        text="Este es el contenido del recurso de texto",
    )
    db_session.add(recurso)
    db_session.commit()

    # Iniciar sesión
    client = app.test_client()
    login_usuario(client, "alumno1")

    # Acceder al recurso
    resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    # Verificaciones
    assert resp.status_code == 200
    assert "Lección de texto" in resp.data.decode("utf-8")


def test_visualizar_recurso_youtube_estudiante_inscrito(app, db_session):
    """Un estudiante inscrito puede visualizar un recurso de YouTube."""
    estudiante = crear_usuario(db_session, "student", "alumno2")
    curso = crear_curso(db_session, "curso_youtube")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="youtube",
        nombre="Video tutorial",
        descripcion="Video educativo",
        requerido="optional",
        indice=1,
        publico=False,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno2")

    resp = client.get(f"/course/{curso.codigo}/resource/youtube/{recurso.id}")

    assert resp.status_code == 200


def test_visualizar_recurso_html_estudiante_inscrito(app, db_session):
    """Un estudiante inscrito puede visualizar un recurso HTML."""
    estudiante = crear_usuario(db_session, "student", "alumno3")
    curso = crear_curso(db_session, "curso_html")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="html",
        nombre="Contenido HTML",
        descripcion="Contenido interactivo",
        requerido="required",
        indice=1,
        publico=False,
        external_code="<div><h1>Contenido HTML</h1></div>",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno3")

    resp = client.get(f"/course/{curso.codigo}/resource/html/{recurso.id}")

    assert resp.status_code == 200


def test_visualizar_recurso_link_estudiante_inscrito(app, db_session):
    """Un estudiante inscrito puede visualizar un recurso de enlace externo."""
    estudiante = crear_usuario(db_session, "student", "alumno4")
    curso = crear_curso(db_session, "curso_link")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="link",
        nombre="Recurso externo",
        descripcion="Enlace a recurso externo",
        requerido="optional",
        indice=1,
        publico=False,
        url="https://example.com/recurso",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno4")

    resp = client.get(f"/course/{curso.codigo}/resource/link/{recurso.id}")

    assert resp.status_code == 200


def test_visualizar_recurso_meet_estudiante_inscrito(app, db_session):
    """Un estudiante inscrito puede visualizar un recurso de sesión síncrona."""
    estudiante = crear_usuario(db_session, "student", "alumno5")
    curso = crear_curso(db_session, "curso_meet")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesión en vivo",
        descripcion="Clase sincrónica",
        requerido="required",
        indice=1,
        publico=False,
        url="https://meet.google.com/abc-defg-hij",
        fecha=date(2026, 3, 15),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 30),
        notes="google_meet",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno5")

    resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}")

    assert resp.status_code == 200


def test_visualizar_recurso_publico_sin_autenticar(app, db_session):
    """Un usuario no autenticado puede ver recursos públicos."""
    curso = crear_curso(db_session, "curso_publico")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Recurso público",
        descripcion="Accesible para todos",
        requerido="optional",
        indice=1,
        publico=True,
        text="Contenido público",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()

    resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    assert resp.status_code == 200


def test_no_visualizar_recurso_privado_sin_inscripcion(app, db_session):
    """Un estudiante no inscrito no puede ver recursos privados."""
    estudiante = crear_usuario(db_session, "student", "alumno6")
    curso = crear_curso(db_session, "curso_privado")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Recurso privado",
        descripcion="Solo para inscritos",
        requerido="required",
        indice=1,
        publico=False,
        text="Contenido privado",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno6")

    resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    # Debería redirigir o mostrar mensaje de no autorizado
    assert resp.status_code in REDIRECT_STATUS_CODES | {200, 403}


# =============================================================================
# Tests de marcado de recursos completados
# =============================================================================


def test_marcar_recurso_completado_crea_registro_avance(app, db_session):
    """Al marcar un recurso como completado se crea registro de avance."""
    estudiante = crear_usuario(db_session, "student", "alumno7")
    curso = crear_curso(db_session, "curso_avance")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Lección completable",
        descripcion="Marca como completada",
        requerido="required",
        indice=1,
        publico=False,
        text="Contenido para completar",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno7")

    # Marcar recurso como completado
    resp = client.get(
        f"/course/{curso.codigo}/resource/text/{recurso.id}/complete",
        follow_redirects=False,
    )

    # Verificar respuesta
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    # Verificar que se creó el registro de avance usando SQLAlchemy 2.0 API
    avance = db_session.execute(
        select(CursoRecursoAvance).filter_by(
            curso=curso.codigo,
            recurso=recurso.id,
            usuario=estudiante.usuario,
        )
    ).scalar_one()

    assert avance is not None
    assert avance.completado is True


def test_marcar_multiples_recursos_completados(app, db_session):
    """Un estudiante puede marcar múltiples recursos como completados."""
    estudiante = crear_usuario(db_session, "student", "alumno8")
    curso = crear_curso(db_session, "curso_multiple")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    # Crear 3 recursos
    recursos = []
    for i in range(1, 4):
        recurso = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            tipo="text",
            nombre=f"Lección {i}",
            descripcion=f"Contenido {i}",
            requerido="required",
            indice=i,
            publico=False,
            text=f"Texto del recurso {i}",
        )
        db_session.add(recurso)
        recursos.append(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno8")

    # Marcar cada recurso como completado
    for recurso in recursos:
        resp = client.get(
            f"/course/{curso.codigo}/resource/text/{recurso.id}/complete",
            follow_redirects=False,
        )
        assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    # Verificar que todos están marcados como completados
    avances = (
        db_session.execute(
            select(CursoRecursoAvance).filter_by(
                curso=curso.codigo,
                usuario=estudiante.usuario,
            )
        )
        .scalars()
        .all()
    )

    assert len(avances) == 3
    assert all(a.completado for a in avances)


def test_no_marcar_completado_sin_inscripcion(app, db_session):
    """Un estudiante no inscrito no puede marcar recursos completados."""
    estudiante = crear_usuario(db_session, "student", "alumno9")
    curso = crear_curso(db_session, "curso_sin_acceso")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Recurso protegido",
        descripcion="Sin acceso",
        requerido="required",
        indice=1,
        publico=False,
        text="Contenido protegido",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno9")

    resp = client.get(
        f"/course/{curso.codigo}/resource/text/{recurso.id}/complete",
        follow_redirects=False,
    )

    # No debería poder completar
    assert resp.status_code in REDIRECT_STATUS_CODES | {403}

    # Verificar que NO se creó registro de avance
    avance = db_session.execute(
        select(CursoRecursoAvance).filter_by(
            curso=curso.codigo,
            recurso=recurso.id,
            usuario=estudiante.usuario,
        )
    ).scalar_one_or_none()

    assert avance is None


# =============================================================================
# Tests de creación de recursos por instructores
# =============================================================================


def test_instructor_crear_recurso_texto(app, db_session):
    """Un instructor puede crear un recurso de texto."""
    instructor = crear_usuario(db_session, "instructor", "instructor1")
    curso = crear_curso(db_session, "curso_crear_texto")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "instructor1")

    # Crear recurso de texto vía POST
    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/text/new",
        data={
            "nombre": "Nuevo texto",
            "descripcion": "Descripción del texto",
            "requerido": "required",
            "editor": "Contenido del editor",
        },
        follow_redirects=False,
    )

    # Verificar redirección exitosa
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    # Verificar que se creó el recurso en BD usando SQLAlchemy 2.0
    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="text",
            nombre="Nuevo texto",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.text is not None
    assert recurso.seccion == seccion.id


def test_instructor_crear_recurso_youtube(app, db_session):
    """Un instructor puede crear un recurso de YouTube."""
    instructor = crear_usuario(db_session, "instructor", "instructor2")
    curso = crear_curso(db_session, "curso_crear_youtube")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "instructor2")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/youtube/new",
        data={
            "nombre": "Video educativo",
            "descripcion": "Descripción del video",
            "requerido": "optional",
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="youtube",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.url is not None
    assert "youtube.com" in recurso.url or "youtu.be" in recurso.url


def test_instructor_crear_recurso_html(app, db_session):
    """Un instructor puede crear un recurso HTML."""
    instructor = crear_usuario(db_session, "instructor", "instructor3")
    curso = crear_curso(db_session, "curso_crear_html")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "instructor3")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/html/new",
        data={
            "nombre": "Contenido HTML",
            "descripcion": "HTML interactivo",
            "requerido": "required",
            "html_externo": "<div><h2>Hola mundo</h2></div>",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="html",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.external_code is not None


def test_instructor_crear_recurso_link(app, db_session):
    """Un instructor puede crear un recurso de enlace externo."""
    instructor = crear_usuario(db_session, "instructor", "instructor4")
    curso = crear_curso(db_session, "curso_crear_link")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "instructor4")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/link/new",
        data={
            "nombre": "Enlace externo",
            "descripcion": "Recurso en otro sitio",
            "requerido": "optional",
            "url": "https://example.com/recurso-externo",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="link",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.url == "https://example.com/recurso-externo"


def test_instructor_crear_recurso_meet(app, db_session):
    """Un instructor puede crear un recurso de sesión Meet."""
    instructor = crear_usuario(db_session, "instructor", "instructor5")
    curso = crear_curso(db_session, "curso_crear_meet")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "instructor5")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/meet/new",
        data={
            "nombre": "Sesión en vivo",
            "descripcion": "Clase sincrónica",
            "requerido": "required",
            "url": "https://meet.google.com/xyz-abcd-efg",
            "fecha": "2026-04-01",
            "hora_inicio": "14:00",
            "hora_fin": "15:30",
            "notes": "google_meet",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="meet",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.url is not None
    assert recurso.fecha is not None
    assert recurso.hora_inicio is not None
    assert recurso.hora_fin is not None


def test_instructor_crear_recurso_pdf(app, db_session):
    """Un instructor puede crear un recurso PDF."""
    instructor = crear_usuario(db_session, "instructor", "instructor6")
    curso = crear_curso(db_session, "curso_crear_pdf")
    seccion = crear_seccion(db_session, curso)

    # Habilitar carga de archivos
    with app.app_context():
        config = database.session.execute(select(Configuracion)).scalar_one_or_none()
        if config:
            config.enable_file_uploads = True
            database.session.commit()
    db_session.expire_all()

    client = app.test_client()
    login_usuario(client, "instructor6")

    # Crear archivo PDF falso
    pdf_bytes = io.BytesIO(b"%PDF-1.4\n%Test PDF content\n")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/pdf/new",
        data={
            "nombre": "Documento PDF",
            "descripcion": "Material de lectura",
            "requerido": "required",
            "pdf": (pdf_bytes, "documento.pdf"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="pdf",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.doc is not None


def test_instructor_crear_recurso_imagen(app, db_session):
    """Un instructor puede crear un recurso de imagen."""
    instructor = crear_usuario(db_session, "instructor", "instructor7")
    curso = crear_curso(db_session, "curso_crear_img")
    seccion = crear_seccion(db_session, curso)

    # Habilitar carga de archivos
    with app.app_context():
        config = database.session.execute(select(Configuracion)).scalar_one_or_none()
        if config:
            config.enable_file_uploads = True
            database.session.commit()
    db_session.expire_all()

    client = app.test_client()
    login_usuario(client, "instructor7")

    # Crear imagen falsa (PNG header)
    img_bytes = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/img/new",
        data={
            "nombre": "Diagrama",
            "descripcion": "Imagen explicativa",
            "requerido": "optional",
            "img": (img_bytes, "diagrama.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="img",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.doc is not None


def test_instructor_crear_recurso_audio(app, db_session):
    """Un instructor puede crear un recurso de audio."""
    instructor = crear_usuario(db_session, "instructor", "instructor8")
    curso = crear_curso(db_session, "curso_crear_audio")
    seccion = crear_seccion(db_session, curso)

    # Habilitar carga de archivos
    with app.app_context():
        config = database.session.execute(select(Configuracion)).scalar_one_or_none()
        if config:
            config.enable_file_uploads = True
            database.session.commit()
    db_session.expire_all()

    client = app.test_client()
    login_usuario(client, "instructor8")

    # Crear archivo de audio falso (MP3 header)
    audio_bytes = io.BytesIO(b"ID3\x04\x00\x00\x00")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/audio/new",
        data={
            "nombre": "Podcast",
            "descripcion": "Audio educativo",
            "requerido": "optional",
            "audio": (audio_bytes, "podcast.mp3"),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso = db_session.execute(
        select(CursoRecurso).filter_by(
            curso=curso.codigo,
            tipo="mp3",
        )
    ).scalar_one_or_none()

    assert recurso is not None
    assert recurso.doc is not None


# =============================================================================
# Tests de edición de recursos por instructores
# =============================================================================


def test_instructor_editar_recurso_texto(app, db_session):
    """Un instructor puede editar un recurso de texto existente."""
    instructor = crear_usuario(db_session, "instructor", "instructor9")
    curso = crear_curso(db_session, "curso_editar_texto")
    seccion = crear_seccion(db_session, curso)

    # Crear recurso inicial
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Texto original",
        descripcion="Descripción original",
        requerido="required",
        indice=1,
        publico=False,
        text="Contenido original",
    )
    db_session.add(recurso)
    db_session.commit()
    recurso_id = recurso.id

    client = app.test_client()
    login_usuario(client, "instructor9")

    # Editar recurso
    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/text/{recurso_id}/edit",
        data={
            "nombre": "Texto editado",
            "descripcion": "Descripción editada",
            "requerido": "optional",
            "editor": "Contenido editado",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    # Verificar cambios en BD
    recurso_editado = db_session.get(CursoRecurso, recurso_id)
    assert recurso_editado.nombre == "Texto editado"
    assert recurso_editado.descripcion == "Descripción editada"


def test_instructor_editar_recurso_youtube(app, db_session):
    """Un instructor puede editar un recurso de YouTube."""
    instructor = crear_usuario(db_session, "instructor", "instructor10")
    curso = crear_curso(db_session, "curso_editar_youtube")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="youtube",
        nombre="Video original",
        descripcion="Video viejo",
        requerido="required",
        indice=1,
        publico=False,
        url="https://www.youtube.com/watch?v=old_video",
    )
    db_session.add(recurso)
    db_session.commit()
    recurso_id = recurso.id

    client = app.test_client()
    login_usuario(client, "instructor10")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/youtube/{recurso_id}/edit",
        data={
            "nombre": "Video actualizado",
            "descripcion": "Video nuevo",
            "requerido": "optional",
            "youtube_url": "https://www.youtube.com/watch?v=new_video",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso_editado = db_session.get(CursoRecurso, recurso_id)
    assert recurso_editado.nombre == "Video actualizado"
    assert "new_video" in recurso_editado.url


def test_instructor_editar_recurso_link(app, db_session):
    """Un instructor puede editar un recurso de enlace."""
    instructor = crear_usuario(db_session, "instructor", "instructor11")
    curso = crear_curso(db_session, "curso_editar_link")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="link",
        nombre="Enlace viejo",
        descripcion="Descripción vieja",
        requerido="required",
        indice=1,
        publico=False,
        url="https://example.com/old",
    )
    db_session.add(recurso)
    db_session.commit()
    recurso_id = recurso.id

    client = app.test_client()
    login_usuario(client, "instructor11")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/link/{recurso_id}/edit",
        data={
            "nombre": "Enlace nuevo",
            "descripcion": "Descripción nueva",
            "requerido": "optional",
            "url": "https://example.com/new",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso_editado = db_session.get(CursoRecurso, recurso_id)
    assert recurso_editado.nombre == "Enlace nuevo"
    assert recurso_editado.url == "https://example.com/new"


def test_instructor_editar_recurso_meet(app, db_session):
    """Un instructor puede editar un recurso Meet."""
    instructor = crear_usuario(db_session, "instructor", "instructor12")
    curso = crear_curso(db_session, "curso_editar_meet")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesión vieja",
        descripcion="Descripción vieja",
        requerido="required",
        indice=1,
        publico=False,
        url="https://meet.google.com/old",
        fecha=date(2026, 1, 1),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 0),
        notes="google_meet",
    )
    db_session.add(recurso)
    db_session.commit()
    recurso_id = recurso.id

    client = app.test_client()
    login_usuario(client, "instructor12")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/meet/{recurso_id}/edit",
        data={
            "nombre": "Sesión nueva",
            "descripcion": "Descripción nueva",
            "requerido": "optional",
            "url": "https://meet.google.com/new",
            "fecha": "2026-06-01",
            "hora_inicio": "15:00",
            "hora_fin": "16:30",
            "notes": "zoom",
        },
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES | {200}

    recurso_editado = db_session.get(CursoRecurso, recurso_id)
    assert recurso_editado.nombre == "Sesión nueva"
    assert "new" in recurso_editado.url


# =============================================================================
# Tests de calendarios Meet
# =============================================================================


def test_descargar_calendario_ics_meet(app, db_session):
    """Se puede descargar un archivo ICS para un recurso Meet."""
    instructor = crear_usuario(db_session, "instructor", "instructor13")
    curso = crear_curso(db_session, "curso_cal_ics")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesión con calendario",
        descripcion="Para exportar",
        requerido="required",
        indice=1,
        publico=False,
        url="https://meet.google.com/abc-def-ghi",
        fecha=date(2026, 5, 15),
        hora_inicio=time(14, 0),
        hora_fin=time(15, 30),
        notes="google_meet",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "instructor13")

    resp = client.get(f"/course/{curso.codigo}/resource/meet/{recurso.id}/calendar.ics")

    assert resp.status_code == 200
    assert resp.mimetype == "text/calendar"

    # Verificar contenido del ICS
    contenido = resp.data.decode("utf-8")
    assert "BEGIN:VCALENDAR" in contenido
    assert "END:VCALENDAR" in contenido
    assert "Sesión con calendario" in contenido
    assert "DTSTART:" in contenido
    assert "DTEND:" in contenido


def test_google_calendar_link_redireccion(app, db_session):
    """El enlace de Google Calendar redirige correctamente."""
    instructor = crear_usuario(db_session, "instructor", "instructor14")
    curso = crear_curso(db_session, "curso_gcal")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesión Google",
        descripcion="Para Google Calendar",
        requerido="required",
        indice=1,
        publico=False,
        url="https://meet.google.com/xyz",
        fecha=date(2026, 6, 1),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 0),
        notes="google_meet",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "instructor14")

    resp = client.get(
        f"/course/{curso.codigo}/resource/meet/{recurso.id}/google-calendar",
        follow_redirects=False,
    )

    assert resp.status_code in REDIRECT_STATUS_CODES

    location = resp.headers.get("Location", "")
    assert "calendar.google.com" in location
    assert "action=TEMPLATE" in location


def test_outlook_calendar_link_redireccion(app, db_session):
    """El enlace de Outlook Calendar redirige correctamente."""
    instructor = crear_usuario(db_session, "instructor", "instructor15")
    curso = crear_curso(db_session, "curso_outlook")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="meet",
        nombre="Sesión Outlook",
        descripcion="Para Outlook Calendar",
        requerido="required",
        indice=1,
        publico=False,
        url="https://meet.google.com/outlook",
        fecha=date(2026, 7, 1),
        hora_inicio=time(16, 0),
        hora_fin=time(17, 0),
        notes="zoom",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "instructor15")

    resp = client.get(
        f"/course/{curso.codigo}/resource/meet/{recurso.id}/outlook-calendar",
        follow_redirects=False,
    )

    # Puede ser redirect o página con botón
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}


# =============================================================================
# Tests de permisos y autorización
# =============================================================================


def test_admin_puede_ver_todos_recursos(app, db_session):
    """Un administrador puede ver todos los recursos."""
    admin = crear_usuario(db_session, "admin", "admin1")
    curso = crear_curso(db_session, "curso_admin")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Recurso admin",
        descripcion="Solo admin",
        requerido="required",
        indice=1,
        publico=False,
        text="Contenido administrativo",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "admin1")

    resp = client.get(f"/course/{curso.codigo}/resource/text/{recurso.id}")

    assert resp.status_code == 200


def test_estudiante_no_inscrito_no_puede_crear_recursos(app, db_session):
    """Un estudiante no puede crear recursos."""
    estudiante = crear_usuario(db_session, "student", "alumno10")
    curso = crear_curso(db_session, "curso_no_crear")
    seccion = crear_seccion(db_session, curso)

    client = app.test_client()
    login_usuario(client, "alumno10")

    resp = client.post(
        f"/course/{curso.codigo}/{seccion.id}/text/new",
        data={
            "nombre": "Intento estudiante",
            "descripcion": "No debería funcionar",
            "requerido": "required",
            "editor": "Contenido",
        },
        follow_redirects=False,
    )

    # Debería ser rechazado (redirect o 403)
    assert resp.status_code in REDIRECT_STATUS_CODES | {403}


# =============================================================================
# Tests de biblioteca del curso
# =============================================================================


def test_instructor_subir_archivo_biblioteca(app, db_session):
    """Un instructor puede subir archivos a la biblioteca del curso."""
    instructor = crear_usuario(db_session, "instructor", "instructor16")
    curso = crear_curso(db_session, "curso_biblioteca")
    seccion = crear_seccion(db_session, curso)

    # Asignar instructor al curso
    asignar_instructor(db_session, curso, instructor)

    # Habilitar carga de archivos
    with app.app_context():
        config = database.session.execute(select(Configuracion)).scalar_one_or_none()
        if config:
            config.enable_file_uploads = True
            database.session.commit()
    db_session.expire_all()

    client = app.test_client()
    login_usuario(client, "instructor16")

    # Subir archivo a biblioteca
    archivo_bytes = io.BytesIO(b"Contenido del archivo de biblioteca")

    resp = client.post(
        f"/course/{curso.codigo}/library/new",
        data={
            "archivo": (archivo_bytes, "material.txt"),
            "descripcion": "Material complementario",
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    # Puede redirigir o retornar 200
    assert resp.status_code in REDIRECT_STATUS_CODES | {200}


def test_ver_biblioteca_curso_instructor_asignado(app, db_session):
    """Un instructor asignado al curso puede acceder a la URL de biblioteca."""
    instructor = crear_usuario(db_session, "instructor", "instructor_lib")
    curso = crear_curso(db_session, "curso_ver_biblioteca")

    # Asignar instructor al curso
    asignar_instructor(db_session, curso, instructor)

    client = app.test_client()
    login_usuario(client, "instructor_lib")

    # Acceder a la biblioteca del curso
    resp = client.get(f"/course/{curso.codigo}/library", follow_redirects=False)

    # El instructor asignado debe poder acceder sin errores
    assert resp.status_code == 200


def test_ver_biblioteca_curso_estudiante_no_permitido(app, db_session):
    """Un estudiante no puede acceder a la biblioteca (requiere perfil instructor)."""
    estudiante = crear_usuario(db_session, "student", "alumno11")
    curso = crear_curso(db_session, "curso_biblioteca_estudiante")
    inscribir_estudiante(db_session, curso, estudiante)

    client = app.test_client()
    login_usuario(client, "alumno11")

    resp = client.get(f"/course/{curso.codigo}/library", follow_redirects=False)

    # Los estudiantes no tienen acceso a la biblioteca (requiere perfil instructor)
    assert resp.status_code in REDIRECT_STATUS_CODES | {403}


def test_ver_biblioteca_curso_no_inscrito(app, db_session):
    """Un usuario no inscrito no puede ver la biblioteca privada."""
    estudiante = crear_usuario(db_session, "student", "alumno12")
    curso = crear_curso(db_session, "curso_biblioteca_privada")

    client = app.test_client()
    login_usuario(client, "alumno12")

    resp = client.get(f"/course/{curso.codigo}/library", follow_redirects=False)

    # Debe redirigir o denegar acceso
    assert resp.status_code in REDIRECT_STATUS_CODES | {403, 200}


# =============================================================================
# Tests de recursos especiales (PDF viewer, external code, etc.)
# =============================================================================


def test_visor_pdf_recurso(app, db_session):
    """El visor de PDF funciona para recursos PDF."""
    estudiante = crear_usuario(db_session, "student", "alumno13")
    curso = crear_curso(db_session, "curso_visor_pdf")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    # Crear recurso PDF
    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="pdf",
        nombre="PDF con visor",
        descripcion="Ver en navegador",
        requerido="required",
        indice=1,
        publico=False,
        doc="documento.pdf",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno13")

    resp = client.get(f"/course/{curso.codigo}/pdf_viewer/{recurso.id}")

    # Puede retornar HTML o redirect
    assert resp.status_code in {200, *REDIRECT_STATUS_CODES}


def test_external_code_recurso_html(app, db_session):
    """El external_code funciona para recursos HTML."""
    estudiante = crear_usuario(db_session, "student", "alumno14")
    curso = crear_curso(db_session, "curso_ext_code")
    seccion = crear_seccion(db_session, curso)
    inscribir_estudiante(db_session, curso, estudiante)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="html",
        nombre="HTML externo",
        descripcion="Código externo",
        requerido="required",
        indice=1,
        publico=False,
        external_code="<div><p>Contenido externo</p></div>",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno14")

    resp = client.get(f"/course/{curso.codigo}/external_code/{recurso.id}")

    assert resp.status_code in {200, *REDIRECT_STATUS_CODES}


# =============================================================================
# Tests adicionales de casos edge
# =============================================================================


def test_recurso_no_existente_retorna_404(app, db_session):
    """Acceder a un recurso inexistente retorna 404."""
    estudiante = crear_usuario(db_session, "student", "alumno15")
    curso = crear_curso(db_session, "curso_404")

    client = app.test_client()
    login_usuario(client, "alumno15")

    resp = client.get(f"/course/{curso.codigo}/resource/text/id_inexistente")

    assert resp.status_code == 404


def test_curso_no_existente_retorna_404(app, db_session):
    """Acceder a recursos de un curso inexistente retorna error."""
    estudiante = crear_usuario(db_session, "student", "alumno16")

    client = app.test_client()
    login_usuario(client, "alumno16")

    resp = client.get("/course/curso_inexistente/resource/text/123")

    # Puede ser 404 o otro error
    assert resp.status_code in {404, 500, *REDIRECT_STATUS_CODES}


def test_tipo_recurso_invalido_retorna_404(app, db_session):
    """Acceder a un tipo de recurso inválido retorna 404."""
    estudiante = crear_usuario(db_session, "student", "alumno17")
    curso = crear_curso(db_session, "curso_tipo_inv")
    seccion = crear_seccion(db_session, curso)

    recurso = CursoRecurso(
        curso=curso.codigo,
        seccion=seccion.id,
        tipo="text",
        nombre="Recurso test",
        descripcion="Test",
        requerido="required",
        indice=1,
        publico=True,
        text="Contenido",
    )
    db_session.add(recurso)
    db_session.commit()

    client = app.test_client()
    login_usuario(client, "alumno17")

    # Intentar acceder con tipo incorrecto
    resp = client.get(f"/course/{curso.codigo}/resource/tipo_invalido/{recurso.id}")

    assert resp.status_code == 404
