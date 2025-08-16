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
#

"""Tests to verify database rollback behavior in exception handling."""

from sqlalchemy.exc import OperationalError
from now_lms.db import database, Etiqueta


def test_database_session_consistency_after_rollback(app, db_session):
    """Test that database session is consistent after rollback."""
    # Create an object but simulate commit failure
    etiqueta = Etiqueta(nombre="Test Tag", color="#FF0000")
    database.session.add(etiqueta)

    # Verify object is in session
    assert etiqueta in database.session.new

    # Simulate an exception scenario by manually calling rollback
    database.session.rollback()

    # After rollback, session should be clean
    assert len(database.session.new) == 0
    assert len(database.session.dirty) == 0

    # Database should not contain the object
    query_result = database.session.query(Etiqueta).filter_by(nombre="Test Tag").first()
    assert query_result is None


def test_rollback_preserves_database_integrity(app, db_session):
    """Test that rollback preserves database integrity by not committing partial changes."""
    # Add a tag successfully first
    original_tag = Etiqueta(nombre="Original Tag", color="#00FF00")
    database.session.add(original_tag)
    database.session.commit()

    # Now try to add another tag but simulate failure
    failing_tag = Etiqueta(nombre="Failing Tag", color="#FF0000")
    database.session.add(failing_tag)

    # Simulate commit failure and rollback
    try:
        # Force an exception after adding to session but before commit
        raise OperationalError("Simulated error", None, None)
    except OperationalError:
        database.session.rollback()

    # Original tag should still exist
    existing_tags = database.session.query(Etiqueta).all()
    assert len(existing_tags) == 1
    assert existing_tags[0].nombre == "Original Tag"

    # Failing tag should not exist
    failing_query = database.session.query(Etiqueta).filter_by(nombre="Failing Tag").first()
    assert failing_query is None


def test_rollback_functionality_simulation(app, db_session):
    """Test rollback functionality by simulating the exception handling pattern."""
    # Simulate the pattern used in our fixed code
    etiqueta = Etiqueta(nombre="Test Tag", color="#FF0000")
    database.session.add(etiqueta)

    # This simulates the try/except pattern with rollback
    try:
        # Simulate commit failure
        raise OperationalError("Simulated database error", None, None)
    except OperationalError:
        # This is the rollback call we added in our fixes
        database.session.rollback()

    # Verify the session is clean after rollback
    assert len(database.session.new) == 0
    assert len(database.session.dirty) == 0

    # Verify the object was not persisted
    query_result = database.session.query(Etiqueta).filter_by(nombre="Test Tag").first()
    assert query_result is None


def test_successful_commit_after_failed_rollback_scenario(app, db_session):
    """Test that successful operations work after a failed operation with rollback."""
    # First, simulate a failed operation
    failing_tag = Etiqueta(nombre="Failing Tag", color="#FF0000")
    database.session.add(failing_tag)

    try:
        raise OperationalError("Simulated error", None, None)
    except OperationalError:
        database.session.rollback()

    # Now perform a successful operation
    successful_tag = Etiqueta(nombre="Successful Tag", color="#00FF00")
    database.session.add(successful_tag)
    database.session.commit()

    # Verify only the successful tag exists
    all_tags = database.session.query(Etiqueta).all()
    assert len(all_tags) == 1
    assert all_tags[0].nombre == "Successful Tag"


def test_rollback_with_modified_existing_object(app, db_session):
    """Test rollback behavior when modifying an existing database object."""
    # Create and commit an initial object
    tag = Etiqueta(nombre="Original Name", color="#FF0000")
    database.session.add(tag)
    database.session.commit()

    # Store original state
    original_name = tag.nombre
    tag_id = tag.id

    # Modify the object
    tag.nombre = "Modified Name"
    tag.color = "#00FF00"

    # Verify object is marked as dirty
    assert tag in database.session.dirty

    # Simulate commit failure and rollback
    try:
        raise OperationalError("Simulated error", None, None)
    except OperationalError:
        database.session.rollback()

    # After rollback, session should be clean
    assert len(database.session.dirty) == 0

    # Refresh the object from database to verify rollback
    database.session.refresh(tag)
    assert tag.nombre == original_name
    assert tag.color == "#FF0000"
