# Copyright 2022 - 2024 BMO Soluciones, S.A.
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

"""Business logic implementation."""

# pylint: disable=E1101


# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares parte de la "logica de negocio" de la implementacion.

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from typing import Union

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import flash
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import Curso, CursoRecurso, CursoSeccion, DocenteCurso, EstudianteCurso, ModeradorCurso, Usuario, database
from now_lms.logs import log


def modificar_indice_curso(
    codigo_curso: Union[None, str] = None,
    task: Union[None, str] = None,
    indice: int = 0,
):
    """Modica el número de indice de una sección dentro de un curso."""
    indice_current = indice
    indice_next = indice + 1
    indice_back = indice - 1

    actual = database.session.execute(
        database.select(CursoSeccion).filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_current)
    ).scalar_one_or_none()
    superior = database.session.execute(
        database.select(CursoSeccion).filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_next)
    ).scalar_one_or_none()
    inferior = database.session.execute(
        database.select(CursoSeccion).filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_back)
    ).scalar_one_or_none()

    if task == "increment":
        actual.indice = indice_next
        database.session.add(actual)
        database.session.commit()
        if superior:
            superior.indice = indice_current
            database.session.add(superior)
            database.session.commit()

    else:  # task == decrement
        if actual.indice != 1:  # No convertir indice 1 a 0.
            actual.indice = indice_back
            database.session.add(actual)
            database.session.commit()
            if inferior:
                inferior.indice = indice_current
                database.session.add(inferior)
                database.session.commit()


def reorganiza_indice_curso(codigo_curso: Union[None, str] = None):
    """Al eliminar una sección de un curso se debe generar el indice nuevamente."""
    secciones = (
        database.session.execute(database.select(CursoSeccion).filter_by(curso=codigo_curso).order_by(CursoSeccion.indice))
        .scalars()
        .all()
    )
    if secciones:
        indice = 1
        for seccion in secciones:
            seccion.indice = indice
            database.session.add(seccion)
            database.session.commit()
            indice = indice + 1


def reorganiza_indice_seccion(seccion: Union[None, str] = None):
    """Al eliminar una sección de un curso se debe generar el indice nuevamente."""
    recursos = (
        database.session.execute(database.select(CursoRecurso).filter_by(seccion=seccion).order_by(CursoRecurso.indice))
        .scalars()
        .all()
    )
    if recursos:
        indice = 1
        for recurso in recursos:
            recurso.indice = indice
            database.session.add(recurso)
            database.session.commit()
            indice = indice + 1


def modificar_indice_seccion(
    seccion_id: Union[None, str] = None,
    task: Union[None, str] = None,
    # increment: aumenta el numero de indice por lo que el recurso "baja" en la lista de recursos.
    # decrement: disminuye el numero de indice por lo que el recurso "sube" nala lista de recursos.
    indice: int = 0,
):
    """Modica el número de indice de un recurso dentro de una sección."""
    NO_INDICE_ACTUAL = int(indice)
    NO_INDICE_ANTERIOR = NO_INDICE_ACTUAL - 1
    NO_INDICE_POSTERIOR = NO_INDICE_ACTUAL + 1

    # Obtenemos lista de recursos de la base de datos.
    RECURSO_ACTUAL = database.session.execute(
        database.select(CursoRecurso).filter(CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_ACTUAL)
    ).scalar_one_or_none()

    RECURSO_ANTERIOR = database.session.execute(
        database.select(CursoRecurso).filter(CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_ANTERIOR)
    ).scalar_one_or_none()

    RECURSO_POSTERIOR = database.session.execute(
        database.select(CursoRecurso).filter(CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_POSTERIOR)
    ).scalar_one_or_none()

    if task == "increment" and RECURSO_POSTERIOR:
        RECURSO_ACTUAL.indice = NO_INDICE_POSTERIOR
        RECURSO_POSTERIOR.indice = NO_INDICE_ACTUAL
        database.session.add(RECURSO_ACTUAL)
        database.session.add(RECURSO_POSTERIOR)

    elif task == "decrement" and RECURSO_ANTERIOR:
        RECURSO_ACTUAL.indice = NO_INDICE_ANTERIOR
        RECURSO_ANTERIOR.indice = NO_INDICE_ACTUAL
        database.session.add(RECURSO_ACTUAL)
        database.session.add(RECURSO_ANTERIOR)

    database.session.commit()


