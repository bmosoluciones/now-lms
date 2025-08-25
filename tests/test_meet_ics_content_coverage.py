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

"""
Comprehensive tests for _generate_meet_ics_content function using session-scoped fixtures.

This test file focuses on improving code coverage for:
- _generate_meet_ics_content function
- _escape_ics_text function
"""

from datetime import date, time
from now_lms.db import Curso, CursoSeccion, CursoRecurso
from now_lms.vistas.courses import _generate_meet_ics_content, _escape_ics_text


class TestMeetIcsContentGeneration:
    """Test ICS content generation for meet resources using session-scoped fixtures."""

    def test_generate_meet_ics_content_normal_case(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation with complete date/time information."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS",
                nombre="Test Course for ICS",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS",
                curso="TEST_ICS",
                nombre="Test Section",
                descripcion="Test section for ICS",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with complete information
            recurso = CursoRecurso(
                id="RES_ICS_COMPLETE",
                seccion="SEC_ICS",
                curso="TEST_ICS",
                nombre="Test Meet Resource",
                descripcion="Test meet description",
                tipo="meet",
                fecha=date(2025, 1, 15),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 30),
                url="https://meet.google.com/test-meet",
                notes="meet",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify ICS content structure
            assert "BEGIN:VCALENDAR" in ics_content
            assert "VERSION:2.0" in ics_content
            assert "PRODID:-//NOW LMS//Meet Calendar//EN" in ics_content
            assert "BEGIN:VEVENT" in ics_content
            assert "END:VEVENT" in ics_content
            assert "END:VCALENDAR" in ics_content

            # Verify event details
            assert f"UID:{recurso.id}@nowlms.local" in ics_content
            assert "DTSTART:20250115T100000" in ics_content
            assert "DTEND:20250115T113000" in ics_content
            assert "SUMMARY:Test Meet Resource" in ics_content
            assert "LOCATION:meet" in ics_content
            assert "STATUS:CONFIRMED" in ics_content

            # Verify description contains course info and URL
            assert "Curso: Test Course for ICS" in ics_content
            assert "Test meet description" in ics_content
            assert "Enlace: https://meet.google.com/test-meet" in ics_content

    def test_generate_meet_ics_content_without_end_time(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation without end time (should default to 1 hour)."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS_NO_END",
                nombre="Test Course No End",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS_NO_END",
                curso="TEST_ICS_NO_END",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without end time
            recurso = CursoRecurso(
                id="RES_ICS_NO_END",
                seccion="SEC_ICS_NO_END",
                curso="TEST_ICS_NO_END",
                nombre="Test Meet No End",
                descripcion="Test meet description",
                tipo="meet",
                fecha=date(2025, 1, 15),
                hora_inicio=time(14, 0),
                hora_fin=None,  # No end time
                url="https://zoom.us/test-meet",
                notes="zoom",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify start time and default 1-hour duration
            assert "DTSTART:20250115T140000" in ics_content
            assert "DTEND:20250115T150000" in ics_content  # 1 hour later

    def test_generate_meet_ics_content_fallback_case(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation fallback when date/time is missing."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS_FALLBACK",
                nombre="Test Course Fallback",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS_FALLBACK",
                curso="TEST_ICS_FALLBACK",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without date/time
            recurso = CursoRecurso(
                id="RES_ICS_FALLBACK",
                seccion="SEC_ICS_FALLBACK",
                curso="TEST_ICS_FALLBACK",
                nombre="Test Meet Fallback",
                descripcion="Test meet description",
                tipo="meet",
                fecha=None,  # Missing date
                hora_inicio=None,  # Missing start time
                hora_fin=None,
                url="https://teams.microsoft.com/test-meet",
                notes="teams",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify fallback content
            expected_fallback = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
            assert ics_content == expected_fallback

    def test_generate_meet_ics_content_without_description(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation without resource description."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS_NO_DESC",
                nombre="Test Course No Desc",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS_NO_DESC",
                curso="TEST_ICS_NO_DESC",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without description but with URL
            recurso = CursoRecurso(
                id="RES_ICS_NO_DESC",
                seccion="SEC_ICS_NO_DESC",
                curso="TEST_ICS_NO_DESC",
                nombre="Test Meet No Desc",
                descripcion="",  # Empty description
                tipo="meet",
                fecha=date(2025, 1, 15),
                hora_inicio=time(9, 0),
                hora_fin=time(10, 0),
                url="https://webex.com/test-meet",
                notes="webex",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify description only contains course name and URL (no resource description)
            assert "Curso: Test Course No Desc" in ics_content
            assert "Enlace: https://webex.com/test-meet" in ics_content
            # Should not contain additional resource description since it's empty
            lines = ics_content.split("\r\n")
            description_line = next(line for line in lines if line.startswith("DESCRIPTION:"))
            # Description should contain course name and URL but not empty resource description
            assert "Curso: Test Course No Desc" in description_line
            assert "https://webex.com/test-meet" in description_line

    def test_generate_meet_ics_content_without_url(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation without URL."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS_NO_URL",
                nombre="Test Course No URL",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS_NO_URL",
                curso="TEST_ICS_NO_URL",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without URL but with description
            recurso = CursoRecurso(
                id="RES_ICS_NO_URL",
                seccion="SEC_ICS_NO_URL",
                curso="TEST_ICS_NO_URL",
                nombre="Test Meet No URL",
                descripcion="Test meet description only",
                tipo="meet",
                fecha=date(2025, 1, 15),
                hora_inicio=time(16, 0),
                hora_fin=time(17, 0),
                url="",  # Empty URL instead of None
                notes="otros",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify description contains course name and resource description (no URL)
            assert "Curso: Test Course No URL" in ics_content
            assert "Test meet description only" in ics_content
            # Should not contain URL section since it's empty
            lines = ics_content.split("\r\n")
            description_line = next(line for line in lines if line.startswith("DESCRIPTION:"))
            assert "Enlace:" not in description_line

    def test_generate_meet_ics_content_minimal_case(self, session_basic_db_setup, isolated_db_session):
        """Test ICS generation with minimal information (no description, no URL)."""
        with session_basic_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_ICS_MINIMAL",
                nombre="Test Course Minimal",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_ICS_MINIMAL",
                curso="TEST_ICS_MINIMAL",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with minimal information
            recurso = CursoRecurso(
                id="RES_ICS_MINIMAL",
                seccion="SEC_ICS_MINIMAL",
                curso="TEST_ICS_MINIMAL",
                nombre="Test Meet Minimal",
                descripcion="",  # Empty description
                tipo="meet",
                fecha=date(2025, 1, 15),
                hora_inicio=time(8, 0),
                hora_fin=time(9, 0),
                url="",  # Empty URL
                notes="",  # Empty notes (should default to "En línea")
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Generate ICS content
            ics_content = _generate_meet_ics_content(recurso, curso)

            # Verify description contains only course name
            assert "Curso: Test Course Minimal" in ics_content
            assert "LOCATION:En línea" in ics_content  # Default location
            # Should not contain description or URL sections
            lines = ics_content.split("\r\n")
            description_line = next(line for line in lines if line.startswith("DESCRIPTION:"))
            # Description should only contain course name
            assert description_line == "DESCRIPTION:Curso: Test Course Minimal"


class TestEscapeIcsText:
    """Test ICS text escaping function."""

    def test_escape_ics_text_empty_input(self):
        """Test escaping with empty/None input."""
        assert _escape_ics_text(None) == ""
        assert _escape_ics_text("") == ""

    def test_escape_ics_text_no_special_chars(self):
        """Test escaping with text that has no special characters."""
        text = "Simple text without special chars"
        assert _escape_ics_text(text) == text

    def test_escape_ics_text_backslash(self):
        """Test escaping backslashes."""
        text = "Text with \\ backslash"
        expected = "Text with \\\\ backslash"
        assert _escape_ics_text(text) == expected

    def test_escape_ics_text_comma(self):
        """Test escaping commas."""
        text = "Text with, commas, here"
        expected = "Text with\\, commas\\, here"
        assert _escape_ics_text(text) == expected

    def test_escape_ics_text_semicolon(self):
        """Test escaping semicolons."""
        text = "Text with; semicolons; here"
        expected = "Text with\\; semicolons\\; here"
        assert _escape_ics_text(text) == expected

    def test_escape_ics_text_newline(self):
        """Test escaping newlines."""
        text = "Text with\nnewlines\nhere"
        expected = "Text with\\nnewlines\\nhere"
        assert _escape_ics_text(text) == expected

    def test_escape_ics_text_multiple_special_chars(self):
        """Test escaping text with multiple special characters."""
        text = "Complex; text\nwith, multiple\\ special chars"
        expected = "Complex\\; text\\nwith\\, multiple\\\\ special chars"
        assert _escape_ics_text(text) == expected

    def test_escape_ics_text_repeated_backslashes(self):
        """Test escaping with repeated backslashes."""
        text = "Text with \\\\ double backslash"
        expected = "Text with \\\\\\\\ double backslash"
        assert _escape_ics_text(text) == expected
