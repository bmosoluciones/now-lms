"""Comprehensive tests for now_lms.db.tools module to improve coverage."""

from unittest.mock import patch


class TestDatabaseUtilities:
    """Test database utility functions in db.tools."""

    def test_database_select_version_query(self, lms_application):
        """Test database_select_version_query for different database types."""
        from now_lms.db.tools import database_select_version_query

        with lms_application.app_context():
            # Test SQLite (default in tests)
            query = database_select_version_query(lms_application)
            assert query == "SELECT sqlite_version() AS version;"

            # Test PostgreSQL
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@host/db"}):
                query = database_select_version_query(lms_application)
                assert query == "SELECT version() AS version;"

            # Test MySQL
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "mysql://user:pass@host/db"}):
                query = database_select_version_query(lms_application)
                assert query == "SELECT VERSION() AS version;"

            # Test MariaDB
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "mariadb://user:pass@host/db"}):
                query = database_select_version_query(lms_application)
                assert query == "SELECT VERSION() AS version;"

            # Test unknown database
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "unknown://user:pass@host/db"}):
                query = database_select_version_query(lms_application)
                assert query is None

    def test_database_select_version(self, lms_application):
        """Test database_select_version for different database types."""
        from now_lms.db.tools import database_select_version

        with lms_application.app_context():
            # Test SQLite (default in tests)
            query = database_select_version(lms_application)
            assert "sqlite_master" in query

            # Test PostgreSQL
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@host/db"}):
                query = database_select_version(lms_application)
                assert "pg_tables" in query

            # Test MySQL
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "mysql://user:pass@host/db"}):
                query = database_select_version(lms_application)
                assert "SHOW TABLES" in query

            # Test unknown database
            with patch.dict(lms_application.config, {"SQLALCHEMY_DATABASE_URI": "unknown://user:pass@host/db"}):
                query = database_select_version(lms_application)
                assert query is None

    def test_check_db_access_errors(self, lms_application):
        """Test check_db_access error handling."""
        from now_lms.db.tools import check_db_access
        from sqlalchemy.exc import OperationalError, ProgrammingError
        from pg8000.dbapi import ProgrammingError as PGProgrammingError
        from pg8000.exceptions import DatabaseError

        with lms_application.app_context():
            # Test OperationalError
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = OperationalError("test", "test", "test")
                assert check_db_access(lms_application) is False

            # Test ProgrammingError
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = ProgrammingError("test", "test", "test")
                assert check_db_access(lms_application) is False

            # Test PGProgrammingError
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = PGProgrammingError("test")
                assert check_db_access(lms_application) is False

            # Test DatabaseError
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = DatabaseError("test")
                assert check_db_access(lms_application) is False

            # Test AttributeError
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = AttributeError("test")
                assert check_db_access(lms_application) is False


class TestContentCounters:
    """Test content counting functions."""

    def test_cursos_por_etiqueta(self, minimal_db_setup):
        """Test cursos_por_etiqueta function."""
        from now_lms.db.tools import cursos_por_etiqueta
        from now_lms.db import Etiqueta, EtiquetaCurso, Curso, database

        with minimal_db_setup.app_context():
            # Create test tag
            tag = Etiqueta(nombre="TestTag", color="#FF0000")
            database.session.add(tag)
            database.session.flush()

            # Create test course
            course = Curso(
                codigo="TEST_COURSE",
                nombre="Test Course",
                descripcion_corta="Test course description",
                descripcion="Test course long description",
                estado="draft",
                plantilla_certificado=None,
            )
            database.session.add(course)
            database.session.flush()

            # Link course to tag
            link = EtiquetaCurso(curso="TEST_COURSE", etiqueta=tag.id)
            database.session.add(link)
            database.session.commit()

            # Test count
            count = cursos_por_etiqueta(tag.id)
            assert count == 1

            # Test with non-existent tag
            count = cursos_por_etiqueta("NON_EXISTENT")
            assert count == 0

    def test_cursos_por_categoria(self, minimal_db_setup):
        """Test cursos_por_categoria function."""
        from now_lms.db.tools import cursos_por_categoria
        from now_lms.db import Categoria, CategoriaCurso, Curso, database

        with minimal_db_setup.app_context():
            # Create test category
            category = Categoria(nombre="TestCategory", descripcion="Test category")
            database.session.add(category)
            database.session.flush()

            # Create test course
            course = Curso(
                codigo="TEST_COURSE_CAT",
                nombre="Test Course for Category",
                descripcion_corta="Test course description",
                descripcion="Test course long description",
                estado="draft",
                plantilla_certificado=None,
            )
            database.session.add(course)
            database.session.flush()

            # Link course to category
            link = CategoriaCurso(curso="TEST_COURSE_CAT", categoria=category.id)
            database.session.add(link)
            database.session.commit()

            # Test count
            count = cursos_por_categoria(category.id)
            assert count == 1

            # Test with non-existent category
            count = cursos_por_categoria("NON_EXISTENT")
            assert count == 0


