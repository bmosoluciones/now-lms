"""
Test audit field validation for foreign key constraint issues.

This test ensures that audit fields (creado_por, modificado_por) properly handle
user references and maintain data consistency even when users don't exist.
"""

from now_lms.db import database, Usuario, Curso
from now_lms.auth import proteger_passwd


class TestAuditFieldValidation:
    """Test audit field validation functionality."""

    def test_invalid_user_reference_cleared(self, isolated_db_session):
        """Test that invalid user references in audit fields are cleared."""
        # Try to create a course with a non-existent user in creado_por
        curso = Curso(
            codigo="test_invalid_user",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="nonexistent_user",  # This user doesn't exist
        )

        database.session.add(curso)
        database.session.commit()

        # Check that creado_por was set to None
        created_course = database.session.execute(database.select(Curso).filter_by(codigo="test_invalid_user")).scalar_one()

        assert created_course.creado_por is None, "Invalid user reference should be cleared"

    def test_valid_user_reference_preserved(self, isolated_db_session):
        """Test that valid user references in audit fields are preserved."""
        # Create a user first
        instructor = Usuario(
            usuario="test_instructor_audit",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

        # Create a course with valid user reference
        curso = Curso(
            codigo="test_valid_user",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="test_instructor_audit",  # This user exists
        )

        database.session.add(curso)
        database.session.commit()

        # Check that creado_por was preserved
        created_course = database.session.execute(database.select(Curso).filter_by(codigo="test_valid_user")).scalar_one()

        assert created_course.creado_por == "test_instructor_audit", "Valid user reference should be preserved"

    def test_update_with_invalid_user_cleared(self, isolated_db_session):
        """Test that invalid user references are cleared during updates."""
        # Create a user and course
        instructor = Usuario(
            usuario="update_instructor_audit",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor)
        database.session.commit()

        curso = Curso(
            codigo="test_update",
            nombre="Test Course",
            descripcion_corta="Test course description",
            descripcion="Test course description",
            estado="draft",
            pagado=False,
            creado_por="update_instructor_audit",
        )
        database.session.add(curso)
        database.session.commit()

        # Update with invalid user reference
        curso.modificado_por = "nonexistent_updater"
        database.session.commit()

        # Refresh the instance
        database.session.refresh(curso)

        assert curso.modificado_por is None, "Invalid user reference should be cleared on update"
        assert curso.creado_por == "update_instructor_audit", "Valid original reference should remain"
