"""
Test to verify that previously problematic view operations now have proper audit trails.
"""

from flask_login import login_user
from now_lms.db import database, Usuario, Categoria
from now_lms.auth import proteger_passwd
from datetime import date


def test_category_creation_now_has_audit_trail(app, minimal_db_setup):
    """Test that category creation (which was missing audit trails) now works correctly."""
    # Create a test user
    test_user = Usuario(
        usuario="category_test_user",
        acceso=proteger_passwd("testpass"),
        nombre="Test",
        apellido="User",
        tipo="instructor",
        activo=True,
        correo_electronico_verificado=True,
    )
    database.session.add(test_user)
    database.session.commit()

    # Simulate the problematic category creation from categories.py
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = test_user.usuario
            sess["_fresh"] = True

        with app.test_request_context():
            login_user(test_user)

            # This mimics the problematic code from categories.py:57-61
            categoria = Categoria(
                nombre="Test Category",
                descripcion="Test category description",
            )
            database.session.add(categoria)
            database.session.commit()

            # Refresh the instance
            database.session.refresh(categoria)

            # Now it should have proper audit trails automatically
            assert categoria.creado_por == "category_test_user"
            # Check that creado date is recent (within 1 day) to handle timezone differences
            today = date.today()
            assert categoria.creado is not None
            assert abs((categoria.creado - today).days) <= 1
            assert categoria.modificado_por is None  # New records don't have modificado_por
            assert categoria.modificado is None


def test_user_creation_patterns_work(app, minimal_db_setup):
    """Test that user creation (which sets creado_por manually) still works."""
    with app.test_request_context():
        # This mimics the pattern from users.py:110-119
        usuario_ = Usuario(
            usuario="newuser@example.com",
            acceso=proteger_passwd("password123"),
            nombre="New",
            apellido="User",
            correo_electronico="newuser@example.com",
            tipo="student",
            activo=False,
            creado_por="newuser@example.com",  # Manual setting like in users.py
        )

        database.session.add(usuario_)
        database.session.commit()

        # Refresh the instance
        database.session.refresh(usuario_)

        # Manual creado_por should be preserved
        assert usuario_.creado_por == "newuser@example.com"
        # Check that creado date is recent (within 1 day) to handle timezone differences
        today = date.today()
        assert usuario_.creado is not None
        assert abs((usuario_.creado - today).days) <= 1
