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

"""Additional tests for settings and programs views as requested in issue #249."""

import time

import pytest

from now_lms.auth import proteger_passwd
from now_lms.db import AdSense, Programa, Usuario, database


class TestSettingsAdditionalPOST:
    """Additional POST tests for settings views, particularly AdSense configuration."""

    @staticmethod
    def _unique_suffix():
        """Generate unique suffix to avoid test conflicts."""
        return int(time.time() * 1000) % 1000000

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    def test_adsense_post_successful_update(self, session_full_db_setup, test_client):
        """Test POST request to /setting/adsense successfully updates AdSense configuration (lines 328-340)."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"adsense_admin_{suffix}"
        admin_email = f"adsense_admin_{suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="AdSense",
                apellido="Admin",
                correo_electronico=admin_email,
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(admin_user)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request to update AdSense configuration (covering lines 328-340)
        adsense_data = {
            "meta_tag": "google-site-verification-test",
            "meta_tag_include": True,
            "pub_id": "1234567890123456",
            "add_code": "test-add-code",
            "show_ads": True,
            "add_leaderboard": "leaderboard-test-code",
            "add_medium_rectangle": "medium-rectangle-test-code",
            "add_large_rectangle": "large-rectangle-test-code",
            "add_mobile_banner": "mobile-banner-test-code",
            "add_wide_skyscraper": "wide-skyscraper-test-code",
            "add_skyscraper": "skyscraper-test-code",
            "add_large_skyscraper": "large-skyscraper-test-code",
            "add_billboard": "billboard-test-code",
        }

        # POST to AdSense settings
        response = test_client.post("/setting/adsense", data=adsense_data, follow_redirects=True)
        assert response.status_code == 200

        # Verify configuration was updated in database (testing the actual updates from lines 328-340)
        with session_full_db_setup.app_context():
            adsense_config = database.session.execute(database.select(AdSense)).first()
            if adsense_config:
                config = adsense_config[0]
                # Verify each field that gets updated in lines 328-340
                assert config.meta_tag == "google-site-verification-test"  # Line 328
                assert config.meta_tag_include is True  # Line 329
                assert config.pub_id == "1234567890123456"  # Line 330
                assert config.add_code == "test-add-code"  # Line 331
                assert config.show_ads is True  # Line 332
                assert config.add_leaderboard == "leaderboard-test-code"  # Line 333
                assert config.add_medium_rectangle == "medium-rectangle-test-code"  # Line 334
                assert config.add_large_rectangle == "large-rectangle-test-code"  # Line 335
                assert config.add_mobile_banner == "mobile-banner-test-code"  # Line 336
                assert config.add_wide_skyscraper == "wide-skyscraper-test-code"  # Line 337
                assert config.add_skyscraper == "skyscraper-test-code"  # Line 338
                assert config.add_large_skyscraper == "large-skyscraper-test-code"  # Line 339
                assert config.add_billboard == "billboard-test-code"  # Line 340

    def test_adsense_post_form_validation_end_to_end(self, session_full_db_setup, test_client):
        """Test end-to-end POST form validation and submission for AdSense configuration."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"adsense_e2e_admin_{suffix}"
        admin_email = f"adsense_e2e_admin_{suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="AdSense",
                apellido="E2EAdmin",
                correo_electronico=admin_email,
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(admin_user)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # First, test form submission with all fields as admin (end-to-end test)
        comprehensive_adsense_data = {
            "meta_tag": "<meta name='google-site-verification' content='test-verification' />",
            "meta_tag_include": "y",  # WTForms BooleanField sends 'y' when True
            "pub_id": "1234567890123456",
            "add_code": "<script>test general ad code</script>",
            "show_ads": "y",  # WTForms BooleanField sends 'y' when True
            "add_leaderboard": "<script>test leaderboard 728x90</script>",
            "add_medium_rectangle": "<script>test medium rectangle 300x250</script>",
            "add_large_rectangle": "<script>test large rectangle 336x280</script>",
            "add_mobile_banner": "<script>test mobile banner 300x50</script>",
            "add_wide_skyscraper": "<script>test wide skyscraper 160x600</script>",
            "add_skyscraper": "<script>test skyscraper 120x600</script>",
            "add_large_skyscraper": "<script>test large skyscraper 300x600</script>",
            "add_billboard": "<script>test billboard 970x250</script>",
        }

        # POST to AdSense settings
        response = test_client.post("/setting/adsense", data=comprehensive_adsense_data, follow_redirects=True)
        assert response.status_code == 200

        # Check for success message in response (indicates successful form processing)
        assert b"success" in response.data.lower() or b"actualizada" in response.data.lower()

    def test_adsense_post_get_request(self, session_full_db_setup, test_client):
        """Test GET request to /setting/adsense returns form with current configuration."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"adsense_get_admin_{suffix}"
        admin_email = f"adsense_get_admin_{suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="AdSense",
                apellido="GetAdmin",
                correo_electronico=admin_email,
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(admin_user)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request to AdSense settings
        response = test_client.get("/setting/adsense")
        assert response.status_code == 200
        assert b"adsense" in response.data.lower() or b"google" in response.data.lower()

    def test_adsense_post_non_admin_access_denied(self, session_full_db_setup, test_client):
        """Test POST request to /setting/adsense denies access to non-admin users."""
        # Create non-admin user
        suffix = self._unique_suffix()
        student_username = f"adsense_student_{suffix}"
        student_email = f"adsense_student_{suffix}@nowlms.com"

        with session_full_db_setup.app_context():
            student_user = Usuario(
                usuario=student_username,
                acceso=proteger_passwd("student_pass"),
                nombre="AdSense",
                apellido="Student",
                correo_electronico=student_email,
                tipo="student",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(student_user)
            database.session.commit()

        # Login as student
        login_response = test_client.post(
            "/user/login",
            data={"usuario": student_username, "acceso": "student_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request should be denied (403 or redirect)
        response = test_client.post("/setting/adsense", data={"show_ads": True})
        # Should be denied access (403) or redirected
        assert response.status_code in [403, 302]


class TestProgramsAdditionalPOST:
    """Additional POST tests for programs views."""

    @staticmethod
    def _unique_suffix():
        """Generate unique suffix to avoid test conflicts."""
        return int(time.time() * 1000) % 1000000

    @staticmethod
    def _unique_code(base="TEST"):
        """Generate unique code based on timestamp to avoid conflicts."""
        return f"{base}{int(time.time() * 1000) % 1000000}"

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    def test_admin_program_enrollment_post(self, session_full_db_setup, test_client, isolated_db_session):
        """Test POST request to /program/<codigo>/admin/enroll for administrative enrollment."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"prog_admin_{suffix}"
        admin_email = f"prog_admin_{suffix}@nowlms.com"

        admin_user = Usuario(
            usuario=admin_username,
            acceso=proteger_passwd("admin_pass"),
            nombre="Program",
            apellido="Admin",
            correo_electronico=admin_email,
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(admin_user)

        # Create student user
        student_username = f"prog_student_{suffix}"
        student_email = f"prog_student_{suffix}@nowlms.com"

        student_user = Usuario(
            usuario=student_username,
            acceso=proteger_passwd("student_pass"),
            nombre="Program",
            apellido="Student",
            correo_electronico=student_email,
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student_user)

        # Create program
        program_code = self._unique_code("ADMINENROLL")
        programa = Programa(
            nombre="Admin Enrollment Test Program",
            codigo=program_code,
            descripcion="Test program for admin enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request for admin enrollment
        enrollment_data = {"student_username": student_username}

        response = test_client.post(f"/program/{program_code}/admin/enroll", data=enrollment_data, follow_redirects=True)
        assert response.status_code == 200

    def test_enroll_user_program_post(self, session_full_db_setup, test_client, isolated_db_session):
        """Test POST request to /program/<codigo>/enroll_user for manual user enrollment."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"enroll_admin_{suffix}"
        admin_email = f"enroll_admin_{suffix}@nowlms.com"

        admin_user = Usuario(
            usuario=admin_username,
            acceso=proteger_passwd("admin_pass"),
            nombre="Enroll",
            apellido="Admin",
            correo_electronico=admin_email,
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(admin_user)

        # Create student user
        student_username = f"enroll_student_{suffix}"
        student_email = f"enroll_student_{suffix}@nowlms.com"

        student_user = Usuario(
            usuario=student_username,
            acceso=proteger_passwd("student_pass"),
            nombre="Enroll",
            apellido="Student",
            correo_electronico=student_email,
            tipo="student",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(student_user)

        # Create program
        program_code = self._unique_code("MANUALENROLL")
        programa = Programa(
            nombre="Manual Enrollment Test Program",
            codigo=program_code,
            descripcion="Test program for manual enrollment",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test POST request for manual enrollment
        enrollment_data = {"usuario_email": student_email}

        response = test_client.post(f"/program/{program_code}/enroll_user", data=enrollment_data, follow_redirects=True)
        assert response.status_code == 200

    def test_program_courses_manage_get(self, session_full_db_setup, test_client, isolated_db_session):
        """Test GET request to /program/<codigo>/courses/manage for accessing course management."""
        # Create admin user
        suffix = self._unique_suffix()
        admin_username = f"course_admin_{suffix}"
        admin_email = f"course_admin_{suffix}@nowlms.com"

        admin_user = Usuario(
            usuario=admin_username,
            acceso=proteger_passwd("admin_pass"),
            nombre="Course",
            apellido="Admin",
            correo_electronico=admin_email,
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        isolated_db_session.add(admin_user)

        # Create program
        program_code = self._unique_code("COURSEMANAGE")
        programa = Programa(
            nombre="Course Management Test Program",
            codigo=program_code,
            descripcion="Test program for course management",
            publico=True,
            estado="open",
        )
        isolated_db_session.add(programa)
        isolated_db_session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # Test GET request to course management page
        get_response = test_client.get(f"/program/{program_code}/courses/manage")
        assert get_response.status_code == 200
