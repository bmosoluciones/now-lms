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

"""End-to-end tests for calendar functionality."""

from datetime import datetime, date, time as time_obj

from now_lms.auth import proteger_passwd
from now_lms.calendar_utils import create_events_for_student_enrollment
from now_lms.db import (
    Usuario,
    Curso,
    CursoSeccion,
    CursoRecurso,
    Evaluation,
    EstudianteCurso,
    UserEvent,
    database,
    select,
)


class TestCalendarEndToEnd:
    """End-to-end tests for calendar views and functionality."""

    def test_calendar_view_navigation(self, full_db_setup, client):
        """Test calendar view navigation and month switching."""
        app = full_db_setup

        # Create test user and login
        with app.app_context():
            user = Usuario(
                usuario="calendar_test",
                acceso=proteger_passwd("test_pass"),
                nombre="Calendar",
                apellido="Test",
                correo_electronico="calendar@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(user)
            database.session.commit()

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "calendar_test", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test calendar view - current month
        calendar_response = client.get("/user/calendar")
        assert calendar_response.status_code == 200
        assert b"Mi Calendario" in calendar_response.data
        assert b"calendar-table" in calendar_response.data

        # Test navigation to specific month
        calendar_month_response = client.get("/user/calendar?year=2025&month=12")
        assert calendar_month_response.status_code == 200
        assert b"December" in calendar_month_response.data

        # Test navigation to previous year
        calendar_prev_year = client.get("/user/calendar?year=2024&month=1")
        assert calendar_prev_year.status_code == 200

    def test_calendar_with_events(self, full_db_setup, client):
        """Test calendar view with events displayed."""
        app = full_db_setup

        # Create test data
        with app.app_context():
            # Create user
            user = Usuario(
                usuario="event_user",
                acceso=proteger_passwd("test_pass"),
                nombre="Event",
                apellido="User",
                correo_electronico="event@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            # Create course
            course = Curso(
                codigo="EVENT001",
                nombre="Event Test Course",
                descripcion="A course for testing events",
                descripcion_corta="Event test",
                publico=True,
                limitado=False,
                capacidad=0,
                nivel=1,
                duracion=4,
                modalidad="time_based",
                foro_habilitado=True,
                estado="open",
            )

            # Create section
            section = CursoSeccion(
                curso="EVENT001",
                nombre="Section 1",
                descripcion="Test section",
                estado=True,
            )

            database.session.add_all([user, course, section])
            database.session.commit()

            # Create meet resource
            meet_resource = CursoRecurso(
                seccion=section.id,
                curso="EVENT001",
                nombre="Test Meeting",
                descripcion="Test meeting description",
                tipo="meet",
                fecha=date(2025, 8, 15),
                hora_inicio=time_obj(10, 0),
                hora_fin=time_obj(11, 0),
                publico=True,
                indice=1,
            )

            # Create evaluation
            evaluation = Evaluation(
                section_id=section.id,
                title="Test Evaluation",
                description="Test evaluation description",
                is_exam=False,
                passing_score=60.0,
                available_until=datetime(2025, 8, 20, 23, 59, 59),
            )

            database.session.add_all([meet_resource, evaluation])
            database.session.commit()

            # Enroll user in course
            enrollment = EstudianteCurso(
                usuario="event_user",
                curso="EVENT001",
                vigente=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            # Create calendar events
            create_events_for_student_enrollment("event_user", "EVENT001")

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "event_user", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # View calendar for August 2025
        calendar_response = client.get("/user/calendar?year=2025&month=8")
        assert calendar_response.status_code == 200

        # Check that events are displayed
        assert b"Test Meeting" in calendar_response.data
        assert b"Test Evaluation" in calendar_response.data
        assert b"event-meet" in calendar_response.data
        assert b"event-evaluation" in calendar_response.data

    def test_event_detail_view(self, full_db_setup, client):
        """Test event detail view."""
        app = full_db_setup

        # Create test data similar to previous test
        with app.app_context():
            user = Usuario(
                usuario="detail_user",
                acceso=proteger_passwd("test_pass"),
                nombre="Detail",
                apellido="User",
                correo_electronico="detail@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            course = Curso(
                codigo="DETAIL001",
                nombre="Detail Test Course",
                descripcion="A course for testing event details",
                descripcion_corta="Detail test",
                publico=True,
                limitado=False,
                capacidad=0,
                nivel=1,
                duracion=4,
                modalidad="time_based",
                foro_habilitado=True,
                estado="open",
            )

            section = CursoSeccion(
                curso="DETAIL001",
                nombre="Section 1",
                descripcion="Test section",
                estado=True,
            )

            database.session.add_all([user, course, section])
            database.session.commit()

            # Create a meet resource
            meet_resource = CursoRecurso(
                seccion=section.id,
                curso="DETAIL001",
                nombre="Detail Meeting",
                descripcion="Detailed meeting description",
                tipo="meet",
                fecha=date(2025, 9, 10),
                hora_inicio=time_obj(14, 0),
                hora_fin=time_obj(15, 30),
                publico=True,
                indice=1,
            )

            database.session.add(meet_resource)
            database.session.commit()

            # Enroll user and create events
            enrollment = EstudianteCurso(
                usuario="detail_user",
                curso="DETAIL001",
                vigente=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            create_events_for_student_enrollment("detail_user", "DETAIL001")

            # Get the created event
            event = database.session.execute(
                select(UserEvent).filter_by(user_id="detail_user", course_id="DETAIL001")
            ).scalar_one()

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "detail_user", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # View event detail
        detail_response = client.get(f"/user/calendar/event/{event.id}")
        assert detail_response.status_code == 200
        assert b"Detail Meeting" in detail_response.data

        # Test access to non-existent event
        nonexistent_response = client.get("/user/calendar/event/nonexistent-id")
        assert nonexistent_response.status_code == 404

    def test_upcoming_events_view(self, full_db_setup, client):
        """Test upcoming events view."""
        app = full_db_setup

        # Create test data
        with app.app_context():
            user = Usuario(
                usuario="upcoming_user",
                acceso=proteger_passwd("test_pass"),
                nombre="Upcoming",
                apellido="User",
                correo_electronico="upcoming@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            course = Curso(
                codigo="UPCOMING001",
                nombre="Upcoming Test Course",
                descripcion="A course for testing upcoming events",
                descripcion_corta="Upcoming test",
                publico=True,
                limitado=False,
                capacidad=0,
                nivel=1,
                duracion=4,
                modalidad="time_based",
                foro_habilitado=True,
                estado="open",
            )

            section = CursoSeccion(
                curso="UPCOMING001",
                nombre="Section 1",
                descripcion="Test section",
                estado=True,
            )

            database.session.add_all([user, course, section])
            database.session.commit()

            # Create future evaluation
            future_eval = Evaluation(
                section_id=section.id,
                title="Future Evaluation",
                description="An evaluation in the future",
                is_exam=True,
                passing_score=70.0,
                available_until=datetime(2025, 12, 31, 23, 59, 59),
            )

            database.session.add(future_eval)
            database.session.commit()

            # Enroll user and create events
            enrollment = EstudianteCurso(
                usuario="upcoming_user",
                curso="UPCOMING001",
                vigente=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            create_events_for_student_enrollment("upcoming_user", "UPCOMING001")

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "upcoming_user", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # View upcoming events
        upcoming_response = client.get("/user/calendar/upcoming")
        assert upcoming_response.status_code == 200
        assert b"Eventos" in upcoming_response.data

    def test_ics_export(self, full_db_setup, client):
        """Test ICS calendar export functionality."""
        app = full_db_setup

        # Create test data
        with app.app_context():
            user = Usuario(
                usuario="export_user",
                acceso=proteger_passwd("test_pass"),
                nombre="Export",
                apellido="User",
                correo_electronico="export@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            course = Curso(
                codigo="EXPORT001",
                nombre="Export Test Course",
                descripcion="A course for testing ICS export",
                descripcion_corta="Export test",
                publico=True,
                limitado=False,
                capacidad=0,
                nivel=1,
                duracion=4,
                modalidad="time_based",
                foro_habilitado=True,
                estado="open",
            )

            section = CursoSeccion(
                curso="EXPORT001",
                nombre="Section 1",
                descripcion="Test section",
                estado=True,
            )

            database.session.add_all([user, course, section])
            database.session.commit()

            # Create future events
            meet_resource = CursoRecurso(
                seccion=section.id,
                curso="EXPORT001",
                nombre="Export Meeting",
                descripcion="Meeting for export test",
                tipo="meet",
                fecha=date(2025, 11, 15),
                hora_inicio=time_obj(9, 0),
                hora_fin=time_obj(10, 0),
                publico=True,
                indice=1,
            )

            evaluation = Evaluation(
                section_id=section.id,
                title="Export Evaluation",
                description="Evaluation for export test",
                is_exam=False,
                passing_score=60.0,
                available_until=datetime(2025, 11, 20, 23, 59, 59),
            )

            database.session.add_all([meet_resource, evaluation])
            database.session.commit()

            # Enroll user and create events
            enrollment = EstudianteCurso(
                usuario="export_user",
                curso="EXPORT001",
                vigente=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            create_events_for_student_enrollment("export_user", "EXPORT001")

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "export_user", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Export ICS file
        export_response = client.get("/user/calendar/export.ics")
        assert export_response.status_code == 200
        assert "text/calendar" in export_response.headers["Content-Type"]
        assert b"BEGIN:VCALENDAR" in export_response.data
        assert b"END:VCALENDAR" in export_response.data
        assert b"Export Meeting" in export_response.data
        assert b"Export Evaluation" in export_response.data

        # Verify ICS format
        ics_content = export_response.data.decode("utf-8")
        assert "VERSION:2.0" in ics_content
        assert "PRODID:-//NOW LMS//Calendar//EN" in ics_content
        assert "BEGIN:VEVENT" in ics_content
        assert "END:VEVENT" in ics_content

    def test_calendar_edge_cases(self, full_db_setup, client):
        """Test calendar edge cases and error conditions."""
        app = full_db_setup

        # Create minimal user for testing
        with app.app_context():
            user = Usuario(
                usuario="edge_user",
                acceso=proteger_passwd("test_pass"),
                nombre="Edge",
                apellido="User",
                correo_electronico="edge@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(user)
            database.session.commit()

        # Login
        login_response = client.post(
            "/user/login",
            data={"usuario": "edge_user", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test with invalid month parameters (should default to current month)
        invalid_month_response = client.get("/user/calendar?year=2025&month=13")
        assert invalid_month_response.status_code == 200  # Should handle gracefully

        # Test with invalid year parameters (should default to current year)
        invalid_year_response = client.get("/user/calendar?year=-1&month=1")
        assert invalid_year_response.status_code == 200  # Should handle gracefully

        # Test calendar with no events
        empty_calendar_response = client.get("/user/calendar")
        assert empty_calendar_response.status_code == 200
        assert b"calendar-table" in empty_calendar_response.data

        # Test upcoming events with no events
        empty_upcoming_response = client.get("/user/calendar/upcoming")
        assert empty_upcoming_response.status_code == 200

        # Test ICS export with no events
        empty_export_response = client.get("/user/calendar/export.ics")
        assert empty_export_response.status_code == 200
        assert b"BEGIN:VCALENDAR" in empty_export_response.data
        assert b"END:VCALENDAR" in empty_export_response.data

    def test_calendar_access_control(self, full_db_setup, client):
        """Test calendar access control - must be logged in."""
        # Test calendar routes without login
        calendar_response = client.get("/user/calendar")
        assert calendar_response.status_code == 302  # Redirect to login

        upcoming_response = client.get("/user/calendar/upcoming")
        assert upcoming_response.status_code == 302  # Redirect to login

        export_response = client.get("/user/calendar/export.ics")
        assert export_response.status_code == 302  # Redirect to login

        event_response = client.get("/user/calendar/event/test-id")
        assert event_response.status_code == 302  # Redirect to login

    def test_calendar_cross_user_access(self, full_db_setup, client):
        """Test that users cannot access other users' events."""
        app = full_db_setup

        # Create two users
        with app.app_context():
            user1 = Usuario(
                usuario="user_one",
                acceso=proteger_passwd("test_pass"),
                nombre="User",
                apellido="One",
                correo_electronico="user1@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            user2 = Usuario(
                usuario="user_two",
                acceso=proteger_passwd("test_pass"),
                nombre="User",
                apellido="Two",
                correo_electronico="user2@test.com",
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )

            course = Curso(
                codigo="CROSS001",
                nombre="Cross Access Test Course",
                descripcion="A course for testing cross-user access",
                descripcion_corta="Cross test",
                publico=True,
                limitado=False,
                capacidad=0,
                nivel=1,
                duracion=4,
                modalidad="time_based",
                foro_habilitado=True,
                estado="open",
            )

            section = CursoSeccion(
                curso="CROSS001",
                nombre="Section 1",
                descripcion="Test section",
                estado=True,
            )

            database.session.add_all([user1, user2, course, section])
            database.session.commit()

            # Create an event for user1 only
            meet_resource = CursoRecurso(
                seccion=section.id,
                curso="CROSS001",
                nombre="User One Meeting",
                descripcion="Meeting for user one only",
                tipo="meet",
                fecha=date(2025, 10, 10),
                hora_inicio=time_obj(10, 0),
                hora_fin=time_obj(11, 0),
                publico=True,
                indice=1,
            )

            database.session.add(meet_resource)
            database.session.commit()

            # Enroll only user1
            enrollment = EstudianteCurso(
                usuario="user_one",
                curso="CROSS001",
                vigente=True,
            )
            database.session.add(enrollment)
            database.session.commit()

            create_events_for_student_enrollment("user_one", "CROSS001")

            # Get user1's event
            user1_event = database.session.execute(
                select(UserEvent).filter_by(user_id="user_one", course_id="CROSS001")
            ).scalar_one()

        # Login as user2
        login_response = client.post(
            "/user/login",
            data={"usuario": "user_two", "acceso": "test_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Try to access user1's event
        cross_access_response = client.get(f"/user/calendar/event/{user1_event.id}")
        assert cross_access_response.status_code == 404  # Should not be able to access
