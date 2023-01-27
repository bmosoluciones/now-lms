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

"""Definición de base de datos."""

# pylint: disable=E1101

# Libreria standar:
from typing import Union

# Librerias de terceros:
from flask_login import current_user

# Recursos locales:
from now_lms.db import (
    database,
    DocenteCurso,
    Configuracion,
    EstudianteCurso,
    ModeradorCurso,
)

# < --------------------------------------------------------------------------------------------- >
# Funciones auxiliares relacionadas a contultas de la base de datos.


def verifica_docente_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como docente al curso devuelve None."""
    if current_user.is_authenticated:
        return DocenteCurso.query.filter(DocenteCurso.usuario == current_user.usuario, DocenteCurso.curso == id_curso)
    else:
        return False


def verifica_moderador_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como moderador al curso devuelve None."""
    if current_user.is_authenticated:
        return ModeradorCurso.query.filter(ModeradorCurso.usuario == current_user.usuario, ModeradorCurso.curso == id_curso)
    else:
        return False


def verifica_estudiante_asignado_a_curso(id_curso: Union[None, str] = None):
    """Si el usuario no esta asignado como estudiante al curso devuelve None."""
    if current_user.is_authenticated:
        return EstudianteCurso.query.filter(EstudianteCurso.usuario == current_user.usuario, EstudianteCurso.curso == id_curso)
    else:
        return False


def crear_configuracion_predeterminada():
    """Crea configuración predeterminada de la aplicación."""
    config = Configuracion(
        titulo="NOW LMS",
        descripcion="Sistema de aprendizaje en linea.",
    )
    database.session.add(config)
    database.session.commit()
