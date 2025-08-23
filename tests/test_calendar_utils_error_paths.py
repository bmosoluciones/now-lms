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

"""Additional tests for calendar_utils.py to improve coverage of error paths."""

from unittest.mock import patch, MagicMock
from now_lms.calendar_utils import (
    create_events_for_student_enrollment,
    update_meet_resource_events,
    update_evaluation_events,
    cleanup_events_for_course_unenrollment,
)
from now_lms.db import database, Curso, CursoSeccion, CursoRecurso


class TestCalendarUtilsErrorPaths:
    """Test error handling paths in calendar utils to improve coverage."""

    def test_create_events_error_handling(self, session_basic_db_setup):
        """Test error handling in create_events_for_student_enrollment."""
        app = session_basic_db_setup

        with app.app_context():
            # Mock database session to raise an exception
            with patch("now_lms.calendar_utils.database.session") as mock_session:
                mock_session.execute.side_effect = Exception("Database error")

                # This should trigger the error handling path
                with patch("now_lms.calendar_utils.log") as mock_log:
                    create_events_for_student_enrollment("test_user", "TEST_COURSE")

                    # Verify error was logged and rollback was called
                    mock_log.error.assert_called()
                    mock_session.rollback.assert_called()

    def test_update_meet_resource_events_non_meet_resource(self, full_db_setup):
        """Test update_meet_resource_events with non-meet resource."""
        app = full_db_setup

        with app.app_context():
            # Create a non-meet resource
            curso = Curso(
                codigo="UPDATE_TEST", nombre="Update Test", descripcion_corta="Short", descripcion="Test", estado="Borrador"
            )
            database.session.add(curso)
            database.session.flush()  # Ensure curso is available for foreign key

            seccion = CursoSeccion(
                id="SEC_UPDATE", curso="UPDATE_TEST", nombre="Section", descripcion="A test section", indice=1, estado=True
            )
            database.session.add(seccion)
            database.session.flush()  # Ensure seccion is available for foreign key

            resource = CursoRecurso(
                id="RES_UPDATE",
                seccion="SEC_UPDATE",
                curso="UPDATE_TEST",
                nombre="Video Resource",
                descripcion="A video resource",
                tipo="video",  # Not a "meet" type
                indice=1,
            )
            database.session.add(resource)
            database.session.commit()

            # Test update with non-meet resource (should early return)
            with patch("now_lms.calendar_utils.log") as mock_log:
                update_meet_resource_events("RES_UPDATE")

                # Give the background thread time to execute
                import time

                time.sleep(0.1)

                # Should not log any updates since it's not a meet resource
                # The function should return early

    def test_update_meet_resource_events_nonexistent_resource(self, session_basic_db_setup):
        """Test update_meet_resource_events with nonexistent resource."""
        app = session_basic_db_setup

        with app.app_context():
            # Test with nonexistent resource ID
            with patch("now_lms.calendar_utils.log") as mock_log:
                update_meet_resource_events("NONEXISTENT_RESOURCE")

                # Give the background thread time to execute
                import time

                time.sleep(0.1)

                # Should handle gracefully (early return)

    def test_update_evaluation_events_nonexistent_evaluation(self, session_basic_db_setup):
        """Test update_evaluation_events with nonexistent evaluation."""
        app = session_basic_db_setup

        with app.app_context():
            # Test with nonexistent evaluation ID
            with patch("now_lms.calendar_utils.log") as mock_log:
                update_evaluation_events("NONEXISTENT_EVAL")

                # Give the background thread time to execute
                import time

                time.sleep(0.1)

                # Should handle gracefully (early return)

    def test_remove_events_error_handling(self, session_basic_db_setup):
        """Test error handling in cleanup_events_for_course_unenrollment."""
        app = session_basic_db_setup

        with app.app_context():
            # Mock database session to raise an exception during deletion
            with patch("now_lms.calendar_utils.database.session") as mock_session:
                # Set up mock to fail on the delete operation
                mock_query = MagicMock()
                mock_session.execute.return_value = mock_query
                mock_query.scalars.return_value.all.return_value = []
                mock_session.commit.side_effect = Exception("Delete error")

                # This should trigger the error handling path
                with patch("now_lms.calendar_utils.log") as mock_log:
                    cleanup_events_for_course_unenrollment("test_user", "TEST_COURSE")

                    # Verify error was logged and rollback was called
                    mock_log.error.assert_called()
                    mock_session.rollback.assert_called()

    def test_background_thread_error_handling_meet_update(self, session_basic_db_setup):
        """Test error handling in background thread for meet resource updates."""
        app = session_basic_db_setup

        with app.app_context():
            # Create a meet resource but cause database error during update
            with patch("now_lms.calendar_utils.database.session") as mock_session:
                # Make the query for the resource succeed
                mock_resource = MagicMock()
                mock_resource.tipo = "meet"
                mock_resource.id = "MEET_RES"
                mock_resource.nombre = "Test Meet"
                mock_resource.descripcion = "Test Description"
                mock_resource.fecha = None
                mock_resource.hora_inicio = None
                mock_resource.hora_fin = None

                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_resource
                # But make the events query fail
                mock_session.execute.side_effect = [
                    MagicMock(scalar_one_or_none=lambda: mock_resource),  # First call succeeds
                    Exception("Events query error"),  # Second call fails
                ]

                with patch("now_lms.calendar_utils.log") as mock_log:
                    update_meet_resource_events("MEET_RES")

                    # Give the background thread time to execute
                    import time

                    time.sleep(0.1)

                    # Should log error from background thread

    def test_background_thread_error_handling_evaluation_update(self, session_basic_db_setup):
        """Test error handling in background thread for evaluation updates."""
        app = session_basic_db_setup

        with app.app_context():
            # Create an evaluation but cause database error during update
            with patch("now_lms.calendar_utils.database.session") as mock_session:
                # Make the query for the evaluation succeed
                mock_evaluation = MagicMock()
                mock_evaluation.id = "EVAL_TEST"
                mock_evaluation.title = "Test Evaluation"
                mock_evaluation.description = "Test Description"
                mock_evaluation.available_until = None

                mock_session.execute.return_value.scalar_one_or_none.return_value = mock_evaluation
                # But make the events query fail
                mock_session.execute.side_effect = [
                    MagicMock(scalar_one_or_none=lambda: mock_evaluation),  # First call succeeds
                    Exception("Events query error"),  # Second call fails
                ]

                with patch("now_lms.calendar_utils.log") as mock_log:
                    update_evaluation_events("EVAL_TEST")

                    # Give the background thread time to execute
                    import time

                    time.sleep(0.1)

                    # Should log error from background thread
