"""
Test automatic audit field population functionality.

This test ensures that audit fields (creado_por, modificado_por, creado, modificado)
are automatically populated for all BaseTabla instances when records are created or modified.
"""

import time
from datetime import date, datetime


from now_lms.auth import proteger_passwd
from now_lms.db import Categoria, Curso, Usuario, database


class TestAutomaticAuditFields:
    """Test automatic audit field population functionality."""

    def test_automatic_audit_fields_on_create_with_authenticated_user(self, session_basic_db_setup):
        """Test that audit fields are automatically populated when creating new records with authenticated user."""
        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        username = f"test_audit_user_{unique_suffix}"

        with session_basic_db_setup.app_context():
            # Create a test user
            test_user = Usuario(
                usuario=username,
                acceso=proteger_passwd("testpass"),
                nombre="Test",
                apellido="User",
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(test_user)
            database.session.commit()

            # Simulate authenticated user context
            with session_basic_db_setup.test_client() as client:
                with client.session_transaction() as sess:
                    sess["_user_id"] = test_user.usuario
                    sess["_fresh"] = True

                with session_basic_db_setup.test_request_context():
                    from flask_login import login_user

                    login_user(test_user)

                    # Create a new record without explicitly setting audit fields
                    categoria = Categoria(nombre=f"Test Category {unique_suffix}", descripcion="Test category description")

                    # Audit fields should be None before adding to session
                    assert categoria.creado_por is None
                    assert categoria.modificado_por is None

                    database.session.add(categoria)
                    database.session.commit()

                    # Refresh the instance to get updated values
                    database.session.refresh(categoria)

                    # Verify audit fields were automatically populated
                    assert categoria.creado_por == username
                    # Check that creado date is recent (within 1 day) to handle timezone differences
                    today = date.today()
                    assert categoria.creado is not None
                    assert abs((categoria.creado - today).days) <= 1
                    # modificado_por should still be None for new records
                    assert categoria.modificado_por is None
                    assert categoria.modificado is None

    def test_automatic_audit_fields_on_update_with_authenticated_user(self, session_basic_db_setup):
        """Test that audit fields are automatically populated when updating records with authenticated user."""
        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        username = f"test_update_user_{unique_suffix}"

        with session_basic_db_setup.app_context():
            # Create a test user
            test_user = Usuario(
                usuario=username,
                acceso=proteger_passwd("testpass"),
                nombre="Test",
                apellido="User",
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(test_user)
            database.session.commit()

            # Simulate authenticated user context
            with session_basic_db_setup.test_client() as client:
                with client.session_transaction() as sess:
                    sess["_user_id"] = test_user.usuario
                    sess["_fresh"] = True

                with session_basic_db_setup.test_request_context():
                    from flask_login import login_user

                    login_user(test_user)

                    # Create a record first
                    curso = Curso(
                        codigo=f"test_update_{unique_suffix}",
                        nombre="Test Course",
                        descripcion_corta="Test course description",
                        descripcion="Test course description",
                        estado="draft",
                        pagado=False,
                    )
                    database.session.add(curso)
                    database.session.commit()

                    # Verify initial creation audit fields
                    database.session.refresh(curso)
                    original_creado_por = curso.creado_por
                    original_creado = curso.creado

                    assert original_creado_por == username
                    # Check that creado date is recent (within 1 day) to handle timezone differences
                    today = date.today()
                    assert original_creado is not None
                    assert abs((original_creado - today).days) <= 1

                    # Now update the record
                    curso.nombre = "Updated Course Name"
                    database.session.commit()

                    # Refresh the instance
                    database.session.refresh(curso)

                    # Verify modification audit fields were set
                    assert curso.modificado_por == username
                    assert curso.modificado is not None
                    assert isinstance(curso.modificado, datetime)

                    # Original creation fields should remain unchanged
                    assert curso.creado_por == original_creado_por
                    assert curso.creado == original_creado

    def test_audit_fields_without_user_context(self, session_basic_db_setup):
        """Test that audit fields handle cases where no user context is available."""
        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000

        with session_basic_db_setup.app_context():
            # Create a record without user context (e.g., from a background job)
            categoria = Categoria(
                nombre=f"Background Category {unique_suffix}", descripcion="Category created without user context"
            )

            database.session.add(categoria)
            database.session.commit()

            # Refresh the instance
            database.session.refresh(categoria)

            # creado_por should be None since no user context
            assert categoria.creado_por is None
            # creado should still be set to a recent date (within 1 day) to handle timezone differences
            today = date.today()
            assert categoria.creado is not None
            assert abs((categoria.creado - today).days) <= 1
            # modificado fields should be None for new records
            assert categoria.modificado_por is None
            assert categoria.modificado is None

    def test_manual_audit_fields_preserved(self, session_basic_db_setup):
        """Test that manually set audit fields are preserved."""
        # Generate unique identifiers to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        test_username = f"test_manual_user_{unique_suffix}"
        manual_username = f"manual_user_{unique_suffix}"

        with session_basic_db_setup.app_context():
            # Create two test users - one to act as current user, another for manual assignment
            test_user = Usuario(
                usuario=test_username,
                acceso=proteger_passwd("testpass"),
                nombre="Test",
                apellido="User",
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )

            manual_user = Usuario(
                usuario=manual_username,
                acceso=proteger_passwd("testpass"),
                nombre="Manual",
                apellido="User",
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )

            database.session.add(test_user)
            database.session.add(manual_user)
            database.session.commit()

            # Simulate authenticated user context
            with session_basic_db_setup.test_client() as client:
                with client.session_transaction() as sess:
                    sess["_user_id"] = test_user.usuario
                    sess["_fresh"] = True

                with session_basic_db_setup.test_request_context():
                    from flask_login import login_user

                    login_user(test_user)

                    # Create a record with manually set audit fields
                    curso = Curso(
                        codigo=f"test_manual_{unique_suffix}",
                        nombre="Manual Course",
                        descripcion_corta="Manually created course",
                        descripcion="Course with manual audit fields",
                        estado="draft",
                        pagado=False,
                        creado_por=manual_username,  # Manually set to existing user
                    )

                    database.session.add(curso)
                    database.session.commit()

                    # Refresh the instance
                    database.session.refresh(curso)

                    # Manually set creado_por should be preserved
                    assert curso.creado_por == manual_username
                    # Other fields should still be set automatically - check that creado date is recent
                    today = date.today()
                    assert curso.creado is not None
                    assert abs((curso.creado - today).days) <= 1