def asignar_curso_a_instructor(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como instructor de un curso."""
    log.trace("Assigning {curso_codigo} to instructor {usuario_id}")
    ASIGNACION = DocenteCurso(curso=curso_codigo, usuario=usuario_id, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_moderador(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
    log.trace("Assigning {curso_codigo} to moderator {usuario_id}")
    ASIGNACION = ModeradorCurso(usuario=usuario_id, curso=curso_codigo, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_estudiante(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
    log.trace("Assigning {curso_codigo} to student {usuario_id}")
    ASIGNACION = EstudianteCurso(
        creado_por=current_user.usuario,
        curso=curso_codigo,
        usuario=usuario_id,
        vigente=True,
    )
    database.session.add(ASIGNACION)
    database.session.commit()


def cambia_tipo_de_usuario_por_id(
    id_usuario: Union[None, str] = None, nuevo_tipo: Union[None, str] = None, usuario: Union[None, str] = None
):
    """
    Cambia el estatus de un usuario del sistema.

    Los valores reconocidos por el sistema son: admin, user, instructor, moderator.
    """
    log.trace("Assigning user {id_usuario} the profile: {nuevo_tipo}")
    USUARIO = database.session.execute(database.select(Usuario).filter_by(usuario=id_usuario)).scalar_one_or_none()
    USUARIO.tipo = nuevo_tipo
    USUARIO.modificado_por = usuario
    database.session.commit()


def cambia_estado_curso_por_id(
    id_curso: Union[None, str, int] = None, nuevo_estado: Union[None, str] = None, usuario: Union[None, str] = None
):
    """
    Cambia el estatus de un curso.

    Los valores reconocidos por el sistema son: draft, public, open, closed, finalizado.
    """
    CURSO = database.session.execute(database.select(Curso).filter(Curso.codigo == id_curso)).first()[0]
    estado_anterior = CURSO.estado
    CURSO.estado = nuevo_estado
    CURSO.modificado_por = usuario
    database.session.commit()

    # Si el curso se finaliza, cerrar todos los mensajes del foro
    if nuevo_estado == "finalized" and estado_anterior != "finalized":
        from now_lms.db import ForoMensaje

        ForoMensaje.close_all_for_course(id_curso)
        # Solo mostrar flash si estamos en contexto de request
        try:
            flash("Curso finalizado. Todos los mensajes del foro han sido cerrados.", "info")
        except RuntimeError:
            # No estamos en contexto de request (ej: durante pruebas)
            pass

    database.session.refresh(CURSO)
    if CURSO.estado != "open":
        CURSO.publico = False
        database.session.commit()
        try:
            flash("Curso eliminado del sitio Web.", "info")
        except RuntimeError:
            # No estamos en contexto de request (ej: durante pruebas)
            pass


def cambia_curso_publico(id_curso: Union[None, str, int] = None):
    """Cambia el estatus publico de un curso."""
    CURSO = database.session.execute(database.select(Curso).filter(Curso.codigo == id_curso)).first()[0]
    if CURSO.estado == "open":
        if CURSO.publico:
            CURSO.publico = False
        else:
            CURSO.publico = True
            CURSO.modificado_por = current_user.usuario
            database.session.commit()
    else:
        flash("No se puede publicar el curso", "warning")


def cambia_seccion_publico(codigo: Union[None, str, int] = None):
    """Cambia el estatus publico de una sección."""
    SECCION = database.session.execute(database.select(CursoSeccion).filter_by(id=codigo)).scalar_one_or_none()
    if SECCION.estado:
        SECCION.estado = False
    else:
        SECCION.estado = True
    SECCION.modificado_por = current_user.usuario
    database.session.commit()
