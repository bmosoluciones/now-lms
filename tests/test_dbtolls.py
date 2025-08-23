

def test_database_info_tools(session_full_db_setup):
    with session_full_db_setup.app_context():
        from now_lms.db.tools import database_is_populated

        assert database_is_populated(session_full_db_setup)
        from now_lms.db.info import course_info

        assert course_info("now")
        from now_lms.db.info import config_info

        assert config_info()
        from now_lms.db.info import lms_info

        assert lms_info()
        from now_lms.db.info import _obtener_info_sistema

        assert _obtener_info_sistema()
        from now_lms.db.tools import get_one_record

        curso = get_one_record("Curso", "now", "codigo")
        assert curso is not None

        curso = get_one_record("Curso", True, "publico")
        assert curso is None

        curso = get_one_record("Curso", "FFFFFFFFFF")
        assert curso is not None

        curso = get_one_record("Curso", "holaFFFFFFFFFF")
        assert curso is None

        from now_lms.db.tools import get_all_records

        cursos = get_all_records("Curso")
        assert cursos is not None

        usuarios = get_all_records("Usuario", {"tipo": "admin"})
        assert usuarios is not None

        vacio = get_all_records("Hola")
        assert vacio is None


def test_db_tools_negative():
    from now_lms import lms_app

    with lms_app.app_context():
        from now_lms.db.tools import database_is_populated, check_db_access, get_current_theme

        assert not database_is_populated(lms_app)
        assert check_db_access(lms_app)  # True with SQLite
        assert get_current_theme() == "now_lms"


def test_user_access_negative(lms_application):
    with lms_application.app_context():
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario, database

        user = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",  # Rol requerido por la vista
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(user)
        database.session.commit()

        # Iniciar sesión como instructor
        with lms_application.test_client() as client:
            login_response = client.post(
                "/user/login",
                data={"usuario": "instructor1", "acceso": "testpass"},
                follow_redirects=True,
            )
            assert login_response.status_code == 200
            from now_lms.db.tools import verifica_docente_asignado_a_curso, verifica_moderador_asignado_a_curso

            assert verifica_docente_asignado_a_curso("now") is False
            assert verifica_moderador_asignado_a_curso("now") is False


def test_get_course_sections_empty(lms_application):
    """Test get_course_sections returns empty list for non-existent course."""
    with lms_application.app_context():
        from now_lms.db.tools import get_course_sections

        # Test with non-existent course
        sections = get_course_sections("nonexistent")
        assert sections == []

        # Test with empty course code
        sections = get_course_sections("")
        assert sections == []

        # Test with None course code
        sections = get_course_sections(None)
        assert sections == []


def test_get_course_sections_with_data(minimal_db_setup):
    """Test get_course_sections returns proper sections for existing course."""
    with minimal_db_setup.app_context():
        from now_lms.db import Curso, CursoSeccion, database
        from now_lms.db.tools import get_course_sections

        # Create a test course
        course = Curso(
            codigo="TEST_COURSE",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course long description",
            estado="draft",
            plantilla_certificado=None,  # Explicitly set to None to avoid FK constraint
        )
        database.session.add(course)
        database.session.commit()

        # Create test sections in different order to test ordering
        section1 = CursoSeccion(
            curso="TEST_COURSE",
            nombre="Section 1",
            descripcion="First section",
            indice=1,
        )
        section3 = CursoSeccion(
            curso="TEST_COURSE",
            nombre="Section 3",
            descripcion="Third section",
            indice=3,
        )
        section2 = CursoSeccion(
            curso="TEST_COURSE",
            nombre="Section 2",
            descripcion="Second section",
            indice=2,
        )

        database.session.add(section1)
        database.session.add(section3)
        database.session.add(section2)
        database.session.commit()

        # Test getting sections
        sections = get_course_sections("TEST_COURSE")

        # Should have 3 sections
        assert len(sections) == 3

        # Should be ordered by indice
        assert sections[0].nombre == "Section 1"
        assert sections[0].indice == 1
        assert sections[1].nombre == "Section 2"
        assert sections[1].indice == 2
        assert sections[2].nombre == "Section 3"
        assert sections[2].indice == 3

        # Test with different course that has no sections
        course2 = Curso(
            codigo="EMPTY_COURSE",
            nombre="Empty Course",
            descripcion_corta="Course with no sections",
            descripcion="Course with no sections",
            estado="draft",
            plantilla_certificado=None,  # Explicitly set to None to avoid FK constraint
        )
        database.session.add(course2)
        database.session.commit()

        empty_sections = get_course_sections("EMPTY_COURSE")
        assert empty_sections == []


def test_get_course_sections_jinja_global(minimal_db_setup):
    """Test that get_course_sections is available as a Jinja global variable."""
    with minimal_db_setup.app_context():
        from flask import render_template_string
        from now_lms.db import Curso, CursoSeccion, database

        # Create a test course with sections
        course = Curso(
            codigo="JINJA_TEST",
            nombre="Jinja Test Course",
            descripcion_corta="Test course for jinja",
            descripcion="Test course for jinja integration",
            estado="draft",
            plantilla_certificado=None,  # Explicitly set to None to avoid FK constraint
        )
        database.session.add(course)
        database.session.commit()

        section = CursoSeccion(
            curso="JINJA_TEST",
            nombre="Test Section",
            descripcion="Test section for jinja",
            indice=1,
        )
        database.session.add(section)
        database.session.commit()

        # Test that get_course_sections is available in Jinja context
        template = "{{ get_course_sections('JINJA_TEST')|length }}"
        result = render_template_string(template)
        assert result == "1"

        # Test accessing section properties
        template = "{{ get_course_sections('JINJA_TEST')[0].nombre }}"
        result = render_template_string(template)
        assert result == "Test Section"

        # Test with non-existent course
        template = "{{ get_course_sections('NONEXISTENT')|length }}"
        result = render_template_string(template)
        assert result == "0"
