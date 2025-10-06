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

import pytest

from now_lms.db import database
from now_lms.logs import log

"""
Comprehensive end-to-end tests for administrator views using session-scoped fixtures.
"""


class TestEndToEndAdminSessionFixtures:
    """End-to-end admin tests converted to use session-scoped fixtures."""

    @pytest.fixture(scope="function")
    def test_client(self, session_full_db_setup):
        """Provide test client using session fixture."""
        return session_full_db_setup.test_client()

    def test_admin_users_list_view_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin users list view using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_{unique_suffix}"
        admin_email = f"admin_test_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access admin users list
        get_response = test_client.get("/admin/users/list")
        assert get_response.status_code == 200
        assert admin_username.encode("utf-8") in get_response.data or "Admin".encode("utf-8") in get_response.data

    def test_admin_users_list_inactive_view_session(self, session_full_db_setup, test_client):
        """Test GET for admin inactive users list view using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_inactive_{unique_suffix}"
        admin_email = f"admin_test_inactive_{unique_suffix}@nowlms.com"
        inactive_username = f"inactive_test_{unique_suffix}"
        inactive_email = f"inactive_test_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Create admin user and inactive user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
                correo_electronico=admin_email,
                tipo="admin",
                activo=True,
                correo_electronico_verificado=True,
            )

            # Create inactive user for testing
            inactive_user = Usuario(
                usuario=inactive_username,
                acceso=proteger_passwd("inactive_pass"),
                nombre="Inactive",
                apellido="User",
                correo_electronico=inactive_email,
                tipo="student",
                activo=False,
                correo_electronico_verificado=True,
            )

            database.session.add(admin_user)
            database.session.add(inactive_user)
            database.session.commit()

        # Login as admin
        login_response = test_client.post(
            "/user/login",
            data={"usuario": admin_username, "acceso": "admin_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # GET: Access admin inactive users list
        get_response = test_client.get("/admin/users/list_inactive")
        assert get_response.status_code == 200
        # Should show inactive users
        assert inactive_username.encode("utf-8") in get_response.data or "Inactive".encode("utf-8") in get_response.data

    def test_admin_new_user_creation_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin user creation using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_newuser_{unique_suffix}"
        admin_email = f"admin_test_newuser_{unique_suffix}@nowlms.com"
        new_username = f"newuser_test_{unique_suffix}"
        new_email = f"newuser_test_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access new user creation form
        get_response = test_client.get("/user/new_user")
        assert get_response.status_code == 200
        assert "nombre".encode("utf-8") in get_response.data or "Nombre".encode("utf-8") in get_response.data

        # POST: Create new user
        post_response = test_client.post(
            "/user/new_user",
            data={
                "nombre": "NewUser",
                "apellido": "TestUser",
                "correo_electronico": new_email,
                "usuario": new_username,
                "acceso": "newuser_pass",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify user was created
        with session_full_db_setup.app_context():
            new_user = database.session.execute(database.select(Usuario).filter_by(usuario=new_username)).scalars().first()
            assert new_user is not None
            assert new_user.nombre == "NewUser"
            assert new_user.tipo == "student"

    def test_instructor_group_list_view_session(self, session_full_db_setup, test_client):
        """Test GET for instructor group list view using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        instructor_username = f"instructor_test_{unique_suffix}"
        instructor_email = f"instructor_test_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Create instructor user (required for accessing instructor group views)
        with session_full_db_setup.app_context():
            instructor_user = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Instructor",
                apellido="Test",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)
            database.session.commit()

        # Login as instructor
        login_response = test_client.post(
            "/user/login",
            data={"usuario": instructor_username, "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200

        # GET: Access instructor group list
        get_response = test_client.get("/instructor/group/list")
        assert get_response.status_code == 200

    def test_admin_group_creation_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin group creation using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_group_{unique_suffix}"
        admin_email = f"admin_test_group_{unique_suffix}@nowlms.com"
        group_name = f"Test Group {unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario, UsuarioGrupo

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access new group creation form
        get_response = test_client.get("/group/new")
        assert get_response.status_code == 200
        assert "nombre".encode("utf-8") in get_response.data or "Nombre".encode("utf-8") in get_response.data

        # POST: Create new group
        post_response = test_client.post(
            "/group/new",
            data={
                "nombre": group_name,
                "descripcion": "A test group for end-to-end testing",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify group was created
        with session_full_db_setup.app_context():
            new_group = database.session.execute(database.select(UsuarioGrupo).filter_by(nombre=group_name)).scalars().first()
            assert new_group is not None
            assert new_group.descripcion == "A test group for end-to-end testing"

    def test_admin_general_settings_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin general settings using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_settings_{unique_suffix}"
        admin_email = f"admin_test_settings_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Configuracion, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access general settings
        get_response = test_client.get("/setting/general")
        assert get_response.status_code == 200
        assert "titulo".encode("utf-8") in get_response.data or "descripcion".encode("utf-8") in get_response.data

        # POST: Update general settings
        post_response = test_client.post(
            "/setting/general",
            data={
                "titulo": f"Test LMS Updated {unique_suffix}",
                "descripcion": f"Updated description for testing {unique_suffix}",
                "moneda": "USD",
                "verify_user_by_email": False,
                "enable_programs": True,
                "enable_masterclass": False,
                "enable_resources": True,
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify settings were updated
        with session_full_db_setup.app_context():
            config = database.session.execute(database.select(Configuracion)).scalars().first()
            assert config.titulo == f"Test LMS Updated {unique_suffix}"
            assert config.descripcion == f"Updated description for testing {unique_suffix}"

    def test_admin_theming_settings_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin theming settings using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_theming_{unique_suffix}"
        admin_email = f"admin_test_theming_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Style, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access theming settings
        get_response = test_client.get("/setting/theming")
        assert get_response.status_code == 200
        assert "style".encode("utf-8") in get_response.data or "tema".encode("utf-8") in get_response.data

        # POST: Update theming settings
        post_response = test_client.post(
            "/setting/theming",
            data={
                "style": "classic",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify theme was updated
        with session_full_db_setup.app_context():
            style_config = database.session.execute(database.select(Style)).scalars().first()
            assert style_config.theme == "classic"

    def test_admin_mail_settings_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin mail settings using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_mail_{unique_suffix}"
        admin_email = f"admin_test_mail_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import MailConfig, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access mail settings
        get_response = test_client.get("/setting/mail")
        assert get_response.status_code == 200
        assert "MAIL_SERVER".encode("utf-8") in get_response.data or "correo".encode("utf-8") in get_response.data

        # POST: Update mail settings
        post_response = test_client.post(
            "/setting/mail",
            data={
                "MAIL_SERVER": "smtp.test.com",
                "MAIL_PORT": "587",
                "MAIL_USERNAME": f"test_{unique_suffix}@nowlms.com",
                "MAIL_PASSWORD": "test_password",
                "MAIL_USE_TLS": True,
                "MAIL_USE_SSL": False,
                "MAIL_DEFAULT_SENDER": f"test_{unique_suffix}@nowlms.com",
                "MAIL_DEFAULT_SENDER_NAME": "Test LMS",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify mail settings were updated
        with session_full_db_setup.app_context():
            mail_config = database.session.execute(database.select(MailConfig)).scalars().first()
            assert mail_config.MAIL_SERVER == "smtp.test.com"
            assert mail_config.MAIL_PORT == "587"  # Port is stored as string

    def test_admin_paypal_settings_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin PayPal settings using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_paypal_{unique_suffix}"
        admin_email = f"admin_test_paypal_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import PaypalConfig, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access PayPal settings
        get_response = test_client.get("/setting/paypal")
        assert get_response.status_code == 200
        assert "paypal".encode("utf-8") in get_response.data or "PayPal".encode("utf-8") in get_response.data

        # POST: Update PayPal settings (without enabling to avoid validation)
        post_response = test_client.post(
            "/setting/paypal",
            data={
                "habilitado": False,
                "sandbox": True,
                "paypal_id": "",
                "paypal_sandbox": "",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify PayPal settings were updated (just check that we can read them back)
        with session_full_db_setup.app_context():
            paypal_config = database.session.execute(database.select(PaypalConfig)).scalars().first()
            # PayPal config exists and sandbox setting was updated
            assert paypal_config is not None
            assert paypal_config.sandbox is True

    def test_admin_blog_management_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin blog management using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_blog_{unique_suffix}"
        admin_email = f"admin_test_blog_{unique_suffix}@nowlms.com"
        blog_title = f"Test Blog Post {unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import BlogPost, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access admin blog management
        get_response = test_client.get("/admin/blog")
        assert get_response.status_code == 200

        # GET: Access new blog post form
        get_new_response = test_client.get("/admin/blog/posts/new")
        assert get_new_response.status_code == 200
        assert "title".encode("utf-8") in get_new_response.data or "titulo".encode("utf-8") in get_new_response.data

        # POST: Create new blog post
        post_response = test_client.post(
            "/admin/blog/posts/new",
            data={
                "nombre": blog_title,  # BaseForm field
                "descripcion": f"This is a test blog post content {unique_suffix}.",  # BaseForm field
                "title": blog_title,  # BlogPostForm field
                "content": f"This is a test blog post content {unique_suffix}.",  # BlogPostForm field
                "tags": "test, admin, blog",
                "allow_comments": True,
                "status": "published",
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify blog post was created
        with session_full_db_setup.app_context():
            blog_post = database.session.execute(database.select(BlogPost).filter_by(title=blog_title)).scalars().first()
            assert blog_post is not None
            assert blog_post.author_id == admin_username

    def test_admin_blog_tags_management_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin blog tags management using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_blogtags_{unique_suffix}"
        admin_email = f"admin_test_blogtags_{unique_suffix}@nowlms.com"
        tag_name = f"Test Tag {unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import BlogTag, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access admin blog tags management
        get_response = test_client.get("/admin/blog/tags")
        assert get_response.status_code == 200

        # POST: Create new blog tag
        post_response = test_client.post(
            "/admin/blog/tags",
            data={
                "nombre": tag_name,  # BaseForm field
                "descripcion": f"A test tag for end-to-end testing {unique_suffix}",  # BaseForm field
                "name": tag_name,  # BlogTagForm field
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify blog tag was created
        with session_full_db_setup.app_context():
            blog_tag = database.session.execute(database.select(BlogTag).filter_by(name=tag_name)).scalars().first()
            assert blog_tag is not None
            assert blog_tag.name == tag_name

    def test_admin_announcements_management_session(self, session_full_db_setup, test_client):
        """Test GET and POST for admin announcements management using session fixture."""
        import time
        from datetime import datetime

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_test_announcements_{unique_suffix}"
        admin_email = f"admin_test_announcements_{unique_suffix}@nowlms.com"
        announcement_title = f"Test Global Announcement {unique_suffix}"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Announcement, Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Test",
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

        # GET: Access admin announcements
        get_response = test_client.get("/admin/announcements")
        assert get_response.status_code == 200

        # GET: Access new announcement form
        get_new_response = test_client.get("/admin/announcements/new")
        assert get_new_response.status_code == 200
        assert "title".encode("utf-8") in get_new_response.data or "titulo".encode("utf-8") in get_new_response.data

        # POST: Create new announcement
        future_date = datetime.now().date().replace(year=datetime.now().year + 1)
        post_response = test_client.post(
            "/admin/announcements/new",
            data={
                "nombre": announcement_title,  # BaseForm field
                "descripcion": f"This is a test global announcement for end-to-end testing {unique_suffix}.",  # BaseForm field
                "title": announcement_title,  # AnnouncementForm field
                "message": f"This is a test global announcement for end-to-end testing {unique_suffix}.",  # AnnouncementForm field
                "expires_at": future_date.strftime("%Y-%m-%d"),
                "is_sticky": True,
            },
            follow_redirects=True,
        )
        assert post_response.status_code == 200

        # Verify announcement was created
        with session_full_db_setup.app_context():
            announcement = (
                database.session.execute(database.select(Announcement).filter_by(title=announcement_title)).scalars().first()
            )
            assert announcement is not None
            assert announcement.created_by_id == admin_username
            assert announcement.course_id is None  # Global announcement
            assert announcement.is_sticky is True

    @pytest.mark.slow
    def test_admin_comprehensive_flow_session(self, session_full_db_setup, test_client):
        """Test comprehensive admin workflow covering multiple admin views using session fixture."""
        import time

        # Generate unique username to avoid conflicts
        unique_suffix = int(time.time() * 1000) % 1000000
        admin_username = f"admin_comprehensive_{unique_suffix}"
        admin_email = f"admin_comprehensive_{unique_suffix}@nowlms.com"
        instructor_username = f"instructor_comprehensive_{unique_suffix}"
        instructor_email = f"instructor_comprehensive_{unique_suffix}@nowlms.com"

        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario

        # Create admin user
        with session_full_db_setup.app_context():
            admin_user = Usuario(
                usuario=admin_username,
                acceso=proteger_passwd("admin_pass"),
                nombre="Admin",
                apellido="Comprehensive",
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

        # Test multiple admin views in sequence (excluding problematic pagination route)
        admin_routes = [
            # "/admin/users/list",  # Skip due to pagination URL routing issue in session fixtures
            "/admin/users/list_inactive",
            "/user/new_user",
            "/group/new",
            "/setting/general",
            "/setting/theming",
            "/setting/mail",
            "/setting/paypal",
            "/admin/blog",
            "/admin/blog/tags",
            "/admin/announcements",
            "/admin/announcements/new",
        ]

        for route in admin_routes:
            log.info(f"Testing admin route: {route}")
            get_response = test_client.get(route)
            assert get_response.status_code == 200, f"Failed to access {route}"

        # Test instructor-specific route (requires instructor role, but admin should also have access)
        instructor_routes = [
            "/instructor/group/list",
        ]

        # For instructor routes, we need to create an instructor user
        with session_full_db_setup.app_context():
            instructor_user = Usuario(
                usuario=instructor_username,
                acceso=proteger_passwd("instructor_pass"),
                nombre="Instructor",
                apellido="Comprehensive",
                correo_electronico=instructor_email,
                tipo="instructor",
                activo=True,
                correo_electronico_verificado=True,
            )
            database.session.add(instructor_user)
            database.session.commit()

        # Logout admin and login as instructor for instructor-specific routes
        test_client.get("/user/logout")
        instructor_login = test_client.post(
            "/user/login",
            data={"usuario": instructor_username, "acceso": "instructor_pass"},
            follow_redirects=True,
        )
        assert instructor_login.status_code == 200

        for route in instructor_routes:
            log.info(f"Testing instructor route: {route}")
            get_response = test_client.get(route)
            assert get_response.status_code == 200, f"Failed to access {route}"
