# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Pruebas para la funcionalidad del foro."""

from now_lms.db import database, Curso, ForoMensaje, Usuario


def create_test_user():
    """Crea un usuario de prueba para los tests."""
    usuario = Usuario(
        usuario="test_user",
        acceso=b"test_password",
        nombre="Test",
        apellido="User",
        correo_electronico="test@example.com",
        tipo="student",
        activo=True,
    )
    database.session.add(usuario)
    database.session.commit()
    return usuario


def test_curso_foro_habilitado_field_exists(isolated_db_session):
    """Verifica que el campo foro_habilitado existe en el modelo Curso."""
    curso = Curso(
        nombre="Curso de Prueba",
        codigo="TEST999",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="draft",
        modalidad="time_based",
        foro_habilitado=True,
    )
    isolated_db_session.add(curso)
    isolated_db_session.flush()

    # Verificar que el curso se guardó correctamente
    from now_lms.db import select

    curso_db = isolated_db_session.execute(select(Curso).where(Curso.codigo == "TEST999")).scalar_one()
    assert curso_db is not None
    assert curso_db.foro_habilitado


def test_curso_self_paced_no_puede_tener_foro(session_basic_db_setup):
    """Verifica que cursos self-paced no pueden tener foro habilitado."""
    with session_basic_db_setup.app_context():
        curso = Curso(
            nombre="Curso Self-Paced",
            codigo="SELF001",
            descripcion_corta="Descripción corta",
            descripcion="Descripción completa",
            estado="draft",
            modalidad="self_paced",
            foro_habilitado=False,
        )

        # Verificar que puede_habilitar_foro retorna False
        assert not curso.puede_habilitar_foro()

        # Verificar que is_self_paced retorna True
        assert curso.is_self_paced()

        # Verificar validación
        valid, message = curso.validar_foro_habilitado()
        assert valid  # Debería ser válido cuando foro_habilitado=False

        # Intentar habilitar foro en curso self-paced debería lanzar error
        try:
            curso.foro_habilitado = True
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "self-paced" in str(e)


def test_curso_time_based_puede_tener_foro(session_basic_db_setup):
    """Verifica que cursos time-based pueden tener foro habilitado."""
    with session_basic_db_setup.app_context():
        curso = Curso(
            nombre="Curso Time-Based",
            codigo="TIME001",
            descripcion_corta="Descripción corta",
            descripcion="Descripción completa",
            estado="draft",
            modalidad="time_based",
            foro_habilitado=True,
        )

        # Verificar que puede_habilitar_foro retorna True
        assert curso.puede_habilitar_foro()

        # Verificar que is_self_paced retorna False
        assert not curso.is_self_paced()

        # Verificar validación
        valid, message = curso.validar_foro_habilitado()
        assert valid


def test_foro_mensaje_model_exists(minimal_db_setup):
    """Verifica que el modelo ForoMensaje funciona correctamente."""
    usuario = create_test_user()

    # Crear curso
    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)
    database.session.commit()

    # Crear mensaje del foro
    mensaje = ForoMensaje(
        curso_id=curso.codigo,
        usuario_id=usuario.usuario,
        contenido="Este es un mensaje de prueba en markdown",
        estado="abierto",
    )
    database.session.add(mensaje)
    database.session.commit()

    # Verificar que el mensaje se guardó correctamente
    mensaje_db = database.session.query(ForoMensaje).filter_by(curso_id=curso.codigo).first()
    assert mensaje_db is not None
    assert mensaje_db.contenido == "Este es un mensaje de prueba en markdown"
    assert mensaje_db.estado == "abierto"
    assert mensaje_db.usuario_id == usuario.usuario


def test_foro_mensaje_reply_functionality(minimal_db_setup):
    """Verifica la funcionalidad de respuestas en el foro."""
    usuario = create_test_user()

    # Crear curso
    curso = Curso(
        nombre="Curso con Foro",
        codigo="FORUM002",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)
    database.session.commit()

    # Crear mensaje principal
    mensaje_principal = ForoMensaje(
        curso_id=curso.codigo,
        usuario_id=usuario.usuario,
        contenido="Mensaje principal del hilo",
        estado="abierto",
    )
    database.session.add(mensaje_principal)
    database.session.commit()

    # Crear respuesta
    respuesta = ForoMensaje(
        curso_id=curso.codigo,
        usuario_id=usuario.usuario,
        parent_id=mensaje_principal.id,
        contenido="Esta es una respuesta al mensaje principal",
        estado="abierto",
    )
    database.session.add(respuesta)
    database.session.commit()

    # Verificar relaciones
    assert respuesta.parent_id == mensaje_principal.id
    assert respuesta.get_thread_root().id == mensaje_principal.id


def test_foro_mensaje_permissions(minimal_db_setup):
    """Verifica los permisos y validaciones del foro."""
    usuario = create_test_user()

    # Crear curso con foro habilitado
    curso = Curso(
        nombre="Curso Activo",
        codigo="ACTIVE001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)
    database.session.commit()

    # Verificar que se puede crear mensaje en curso activo con foro habilitado
    mensaje = ForoMensaje(
        curso_id=curso.codigo,
        usuario_id=usuario.usuario,
        contenido="Mensaje en curso activo",
        estado="abierto",
    )
    database.session.add(mensaje)
    database.session.commit()

    mensaje_db = database.session.query(ForoMensaje).filter_by(curso_id=curso.codigo).first()
    assert mensaje_db is not None
    assert mensaje_db.estado == "abierto"

    # Test reply functionality
    assert mensaje.can_reply()

    # Test closed message cannot be replied to
    mensaje.estado = "cerrado"
    assert not mensaje.can_reply()


def test_close_forum_when_course_finalized(minimal_db_setup):
    """Verifica que el foro se cierre cuando el curso se finaliza."""
    usuario = create_test_user()

    # Crear curso
    curso = Curso(
        nombre="Curso a Finalizar",
        codigo="FINAL001",
        descripcion_corta="Descripción corta",
        descripcion="Descripción completa",
        estado="open",
        modalidad="time_based",
        foro_habilitado=True,
    )
    database.session.add(curso)
    database.session.commit()

    # Crear varios mensajes

    mensaje1 = ForoMensaje(curso_id=curso.codigo, usuario_id=usuario.usuario, contenido="Primer mensaje", estado="abierto")
    mensaje2 = ForoMensaje(curso_id=curso.codigo, usuario_id=usuario.usuario, contenido="Segundo mensaje", estado="abierto")

    database.session.add_all([mensaje1, mensaje2])
    database.session.commit()

    # Cerrar todos los mensajes del curso
    ForoMensaje.close_all_for_course(curso.codigo)

    # Verificar que todos los mensajes están cerrados
    mensajes = database.session.query(ForoMensaje).filter_by(curso_id=curso.codigo).all()
    for mensaje in mensajes:

        assert mensaje.estado == "cerrado"