class TestChoiceGenerators:
    """Test choice generation functions for forms."""

    def test_generate_user_choices(self, minimal_db_setup):
        """Test generate_user_choices function."""
        from now_lms.db.tools import generate_user_choices
        from now_lms.db import Usuario, database

        with minimal_db_setup.app_context():
            # Create test user
            user = Usuario(
                usuario="testuser",
                acceso=b"password123",
                nombre="Test",
                apellido="User",
                correo_electronico="test@example.com",
                tipo="student",
            )
            database.session.add(user)
            database.session.commit()

            # Test choices generation
            choices = generate_user_choices()
            assert len(choices) >= 1
            assert any(choice[0] == "testuser" and choice[1] == "Test User" for choice in choices)

    def test_generate_cource_choices(self, minimal_db_setup):
        """Test generate_cource_choices function."""
        from now_lms.db.tools import generate_cource_choices
        from now_lms.db import Curso, database

        with minimal_db_setup.app_context():
            # Create test course
            course = Curso(
                codigo="TEST_CHOICES",
                nombre="Test Course for Choices",
                descripcion_corta="Test course description",
                descripcion="Test course long description",
                estado="draft",
                plantilla_certificado=None,
            )
            database.session.add(course)
            database.session.commit()

            # Test choices generation
            choices = generate_cource_choices()
            assert len(choices) >= 1
            assert any(choice[0] == "TEST_CHOICES" and choice[1] == "Test Course for Choices" for choice in choices)

    def test_generate_masterclass_choices(self, minimal_db_setup):
        """Test generate_masterclass_choices function."""
        from now_lms.db.tools import generate_masterclass_choices
        from now_lms.db import MasterClass, Usuario, database
        from datetime import date, time

        with minimal_db_setup.app_context():
            # Create instructor
            instructor = Usuario(
                usuario="mc_instructor",
                acceso=b"password123",
                nombre="MasterClass",
                apellido="Instructor",
                correo_electronico="mcteacher@example.com",
                tipo="teacher",
            )
            database.session.add(instructor)
            database.session.flush()

            # Create test master class
            masterclass = MasterClass(
                title="Test Master Class",
                slug="test-masterclass",
                description_public="Test master class description",
                date=date(2026, 6, 15),
                start_time=time(10, 0),
                end_time=time(12, 0),
                platform_name="Google Meet",
                platform_url="https://meet.google.com/test-link",
                instructor_id=instructor.usuario,
            )
            database.session.add(masterclass)
            database.session.commit()

            # Test choices generation
            choices = generate_masterclass_choices()
            assert len(choices) >= 1
            assert any(choice[1] == "Test Master Class" for choice in choices)

    def test_generate_template_choices(self, minimal_db_setup):
        """Test generate_template_choices function."""
        from now_lms.db.tools import generate_template_choices

        with minimal_db_setup.app_context():
            # Test choices generation (certificates should be created by minimal_db_setup)
            choices = generate_template_choices()
            assert len(choices) >= 1
            assert all(len(choice) == 2 for choice in choices)

    def test_generate_category_choices(self, minimal_db_setup):
        """Test generate_category_choices function."""
        from now_lms.db.tools import generate_category_choices
        from now_lms.db import Categoria, database

        with minimal_db_setup.app_context():
            # Create test category
            category = Categoria(nombre="TestCategory", descripcion="Test category")
            database.session.add(category)
            database.session.commit()

            # Test choices generation
            choices = generate_category_choices()
            assert len(choices) >= 2  # At least empty option + test category
            assert choices[0] == ("", "-- Seleccionar categoría --")
            assert any(choice[1] == "TestCategory" for choice in choices)

    def test_generate_tag_choices(self, minimal_db_setup):
        """Test generate_tag_choices function."""
        from now_lms.db.tools import generate_tag_choices
        from now_lms.db import Etiqueta, database

        with minimal_db_setup.app_context():
            # Create test tag
            tag = Etiqueta(nombre="TestTag", color="#FF0000")
            database.session.add(tag)
            database.session.commit()

            # Test choices generation
            choices = generate_tag_choices()
            assert len(choices) >= 1
            assert any(choice[1] == "TestTag" for choice in choices)


