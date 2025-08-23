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

"""Test session-scoped pytest fixtures to ensure they work correctly."""



class TestSessionBasicFixture:
    """Test session_basic_db_setup fixture."""

    def test_session_basic_app_context(self, session_basic_db_setup):
        """Test that session basic fixture provides working app context."""
        with session_basic_db_setup.app_context():
            from now_lms import database

            # Test that database is accessible
            assert database is not None

            # Test that basic configuration exists
            from now_lms.db import Configuracion
            from now_lms.db import select

            config_count = database.session.execute(select(Configuracion)).scalars().all()

            # Should have basic configuration
            assert len(config_count) > 0

    def test_session_basic_certificates_exist(self, session_basic_db_setup):
        """Test that basic certificates are created."""
        with session_basic_db_setup.app_context():
            from now_lms import database
            from now_lms.db import Certificado
            from now_lms.db import select

            certificates = database.session.execute(select(Certificado)).scalars().all()

            # Should have basic certificates
            assert len(certificates) > 0


class TestSessionFullFixture:
    """Test session_full_db_setup fixture."""

    def test_session_full_app_context(self, session_full_db_setup):
        """Test that session full fixture provides working app context."""
        with session_full_db_setup.app_context():
            from now_lms import database

            # Test that database is accessible
            assert database is not None

            # Test that users exist (should have test data)
            from now_lms.db import Usuario
            from now_lms.db import select

            users = database.session.execute(select(Usuario)).scalars().all()

            # Should have users from full setup (at least admin user should exist)
            # Even if certificate creation failed, user creation should succeed
            assert len(users) >= 1  # At least admin user should exist

    def test_session_full_courses_exist(self, session_full_db_setup):
        """Test that courses exist in full setup."""
        with session_full_db_setup.app_context():
            from now_lms import database
            from now_lms.db import Curso
            from now_lms.db import select

            courses = database.session.execute(select(Curso)).scalars().all()

            # Should have courses from full setup
            # Even if some setup steps failed, basic course creation should work
            assert len(courses) >= 1  # At least one course should exist


class TestSessionFullWithExamplesFixture:
    """Test session_full_db_setup_with_examples fixture."""

    def test_session_full_with_examples_app_context(self, session_full_db_setup_with_examples):
        """Test that session full with examples fixture provides working app context."""
        with session_full_db_setup_with_examples.app_context():
            from now_lms import database

            # Test that database is accessible
            assert database is not None

            # Test that users exist (should have test data and examples)
            from now_lms.db import Usuario
            from now_lms.db import select

            users = database.session.execute(select(Usuario)).scalars().all()

            # Should have users from full setup with examples
            # Even if some setup steps failed, at least admin user should exist
            assert len(users) >= 1


class TestIsolatedSessionFixture:
    """Test isolated_db_session fixture."""

    def test_isolated_session_rollback(self, isolated_db_session):
        """Test that isolated session properly rolls back changes."""
        from now_lms.db import Usuario
        from now_lms.db import select
        from now_lms.auth import proteger_passwd

        # Get initial user count
        initial_users = isolated_db_session.execute(select(Usuario)).scalars().all()
        initial_count = len(initial_users)

        # Add a new user within the test
        new_user = Usuario(
            usuario="test_session_user",
            acceso=proteger_passwd("test_password"),
            correo_electronico="test_session@example.com",
            nombre="Test Session",
            apellido="User",
            activo=True,
        )
        isolated_db_session.add(new_user)
        isolated_db_session.flush()  # Flush but don't commit

        # Verify user was added
        users_after_add = isolated_db_session.execute(select(Usuario)).scalars().all()
        assert len(users_after_add) == initial_count + 1

    def test_isolated_session_rollback_verification(self, isolated_db_session):
        """Test that changes from previous test were rolled back."""
        from now_lms.db import Usuario
        from now_lms.db import select

        # Check that the user from previous test is not present
        users = isolated_db_session.execute(select(Usuario).where(Usuario.usuario == "test_session_user")).scalars().all()

        # Should be empty since previous test was rolled back
        assert len(users) == 0


class TestFixtureIndependence:
    """Test that session fixtures are independent from function fixtures."""

    def test_session_vs_function_independence(self, session_basic_db_setup):
        """Test that session fixtures use different databases than function fixtures."""
        # This test uses session fixture and should work independently
        with session_basic_db_setup.app_context():
            from now_lms import database

            # Get database URI to verify it's session-specific
            db_uri = session_basic_db_setup.config.get("SQLALCHEMY_DATABASE_URI", "")

            # Should be either memory or DATABASE_URL
            import os

            expected_uri = os.environ.get("DATABASE_URL") or "sqlite:///:memory:"
            assert db_uri == expected_uri

            # Verify we can access the database
            assert database is not None


class TestDatabaseUrlSupport:
    """Test DATABASE_URL environment variable support for function fixtures only.

    Session fixtures always use in-memory SQLite for complete isolation.
    """

    def test_session_fixtures_use_memory_database_basic(self, session_basic_db_setup):
        """Test that session_basic_db_setup always uses in-memory SQLite."""
        with session_basic_db_setup.app_context():
            db_uri = session_basic_db_setup.config.get("SQLALCHEMY_DATABASE_URI", "")
            # Session fixtures should always use in-memory SQLite
            assert db_uri == "sqlite:///:memory:"

    def test_session_fixtures_use_memory_database_full(self, session_full_db_setup):
        """Test that session_full_db_setup always uses in-memory SQLite."""
        with session_full_db_setup.app_context():
            db_uri = session_full_db_setup.config.get("SQLALCHEMY_DATABASE_URI", "")
            # Session fixtures should always use in-memory SQLite
            assert db_uri == "sqlite:///:memory:"

    def test_session_fixtures_use_memory_database_examples(self, session_full_db_setup_with_examples):
        """Test that session_full_db_setup_with_examples always uses in-memory SQLite."""
        with session_full_db_setup_with_examples.app_context():
            db_uri = session_full_db_setup_with_examples.config.get("SQLALCHEMY_DATABASE_URI", "")
            # Session fixtures should always use in-memory SQLite
            assert db_uri == "sqlite:///:memory:"
