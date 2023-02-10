# Copyright 2022 - 2023 BMO Soluciones, S.A.
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
# Contributors:
# - William José Moreno Reyes

"""Logica del "negocio"."""

# pylint: disable=E1101


# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares parte de la "logica de negocio" de la implementacion.

# Libreria standar:
from typing import Union

# Librerias de terceros:
from flask_login import current_user

# Recursos locales:
from now_lms.db import database, EstudianteCurso, DocenteCurso, ModeradorCurso, Usuario, Curso, CursoSeccion, CursoRecurso


def modificar_indice_curso(
    codigo_curso: Union[None, str] = None,
    task: Union[None, str] = None,
    indice: int = 0,
):
    """Modica el número de indice de una sección dentro de un curso."""

    indice_current = indice
    indice_next = indice + 1
    indice_back = indice - 1

    actual = CursoSeccion.query.filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_current).first()
    superior = CursoSeccion.query.filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_next).first()
    inferior = CursoSeccion.query.filter(CursoSeccion.curso == codigo_curso, CursoSeccion.indice == indice_back).first()

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

    secciones = secciones = CursoSeccion.query.filter_by(curso=codigo_curso).order_by(CursoSeccion.indice).all()
    if secciones:
        indice = 1
        for seccion in secciones:
            seccion.indice = indice
            database.session.add(seccion)
            database.session.commit()
            indice = indice + 1


def reorganiza_indice_seccion(seccion: Union[None, str] = None):
    """Al eliminar una sección de un curso se debe generar el indice nuevamente."""

    recursos = CursoRecurso.query.filter_by(seccion=seccion).order_by(CursoRecurso.indice).all()
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
    RECURSO_ACTUAL = CursoRecurso.query.filter(
        CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_ACTUAL
    ).first()

    RECURSO_ANTERIOR = CursoRecurso.query.filter(
        CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_ANTERIOR
    ).first()

    RECURSO_POSTERIOR = CursoRecurso.query.filter(
        CursoRecurso.seccion == seccion_id, CursoRecurso.indice == NO_INDICE_POSTERIOR
    ).first()

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
    ASIGNACION = DocenteCurso(curso=curso_codigo, usuario=usuario_id, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_moderador(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
    ASIGNACION = ModeradorCurso(usuario=usuario_id, curso=curso_codigo, vigente=True, creado_por=current_user.usuario)
    database.session.add(ASIGNACION)
    database.session.commit()


def asignar_curso_a_estudiante(curso_codigo: Union[None, str] = None, usuario_id: Union[None, str] = None):
    """Asigna un usuario como moderador de un curso."""
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
    USUARIO = Usuario.query.filter_by(usuario=id_usuario).first()
    USUARIO.tipo = nuevo_tipo
    USUARIO.modificado_por = usuario
    database.session.commit()


def cambia_estado_curso_por_id(
    id_curso: Union[None, str, int] = None, nuevo_estado: Union[None, str] = None, usuario: Union[None, str] = None
):
    """
    Cambia el estatus de un curso.

    Los valores reconocidos por el sistema son: draft, public, open, closed.
    """
    CURSO = Curso.query.filter_by(codigo=id_curso).first()
    CURSO.estado = nuevo_estado
    CURSO.modificado_por = usuario
    database.session.commit()


def cambia_curso_publico(id_curso: Union[None, str, int] = None):
    """Cambia el estatus publico de un curso."""
    CURSO = Curso.query.filter_by(codigo=id_curso).first()
    if CURSO.publico:
        CURSO.publico = False
    else:
        CURSO.publico = True
    CURSO.modificado_por = current_user.usuario
    database.session.commit()


def cambia_seccion_publico(codigo: Union[None, str, int] = None):
    """Cambia el estatus publico de una sección."""

    SECCION = CursoSeccion.query.filter_by(id=codigo).first()
    if SECCION.estado:
        SECCION.estado = False
    else:
        SECCION.estado = True
    SECCION.modificado_por = current_user.usuario
    database.session.commit()