class TestFeatureFlags:
    """Test feature flag functions."""

    def test_is_programs_enabled(self, minimal_db_setup):
        """Test is_programs_enabled function."""
        from now_lms.db.tools import is_programs_enabled
        from now_lms.db import Configuracion, database

        with minimal_db_setup.app_context():
            # Test when programs are enabled
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            if config:
                config.enable_programs = True
                database.session.commit()
                assert is_programs_enabled() is True

                config.enable_programs = False
                database.session.commit()
                assert is_programs_enabled() is False
            else:
                # No config exists, should return False
                assert is_programs_enabled() is False

    def test_is_masterclass_enabled(self, minimal_db_setup):
        """Test is_masterclass_enabled function."""
        from now_lms.db.tools import is_masterclass_enabled
        from now_lms.db import Configuracion, database

        with minimal_db_setup.app_context():
            # Test when masterclass is enabled
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            if config:
                config.enable_masterclass = True
                database.session.commit()
                assert is_masterclass_enabled() is True

                config.enable_masterclass = False
                database.session.commit()
                assert is_masterclass_enabled() is False
            else:
                # No config exists, should return False
                assert is_masterclass_enabled() is False

    def test_is_resources_enabled(self, minimal_db_setup):
        """Test is_resources_enabled function."""
        from now_lms.db.tools import is_resources_enabled
        from now_lms.db import Configuracion, database

        with minimal_db_setup.app_context():
            # Test when resources are enabled
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            if config:
                config.enable_resources = True
                database.session.commit()
                assert is_resources_enabled() is True

                config.enable_resources = False
                database.session.commit()
                assert is_resources_enabled() is False
            else:
                # No config exists, should return False
                assert is_resources_enabled() is False

    def test_is_blog_enabled(self, minimal_db_setup):
        """Test is_blog_enabled function."""
        from now_lms.db.tools import is_blog_enabled

        with minimal_db_setup.app_context():
            # Blog is typically always enabled, test the function exists and returns bool
            result = is_blog_enabled()
            assert isinstance(result, bool)


class TestAdSenseFunctions:
    """Test AdSense-related functions."""

    def test_get_addsense_meta(self, minimal_db_setup):
        """Test get_addsense_meta function."""
        from now_lms.db.tools import get_addsense_meta

        with minimal_db_setup.app_context():
            # Test when no AdSense config exists or is disabled
            meta = get_addsense_meta()
            assert meta == ""

    def test_get_addsense_code(self, minimal_db_setup):
        """Test get_addsense_code function."""
        from now_lms.db.tools import get_addsense_code

        with minimal_db_setup.app_context():
            # Test when no AdSense config exists or is disabled
            code = get_addsense_code()
            assert code == ""

    def test_get_adsense_enabled(self, minimal_db_setup):
        """Test get_adsense_enabled function."""
        from now_lms.db.tools import get_adsense_enabled

        with minimal_db_setup.app_context():
            # Test when no AdSense config exists
            enabled = get_adsense_enabled()
            assert enabled is False

    def test_get_ad_functions(self, minimal_db_setup):
        """Test various ad placement functions."""
        from now_lms.db.tools import (
            get_ad_leaderboard,
            get_ad_medium_rectangle,
            get_ad_large_rectangle,
            get_ad_mobile_banner,
            get_ad_wide_skyscraper,
            get_ad_skyscraper,
            get_ad_large_skyscraper,
            get_ad_billboard,
        )

        with minimal_db_setup.app_context():
            # Test all ad functions return empty string when no config exists
            assert get_ad_leaderboard() == ""
            assert get_ad_medium_rectangle() == ""
            assert get_ad_large_rectangle() == ""
            assert get_ad_mobile_banner() == ""
            assert get_ad_wide_skyscraper() == ""
            assert get_ad_skyscraper() == ""
            assert get_ad_large_skyscraper() == ""
            assert get_ad_billboard() == ""


