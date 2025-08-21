# Copyright 2021 -2023 William José Moreno Reyes
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
Specific functional tests for LMS views.
"""


def test_demo_course(session_full_db_setup_with_examples):
    """Test demo course view with session-scoped fixture that includes examples."""
    with session_full_db_setup_with_examples.app_context():
        with session_full_db_setup_with_examples.test_client() as client:
            client.get("/course/test/view")


def test_email_backend(session_basic_db_setup):
    """Test email backend configuration with session-scoped basic setup."""
    with session_basic_db_setup.app_context():
        with session_basic_db_setup.test_client() as client:
            client.get("/setting/mail")
            client.get("/setting/mail_check")
            data = {
                "MAIL_HOST": "smtp.server.domain",
                "MAIL_PORT": "465",
                "MAIL_USERNAME": "user@server.domain",
                "MAIL_PASSWORD": "ello123ass",
                "MAIL_USE_TLS": True,
                "MAIL_USE_SSL": True,
                "email": True,
            }
            client.post(
                "/setting/mail",
                data=data,
                follow_redirects=True,
            )


def test_contraseña_incorrecta(session_full_db_setup):
    """Test incorrect password validation with session-scoped full setup."""
    from now_lms.auth import validar_acceso

    with session_full_db_setup.app_context():
        from flask_login import current_user
        from flask_login.mixins import AnonymousUserMixin

        with session_full_db_setup.test_client() as client:
            # Keep the session alive until the with clause closes
            client.post("/user/login", data={"usuario": "lms-admin", "acceso": "lms_admin"})
            assert isinstance(current_user, AnonymousUserMixin)
            assert validar_acceso("lms-admn", "lms-admin") is False
            client.get("/user/logout")
