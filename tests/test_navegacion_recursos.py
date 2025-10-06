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

"""Test resource navigation functionality."""

from now_lms.db import Curso, CursoRecurso, CursoSeccion
from now_lms.db.tools import crear_indice_recurso


class TestNavegacionRecursos:
    """Test resource navigation between sections and courses."""

    def test_recurso_primero_no_tiene_anterior(self, isolated_db_session):
        """Test that first resource has no previous resource."""
        # Create course
        curso = Curso(
            codigo="TEST01",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create section
        seccion = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion)
        isolated_db_session.commit()

        # Create first resource
        recurso = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="First Resource",
            descripcion="First resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso)
        isolated_db_session.commit()

        # Test navigation
        indice = crear_indice_recurso(recurso.id)
        assert indice.has_prev is False
        assert indice.prev_resource is None

    def test_recurso_ultimo_no_tiene_siguiente(self, isolated_db_session):
        """Test that last resource has no next resource."""
        # Create course
        curso = Curso(
            codigo="TEST02",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create section
        seccion = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion)
        isolated_db_session.commit()

        # Create last resource
        recurso = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Last Resource",
            descripcion="Last resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso)
        isolated_db_session.commit()

        # Test navigation
        indice = crear_indice_recurso(recurso.id)
        assert indice.has_next is False
        assert indice.next_resource is None

    def test_recurso_siguiente_en_misma_seccion(self, isolated_db_session):
        """Test navigation to next resource in same section."""
        # Create course
        curso = Curso(
            codigo="TEST03",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create section
        seccion = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion)
        isolated_db_session.commit()

        # Create resources
        recurso1 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Resource 1",
            descripcion="First resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso1)
        isolated_db_session.commit()

        recurso2 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Resource 2",
            descripcion="Second resource",
            tipo="text",
            indice=2,
            requerido="required",
        )
        isolated_db_session.add(recurso2)
        isolated_db_session.commit()

        # Test navigation from first resource
        indice = crear_indice_recurso(recurso1.id)
        assert indice.has_next is True
        assert indice.next_resource is not None
        assert indice.next_resource.codigo == recurso2.id

        # Test navigation from second resource
        indice = crear_indice_recurso(recurso2.id)
        assert indice.has_prev is True
        assert indice.prev_resource is not None
        assert indice.prev_resource.codigo == recurso1.id

    def test_recurso_siguiente_en_siguiente_seccion(self, isolated_db_session):
        """Test navigation to first resource of next section."""
        # Create course
        curso = Curso(
            codigo="TEST04",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create first section
        seccion1 = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion1)
        isolated_db_session.commit()

        # Create second section
        seccion2 = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 2",
            descripcion="Second section",
            indice=2,
            estado=True,
        )
        isolated_db_session.add(seccion2)
        isolated_db_session.commit()

        # Create resource in first section
        recurso1 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion1.id,
            nombre="Resource 1",
            descripcion="First resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso1)
        isolated_db_session.commit()

        # Create resource in second section
        recurso2 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion2.id,
            nombre="Resource 2",
            descripcion="Second resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso2)
        isolated_db_session.commit()

        # Test navigation - should navigate to next section
        indice = crear_indice_recurso(recurso1.id)
        assert indice.has_next is True
        assert indice.next_resource is not None
        assert indice.next_resource.codigo == recurso2.id
        assert indice.next_resource.curso_id == curso.codigo

    def test_no_devuelve_recursos_de_otro_curso(self, isolated_db_session):
        """Test that navigation doesn't return resources from other courses."""
        # Create first course
        curso1 = Curso(
            codigo="TEST05A",
            nombre="Test Course 1",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso1)
        isolated_db_session.commit()

        # Create second course
        curso2 = Curso(
            codigo="TEST05B",
            nombre="Test Course 2",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso2)
        isolated_db_session.commit()

        # Create section in course 1
        seccion1 = CursoSeccion(
            curso=curso1.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion1)
        isolated_db_session.commit()

        # Create section in course 2 with same index
        seccion2 = CursoSeccion(
            curso=curso2.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion2)
        isolated_db_session.commit()

        # Create resource in course 1
        recurso1 = CursoRecurso(
            curso=curso1.codigo,
            seccion=seccion1.id,
            nombre="Resource 1",
            descripcion="First resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso1)
        isolated_db_session.commit()

        # Create resource in course 2
        recurso2 = CursoRecurso(
            curso=curso2.codigo,
            seccion=seccion2.id,
            nombre="Resource 2",
            descripcion="Second resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso2)
        isolated_db_session.commit()

        # Test navigation - should not find next resource from other course
        indice = crear_indice_recurso(recurso1.id)
        assert indice.has_next is False or (
            indice.next_resource is not None and indice.next_resource.curso_id == curso1.codigo
        )

    def test_recursos_alternativos_consecutivos_muestran_seleccion(self, isolated_db_session):
        """Test that consecutive alternative resources trigger selection screen."""
        # Create course
        curso = Curso(
            codigo="TEST06",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create section
        seccion = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion)
        isolated_db_session.commit()

        # Create normal resource
        recurso1 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Resource 1",
            descripcion="First resource",
            tipo="text",
            indice=1,
            requerido="required",
        )
        isolated_db_session.add(recurso1)
        isolated_db_session.commit()

        # Create first alternative resource
        recurso2 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Alternative 1",
            descripcion="First alternative",
            tipo="text",
            indice=2,
            requerido=3,  # Alternative
        )
        isolated_db_session.add(recurso2)
        isolated_db_session.commit()

        # Create second alternative resource
        recurso3 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Alternative 2",
            descripcion="Second alternative",
            tipo="text",
            indice=3,
            requerido=3,  # Alternative
        )
        isolated_db_session.add(recurso3)
        isolated_db_session.commit()

        # Test navigation from first resource - should show alternatives
        indice = crear_indice_recurso(recurso1.id)
        assert indice.has_next is True
        # Should indicate next is alternative (consecutive alternatives)
        assert indice.next_is_alternative is True

    def test_recursos_alternativos_no_consecutivos_no_muestran_seleccion(self, isolated_db_session):
        """Test that non-consecutive alternative resources don't trigger selection screen."""
        # Create course
        curso = Curso(
            codigo="TEST07",
            nombre="Test Course",
            descripcion_corta="Short description",
            descripcion="Long description",
            estado="open",
        )
        isolated_db_session.add(curso)
        isolated_db_session.commit()

        # Create section
        seccion = CursoSeccion(
            curso=curso.codigo,
            nombre="Section 1",
            descripcion="First section",
            indice=1,
            estado=True,
        )
        isolated_db_session.add(seccion)
        isolated_db_session.commit()

        # Create first alternative resource
        recurso1 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Alternative 1",
            descripcion="First alternative",
            tipo="text",
            indice=1,
            requerido=3,  # Alternative
        )
        isolated_db_session.add(recurso1)
        isolated_db_session.commit()

        # Create normal resource (breaks consecutive alternatives)
        recurso2 = CursoRecurso(
            curso=curso.codigo,
            seccion=seccion.id,
            nombre="Normal Resource",
            descripcion="Normal resource",
            tipo="text",
            indice=2,
            requerido="required",
        )
        isolated_db_session.add(recurso2)
        isolated_db_session.commit()

        # Test navigation - next is not alternative (no consecutive alternatives)
        indice = crear_indice_recurso(recurso1.id)
        assert indice.has_next is True
        assert indice.next_is_alternative is False