class TestCourseTagsAndCategories:
    """Test course/program tags and categories functions."""

    def test_get_course_category(self, minimal_db_setup):
        """Test get_course_category function."""
        from now_lms.db.tools import get_course_category
        from now_lms.db import Categoria, CategoriaCurso, Curso, database

        with minimal_db_setup.app_context():
            # Create test category and course
            category = Categoria(nombre="TestCategory", descripcion="Test category")
            database.session.add(category)
            database.session.flush()

            course = Curso(
                codigo="TEST_COURSE_CAT",
                nombre="Test Course",
                descripcion_corta="Test course description",
                descripcion="Test course long description",
                estado="draft",
                plantilla_certificado=None,
            )
            database.session.add(course)
            database.session.flush()

            # Link course to category
            link = CategoriaCurso(curso="TEST_COURSE_CAT", categoria=category.id)
            database.session.add(link)
            database.session.commit()

            # Test getting category
            result = get_course_category("TEST_COURSE_CAT")
            assert result == category.id

            # Test with non-existent course
            result = get_course_category("NON_EXISTENT")
            assert result is None

    def test_get_course_tags(self, minimal_db_setup):
        """Test get_course_tags function."""
        from now_lms.db.tools import get_course_tags
        from now_lms.db import Etiqueta, EtiquetaCurso, Curso, database

        with minimal_db_setup.app_context():
            # Create test tags and course
            tag1 = Etiqueta(nombre="Tag1", color="#FF0000")
            tag2 = Etiqueta(nombre="Tag2", color="#00FF00")
            database.session.add_all([tag1, tag2])
            database.session.flush()

            course = Curso(
                codigo="TEST_COURSE_TAGS",
                nombre="Test Course",
                descripcion_corta="Test course description",
                descripcion="Test course long description",
                estado="draft",
                plantilla_certificado=None,
            )
            database.session.add(course)
            database.session.flush()

            # Link course to tags
            link1 = EtiquetaCurso(curso="TEST_COURSE_TAGS", etiqueta=tag1.id)
            link2 = EtiquetaCurso(curso="TEST_COURSE_TAGS", etiqueta=tag2.id)
            database.session.add_all([link1, link2])
            database.session.commit()

            # Test getting tags
            result = get_course_tags("TEST_COURSE_TAGS")
            assert len(result) == 2
            assert tag1.id in result
            assert tag2.id in result

            # Test with non-existent course
            result = get_course_tags("NON_EXISTENT")
            assert result == []


class TestGetCurrentThemeErrors:
    """Test get_current_theme error handling."""

    def test_get_current_theme_attribute_error(self, lms_application):
        """Test get_current_theme handles AttributeError."""
        from now_lms.db.tools import get_current_theme

        with lms_application.app_context():
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = AttributeError("test")
                theme = get_current_theme()
                assert theme == "now_lms"

    def test_get_current_theme_operational_error(self, lms_application):
        """Test get_current_theme handles OperationalError."""
        from now_lms.db.tools import get_current_theme
        from sqlalchemy.exc import OperationalError

        with lms_application.app_context():
            with patch("now_lms.db.tools.database.session.execute") as mock_execute:
                mock_execute.side_effect = OperationalError("test", "test", "test")
                theme = get_current_theme()
                assert theme == "now_lms"
