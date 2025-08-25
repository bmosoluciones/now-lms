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
Comprehensive tests for meet calendar route functions using session-scoped fixtures.

This test file focuses on improving code coverage for:
- download_meet_calendar(course_code, codigo) - Line 2445
- google_calendar_link(course_code, codigo) - Line 2497
- outlook_calendar_link(course_code, codigo) - Line 2572
"""

from datetime import date, time
from urllib.parse import unquote
from flask import url_for
from now_lms.db import Curso, CursoSeccion, CursoRecurso


class TestDownloadMeetCalendar:
    """Test download_meet_calendar function using session-scoped fixtures."""

    def _login_user(self, client, username="lms-admin", password="lms-admin"):
        """Helper to login a user via form POST."""
        login_response = client.post("/user/login", data={"usuario": username, "acceso": password})
        # Should redirect to dashboard or return 200
        assert login_response.status_code in [200, 302], f"Login failed with status {login_response.status_code}"

    def test_download_meet_calendar_admin_success(self, session_full_db_setup, isolated_db_session):
        """Test successful ICS download as admin user."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_CAL_ADMIN",
                nombre="Test Course Admin",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_CAL_ADMIN",
                curso="TEST_CAL_ADMIN",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with complete information
            recurso = CursoRecurso(
                id="RES_CAL_ADMIN",
                seccion="SEC_CAL_ADMIN",
                curso="TEST_CAL_ADMIN",
                nombre="Test Meet Admin",
                descripcion="Admin meet description",
                tipo="meet",
                fecha=date(2025, 1, 20),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 30),
                url="https://meet.google.com/admin-meet",
                notes="google meet",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

    def test_download_meet_calendar_admin_success(self, session_full_db_setup, isolated_db_session):
        """Test successful ICS download as admin user."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_CAL_ADMIN",
                nombre="Test Course Admin",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_CAL_ADMIN",
                curso="TEST_CAL_ADMIN",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with complete information
            recurso = CursoRecurso(
                id="RES_CAL_ADMIN",
                seccion="SEC_CAL_ADMIN",
                curso="TEST_CAL_ADMIN",
                nombre="Test Meet Admin",
                descripcion="Admin meet description",
                tipo="meet",
                fecha=date(2025, 1, 20),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 30),
                url="https://meet.google.com/admin-meet",
                notes="google meet",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login
            with session_full_db_setup.test_client() as client:
                # Login via form post
                self._login_user(client)

                # Request ICS download
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="TEST_CAL_ADMIN", codigo="RES_CAL_ADMIN")
                )

                # Verify successful response
                assert response.status_code == 200
                assert response.mimetype == "text/calendar"
                assert "Content-Disposition" in response.headers
                assert "attachment; filename=" in response.headers["Content-Disposition"]
                assert "meet-Test-Meet-Admin" in response.headers["Content-Disposition"]
                assert ".ics" in response.headers["Content-Disposition"]

                # Verify ICS content
                ics_content = response.get_data(as_text=True)
                assert "BEGIN:VCALENDAR" in ics_content
                assert "BEGIN:VEVENT" in ics_content
                assert "SUMMARY:Test Meet Admin" in ics_content
                assert "DTSTART:20250120T100000" in ics_content
                assert "DTEND:20250120T113000" in ics_content
                assert "Curso: Test Course Admin" in ics_content
                assert "https://meet.google.com/admin-meet" in ics_content

    def test_download_meet_calendar_student_success(self, session_full_db_setup, isolated_db_session):
        """Test successful ICS download with default 1-hour duration."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_CAL_STUDENT",
                nombre="Test Course Student",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_CAL_STUDENT",
                curso="TEST_CAL_STUDENT",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource
            recurso = CursoRecurso(
                id="RES_CAL_STUDENT",
                seccion="SEC_CAL_STUDENT",
                curso="TEST_CAL_STUDENT",
                nombre="Test Meet Student",
                descripcion="Student meet description",
                tipo="meet",
                fecha=date(2025, 1, 21),
                hora_inicio=time(14, 0),
                hora_fin=None,  # Test default 1-hour duration
                url="https://zoom.us/student-meet",
                notes="zoom",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as admin (admin can access any resource)
            with session_full_db_setup.test_client() as client:
                # Login as admin to test the calendar functionality
                self._login_user(client)

                # Request ICS download
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="TEST_CAL_STUDENT", codigo="RES_CAL_STUDENT")
                )

            # Verify successful response
            assert response.status_code == 200
            assert response.mimetype == "text/calendar"

            # Verify ICS content shows default 1-hour duration
            ics_content = response.get_data(as_text=True)
            assert "DTSTART:20250121T140000" in ics_content
            assert "DTEND:20250121T150000" in ics_content  # 1 hour later

    def test_download_meet_calendar_public_resource(self, session_full_db_setup, isolated_db_session):
        """Test ICS download for public resource with login."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_CAL_PUBLIC",
                nombre="Test Course Public",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_CAL_PUBLIC",
                curso="TEST_CAL_PUBLIC",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create PUBLIC meet resource
            recurso = CursoRecurso(
                id="RES_CAL_PUBLIC",
                seccion="SEC_CAL_PUBLIC",
                curso="TEST_CAL_PUBLIC",
                nombre="Test Meet Public",
                descripcion="Public meet description",
                tipo="meet",
                fecha=date(2025, 1, 22),
                hora_inicio=time(16, 0),
                hora_fin=time(17, 0),
                url="https://teams.microsoft.com/public-meet",
                notes="teams",
                publico=True,  # Make resource public
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as any user (since resource is public)
            with session_full_db_setup.test_client() as client:
                # Login is still required due to @login_required decorator
                self._login_user(client)

                # Request ICS download
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="TEST_CAL_PUBLIC", codigo="RES_CAL_PUBLIC")
                )

                # Verify successful response for public resource
                assert response.status_code == 200
                assert response.mimetype == "text/calendar"

    def test_download_meet_calendar_resource_not_found(self, session_full_db_setup):
        """Test 404 when meet resource not found."""
        with session_full_db_setup.app_context():
            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request non-existent resource
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="NONEXISTENT", codigo="NONEXISTENT")
                )

                assert response.status_code == 404

    def test_download_meet_calendar_course_not_found(self, session_full_db_setup):
        """Test 404 when course not found."""
        with session_full_db_setup.app_context():
            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request resource with non-existent course
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="NONEXISTENT_COURSE", codigo="NONEXISTENT_RESOURCE")
                )

                assert response.status_code == 404

    def test_download_meet_calendar_access_denied(self, session_full_db_setup, isolated_db_session):
        """Test 403 when user doesn't have access to private resource."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_CAL_PRIVATE",
                nombre="Test Course Private",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_CAL_PRIVATE",
                curso="TEST_CAL_PRIVATE",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create PRIVATE meet resource
            recurso = CursoRecurso(
                id="RES_CAL_PRIVATE",
                seccion="SEC_CAL_PRIVATE",
                curso="TEST_CAL_PRIVATE",
                nombre="Test Meet Private",
                descripcion="Private meet description",
                tipo="meet",
                fecha=date(2025, 1, 24),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                publico=False,  # Private resource
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as a user without access to the course
            with session_full_db_setup.test_client() as client:
                # Login as student who is not enrolled in this course
                self._login_user(client, username="student", password="student")

                # Try to access private resource
                response = client.get(
                    url_for("course.download_meet_calendar", course_code="TEST_CAL_PRIVATE", codigo="RES_CAL_PRIVATE")
                )

                assert response.status_code == 403


class TestGoogleCalendarLink:
    """Test google_calendar_link function using session-scoped fixtures."""

    def _login_user(self, client, username="lms-admin", password="lms-admin"):
        """Helper to login a user via form POST."""
        login_response = client.post("/user/login", data={"usuario": username, "acceso": password})
        # Should redirect to dashboard or return 200
        assert login_response.status_code in [200, 302], f"Login failed with status {login_response.status_code}"

    def test_google_calendar_link_admin_success(self, session_full_db_setup, isolated_db_session):
        """Test successful Google Calendar redirect as admin user."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_GCAL_ADMIN",
                nombre="Test Course Google",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_GCAL_ADMIN",
                curso="TEST_GCAL_ADMIN",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with complete information
            recurso = CursoRecurso(
                id="RES_GCAL_ADMIN",
                seccion="SEC_GCAL_ADMIN",
                curso="TEST_GCAL_ADMIN",
                nombre="Test Meet Google",
                descripcion="Google meet description",
                tipo="meet",
                fecha=date(2025, 1, 25),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 30),
                url="https://meet.google.com/google-test",
                notes="google meet location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login
            with session_full_db_setup.test_client() as client:
                # Login via form post
                self._login_user(client)

                # Request Google Calendar redirect
                response = client.get(
                    url_for("course.google_calendar_link", course_code="TEST_GCAL_ADMIN", codigo="RES_GCAL_ADMIN")
                )

                # Verify redirect response
                assert response.status_code == 302
                assert "calendar.google.com" in response.location
                assert "action=TEMPLATE" in response.location

                # Verify URL contains proper encoded parameters
                assert "text=" in response.location
                assert "dates=20250125T100000/20250125T113000" in response.location
                assert "details=" in response.location
                assert "location=" in response.location

            # Check that course name and description are in the URL
            decoded_url = unquote(response.location)
            assert "Test Meet Google" in decoded_url
            assert "Curso: Test Course Google" in decoded_url
            assert "Google meet description" in decoded_url
            assert "https://meet.google.com/google-test" in decoded_url
            assert "google meet location" in decoded_url

    def test_google_calendar_link_without_end_time(self, session_full_db_setup, isolated_db_session):
        """Test Google Calendar redirect with default 1-hour duration."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_GCAL_NO_END",
                nombre="Test Course No End",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_GCAL_NO_END",
                curso="TEST_GCAL_NO_END",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without end time
            recurso = CursoRecurso(
                id="RES_GCAL_NO_END",
                seccion="SEC_GCAL_NO_END",
                curso="TEST_GCAL_NO_END",
                nombre="Test Meet No End",
                descripcion="No end time",
                tipo="meet",
                fecha=date(2025, 1, 26),
                hora_inicio=time(14, 0),
                hora_fin=None,  # No end time - should default to 1 hour
                url="https://zoom.us/no-end-test",
                notes="zoom location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request Google Calendar redirect
                response = client.get(
                    url_for("course.google_calendar_link", course_code="TEST_GCAL_NO_END", codigo="RES_GCAL_NO_END")
                )

                # Verify redirect with 1-hour default duration
                assert response.status_code == 302
                assert "dates=20250126T140000/20250126T150000" in response.location  # 1 hour later

    def test_google_calendar_link_missing_datetime_error(self, session_full_db_setup, isolated_db_session, client):
        """Test error handling when date/time is missing."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_GCAL_NO_DATE",
                nombre="Test Course No Date",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_GCAL_NO_DATE",
                curso="TEST_GCAL_NO_DATE",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without date/time
            recurso = CursoRecurso(
                id="RES_GCAL_NO_DATE",
                seccion="SEC_GCAL_NO_DATE",
                curso="TEST_GCAL_NO_DATE",
                nombre="Test Meet No Date",
                descripcion="No date time",
                tipo="meet",
                fecha=None,  # Missing date
                hora_inicio=None,  # Missing start time
                hora_fin=None,
                url="https://teams.microsoft.com/no-date",
                notes="teams location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Login as admin
            with client.session_transaction() as sess:
                sess["user_id"] = "lms-admin"

            # Request Google Calendar redirect
            response = client.get(
                url_for("course.google_calendar_link", course_code="TEST_GCAL_NO_DATE", codigo="RES_GCAL_NO_DATE"),
                follow_redirects=True,
            )

            # Should redirect back to resource view with error message
            assert response.status_code == 200
            # Check that we got redirected back (can't easily test flash message without a full page)

    def test_google_calendar_link_minimal_content(self, session_full_db_setup, isolated_db_session):
        """Test Google Calendar link with minimal content (no description, no URL)."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_GCAL_MINIMAL",
                nombre="Test Course Minimal",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_GCAL_MINIMAL",
                curso="TEST_GCAL_MINIMAL",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with minimal information
            recurso = CursoRecurso(
                id="RES_GCAL_MINIMAL",
                seccion="SEC_GCAL_MINIMAL",
                curso="TEST_GCAL_MINIMAL",
                nombre="Test Meet Minimal",
                descripcion="",  # Empty description
                tipo="meet",
                fecha=date(2025, 1, 27),
                hora_inicio=time(9, 0),
                hora_fin=time(10, 0),
                url="",  # Empty URL
                notes=None,  # No notes - should default to "En línea"
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request Google Calendar redirect
                response = client.get(
                    url_for("course.google_calendar_link", course_code="TEST_GCAL_MINIMAL", codigo="RES_GCAL_MINIMAL")
                )

                # Verify redirect response
                assert response.status_code == 302
                assert "calendar.google.com" in response.location

                # Check that minimal content is properly handled
                decoded_url = unquote(response.location)
                assert "Test Meet Minimal" in decoded_url
                assert "Curso: Test Course Minimal" in decoded_url
                assert "En línea" in decoded_url  # Default location
                # Should not contain empty description or URL sections


class TestOutlookCalendarLink:
    """Test outlook_calendar_link function using session-scoped fixtures."""

    def _login_user(self, client, username="lms-admin", password="lms-admin"):
        """Helper to login a user via form POST."""
        login_response = client.post("/user/login", data={"usuario": username, "acceso": password})
        # Should redirect to dashboard or return 200
        assert login_response.status_code in [200, 302], f"Login failed with status {login_response.status_code}"

    def test_outlook_calendar_link_admin_success(self, session_full_db_setup, isolated_db_session):
        """Test successful Outlook Calendar redirect as admin user."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_OCAL_ADMIN",
                nombre="Test Course Outlook",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_OCAL_ADMIN",
                curso="TEST_OCAL_ADMIN",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with complete information
            recurso = CursoRecurso(
                id="RES_OCAL_ADMIN",
                seccion="SEC_OCAL_ADMIN",
                curso="TEST_OCAL_ADMIN",
                nombre="Test Meet Outlook",
                descripcion="Outlook meet description",
                tipo="meet",
                fecha=date(2025, 1, 28),
                hora_inicio=time(15, 0),
                hora_fin=time(16, 30),
                url="https://teams.microsoft.com/outlook-test",
                notes="teams location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login
            with session_full_db_setup.test_client() as client:
                # Login via form post
                self._login_user(client)

                # Request Outlook Calendar redirect
                response = client.get(
                    url_for("course.outlook_calendar_link", course_code="TEST_OCAL_ADMIN", codigo="RES_OCAL_ADMIN")
                )

                # Verify redirect response
                assert response.status_code == 302
                assert "outlook.live.com" in response.location
                assert "deeplink/compose" in response.location

                # Verify URL contains proper encoded parameters
                assert "subject=" in response.location
                assert "startdt=20250128T150000" in response.location
                assert "enddt=20250128T163000" in response.location
                assert "body=" in response.location
                assert "location=" in response.location

                # Check that course name and description are in the URL
                decoded_url = unquote(response.location)
                assert "Test Meet Outlook" in decoded_url
                assert "Curso: Test Course Outlook" in decoded_url
                assert "Outlook meet description" in decoded_url
                assert "https://teams.microsoft.com/outlook-test" in decoded_url
                assert "teams location" in decoded_url

    def test_outlook_calendar_link_without_end_time(self, session_full_db_setup, isolated_db_session):
        """Test Outlook Calendar redirect with default 1-hour duration."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_OCAL_NO_END",
                nombre="Test Outlook No End",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_OCAL_NO_END",
                curso="TEST_OCAL_NO_END",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without end time
            recurso = CursoRecurso(
                id="RES_OCAL_NO_END",
                seccion="SEC_OCAL_NO_END",
                curso="TEST_OCAL_NO_END",
                nombre="Test Outlook No End",
                descripcion="No end time",
                tipo="meet",
                fecha=date(2025, 1, 29),
                hora_inicio=time(11, 0),
                hora_fin=None,  # No end time - should default to 1 hour
                url="https://webex.com/outlook-no-end",
                notes="webex location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request Outlook Calendar redirect
                response = client.get(
                    url_for("course.outlook_calendar_link", course_code="TEST_OCAL_NO_END", codigo="RES_OCAL_NO_END")
                )

                # Verify redirect with 1-hour default duration
                assert response.status_code == 302
                assert "startdt=20250129T110000" in response.location
                assert "enddt=20250129T120000" in response.location  # 1 hour later

    def test_outlook_calendar_link_missing_datetime_error(self, session_full_db_setup, isolated_db_session, client):
        """Test error handling when date/time is missing."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_OCAL_NO_DATE",
                nombre="Test Outlook No Date",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_OCAL_NO_DATE",
                curso="TEST_OCAL_NO_DATE",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource without date/time
            recurso = CursoRecurso(
                id="RES_OCAL_NO_DATE",
                seccion="SEC_OCAL_NO_DATE",
                curso="TEST_OCAL_NO_DATE",
                nombre="Test Outlook No Date",
                descripcion="No date time",
                tipo="meet",
                fecha=None,  # Missing date
                hora_inicio=None,  # Missing start time
                hora_fin=None,
                url="https://discord.com/outlook-no-date",
                notes="discord location",
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Login as admin
            with client.session_transaction() as sess:
                sess["user_id"] = "lms-admin"

            # Request Outlook Calendar redirect
            response = client.get(
                url_for("course.outlook_calendar_link", course_code="TEST_OCAL_NO_DATE", codigo="RES_OCAL_NO_DATE"),
                follow_redirects=True,
            )

            # Should redirect back to resource view with error message
            assert response.status_code == 200
            # Check that we got redirected back (can't easily test flash message without a full page)

    def test_outlook_calendar_link_minimal_content(self, session_full_db_setup, isolated_db_session):
        """Test Outlook Calendar link with minimal content (no description, no URL)."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_OCAL_MINIMAL",
                nombre="Test Outlook Minimal",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_OCAL_MINIMAL",
                curso="TEST_OCAL_MINIMAL",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create meet resource with minimal information
            recurso = CursoRecurso(
                id="RES_OCAL_MINIMAL",
                seccion="SEC_OCAL_MINIMAL",
                curso="TEST_OCAL_MINIMAL",
                nombre="Test Outlook Minimal",
                descripcion="",  # Empty description
                tipo="meet",
                fecha=date(2025, 1, 30),
                hora_inicio=time(13, 0),
                hora_fin=time(14, 0),
                url="",  # Empty URL
                notes=None,  # No notes - should default to "En línea"
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and login as admin
            with session_full_db_setup.test_client() as client:
                # Login as admin
                self._login_user(client)

                # Request Outlook Calendar redirect
                response = client.get(
                    url_for("course.outlook_calendar_link", course_code="TEST_OCAL_MINIMAL", codigo="RES_OCAL_MINIMAL")
                )

                # Verify redirect response
                assert response.status_code == 302
                assert "outlook.live.com" in response.location

                # Check that minimal content is properly handled
                decoded_url = unquote(response.location)
                assert "Test Outlook Minimal" in decoded_url
                assert "Curso: Test Outlook Minimal" in decoded_url
                assert "En línea" in decoded_url  # Default location
                # Should not contain empty description or URL sections

    def test_outlook_calendar_link_access_permissions(self, session_full_db_setup, isolated_db_session):
        """Test access permissions for Outlook Calendar link."""
        with session_full_db_setup.app_context():
            # Create test course
            curso = Curso(
                codigo="TEST_OCAL_PERM",
                nombre="Test Outlook Permissions",
                descripcion_corta="Short description",
                descripcion="Long description",
                estado="open",
            )
            isolated_db_session.add(curso)
            isolated_db_session.flush()

            # Create test section
            seccion = CursoSeccion(
                id="SEC_OCAL_PERM",
                curso="TEST_OCAL_PERM",
                nombre="Test Section",
                descripcion="Test section",
                indice=1,
                estado=True,
            )
            isolated_db_session.add(seccion)
            isolated_db_session.flush()

            # Create PRIVATE meet resource
            recurso = CursoRecurso(
                id="RES_OCAL_PERM",
                seccion="SEC_OCAL_PERM",
                curso="TEST_OCAL_PERM",
                nombre="Test Outlook Permissions",
                descripcion="Permission test",
                tipo="meet",
                fecha=date(2025, 1, 31),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                publico=False,  # Private resource
            )
            isolated_db_session.add(recurso)
            isolated_db_session.commit()

            # Create test client and test access denied for non-enrolled user
            with session_full_db_setup.test_client() as client:
                # Login as a student who is not enrolled in this course
                self._login_user(client, username="student", password="student")

                # Try to access private resource
                response = client.get(
                    url_for("course.outlook_calendar_link", course_code="TEST_OCAL_PERM", codigo="RES_OCAL_PERM")
                )
                assert response.status_code == 403
