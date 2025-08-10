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

from now_lms.db import database
from now_lms.logs import log

"""
Comprehensive end-to-end tests for administrator views.
"""


def test_admin_users_list_view(full_db_setup, client):
    """Test GET and POST for admin users list view."""
    app = full_db_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access admin users list
    get_response = client.get("/admin/users/list")
    assert get_response.status_code == 200
    assert "admin_test".encode("utf-8") in get_response.data or "Admin".encode("utf-8") in get_response.data


def test_admin_users_list_inactive_view(full_db_setup, client):
    """Test GET for admin inactive users list view."""
    app = full_db_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )

        # Create inactive user for testing
        inactive_user = Usuario(
            usuario="inactive_test",
            acceso=proteger_passwd("inactive_pass"),
            nombre="Inactive",
            apellido="User",
            correo_electronico="inactive@nowlms.com",
            tipo="student",
            activo=False,
            correo_electronico_verificado=True,
        )

        database.session.add(admin_user)
        database.session.add(inactive_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access admin inactive users list
    get_response = client.get("/admin/users/list_inactive")
    assert get_response.status_code == 200
    # Should show inactive users
    assert "inactive_test".encode("utf-8") in get_response.data or "Inactive".encode("utf-8") in get_response.data


def test_admin_new_user_creation(full_db_setup, client):
    """Test GET and POST for admin user creation."""
    app = full_db_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access new user creation form
    get_response = client.get("/user/new_user")
    assert get_response.status_code == 200
    assert "nombre".encode("utf-8") in get_response.data or "Nombre".encode("utf-8") in get_response.data

    # POST: Create new user
    post_response = client.post(
        "/user/new_user",
        data={
            "nombre": "NewUser",
            "apellido": "TestUser",
            "correo_electronico": "newuser@nowlms.com",
            "usuario": "newuser_test",
            "acceso": "newuser_pass",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify user was created
    with app.app_context():
        new_user = database.session.execute(database.select(Usuario).filter_by(usuario="newuser_test")).scalars().first()
        assert new_user is not None
        assert new_user.nombre == "NewUser"
        assert new_user.tipo == "student"


def test_instructor_group_list_view(full_db_setup, client):
    """Test GET for instructor group list view."""
    app = full_db_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create instructor user (required for accessing instructor group views)
    with app.app_context():
        instructor_user = Usuario(
            usuario="instructor_test",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Instructor",
            apellido="Test",
            correo_electronico="instructor@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor_user)
        database.session.commit()

    # Login as instructor
    login_response = client.post(
        "/user/login",
        data={"usuario": "instructor_test", "acceso": "instructor_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access instructor group list
    get_response = client.get("/instructor/group/list")
    assert get_response.status_code == 200


def test_admin_group_creation(full_db_setup, client):
    """Test GET and POST for admin group creation."""
    app = full_db_setup
    from now_lms.db import Usuario, UsuarioGrupo
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access new group creation form
    get_response = client.get("/group/new")
    assert get_response.status_code == 200
    assert "nombre".encode("utf-8") in get_response.data or "Nombre".encode("utf-8") in get_response.data

    # POST: Create new group
    post_response = client.post(
        "/group/new",
        data={
            "nombre": "Test Group",
            "descripcion": "A test group for end-to-end testing",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify group was created
    with app.app_context():
        new_group = database.session.execute(database.select(UsuarioGrupo).filter_by(nombre="Test Group")).scalars().first()
        assert new_group is not None
        assert new_group.descripcion == "A test group for end-to-end testing"


def test_admin_general_settings(full_db_setup, client):
    """Test GET and POST for admin general settings."""
    app = full_db_setup
    from now_lms.db import Usuario, Configuracion
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access general settings
    get_response = client.get("/setting/general")
    assert get_response.status_code == 200
    assert "titulo".encode("utf-8") in get_response.data or "descripcion".encode("utf-8") in get_response.data

    # POST: Update general settings
    post_response = client.post(
        "/setting/general",
        data={
            "titulo": "Test LMS Updated",
            "descripcion": "Updated description for testing",
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
    with app.app_context():
        config = database.session.execute(database.select(Configuracion)).scalars().first()
        assert config.titulo == "Test LMS Updated"
        assert config.descripcion == "Updated description for testing"


def test_admin_theming_settings(full_db_setup, client):
    """Test GET and POST for admin theming settings."""
    app = full_db_setup
    from now_lms.db import Usuario, Style
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access theming settings
    get_response = client.get("/setting/theming")
    assert get_response.status_code == 200
    assert "style".encode("utf-8") in get_response.data or "tema".encode("utf-8") in get_response.data

    # POST: Update theming settings
    post_response = client.post(
        "/setting/theming",
        data={
            "style": "classic",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify theme was updated
    with app.app_context():
        style_config = database.session.execute(database.select(Style)).scalars().first()
        assert style_config.theme == "classic"


def test_admin_mail_settings(full_db_setup, client):
    """Test GET and POST for admin mail settings."""
    app = full_db_setup
    from now_lms.db import Usuario, MailConfig
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access mail settings
    get_response = client.get("/setting/mail")
    assert get_response.status_code == 200
    assert "MAIL_SERVER".encode("utf-8") in get_response.data or "correo".encode("utf-8") in get_response.data

    # POST: Update mail settings
    post_response = client.post(
        "/setting/mail",
        data={
            "MAIL_SERVER": "smtp.test.com",
            "MAIL_PORT": "587",
            "MAIL_USERNAME": "test@nowlms.com",
            "MAIL_PASSWORD": "test_password",
            "MAIL_USE_TLS": True,
            "MAIL_USE_SSL": False,
            "MAIL_DEFAULT_SENDER": "test@nowlms.com",
            "MAIL_DEFAULT_SENDER_NAME": "Test LMS",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify mail settings were updated
    with app.app_context():
        mail_config = database.session.execute(database.select(MailConfig)).scalars().first()
        assert mail_config.MAIL_SERVER == "smtp.test.com"
        assert mail_config.MAIL_PORT == "587"  # Port is stored as string


def test_admin_paypal_settings(full_db_setup, client):
    """Test GET and POST for admin PayPal settings."""
    app = full_db_setup
    from now_lms.db import Usuario, PaypalConfig
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access PayPal settings
    get_response = client.get("/setting/paypal")
    assert get_response.status_code == 200
    assert "paypal".encode("utf-8") in get_response.data or "PayPal".encode("utf-8") in get_response.data

    # POST: Update PayPal settings (without enabling to avoid validation)
    post_response = client.post(
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
    with app.app_context():
        paypal_config = database.session.execute(database.select(PaypalConfig)).scalars().first()
        # PayPal config exists and sandbox setting was updated
        assert paypal_config is not None
        assert paypal_config.sandbox is True


def test_admin_blog_management(full_db_setup, client):
    """Test GET and POST for admin blog management."""
    app = full_db_setup
    from now_lms.db import Usuario, BlogPost
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access admin blog management
    get_response = client.get("/admin/blog")
    assert get_response.status_code == 200

    # GET: Access new blog post form
    get_new_response = client.get("/admin/blog/posts/new")
    assert get_new_response.status_code == 200
    assert "title".encode("utf-8") in get_new_response.data or "titulo".encode("utf-8") in get_new_response.data

    # POST: Create new blog post
    post_response = client.post(
        "/admin/blog/posts/new",
        data={
            "nombre": "Test Blog Post",  # BaseForm field
            "descripcion": "This is a test blog post content.",  # BaseForm field
            "title": "Test Blog Post",  # BlogPostForm field
            "content": "This is a test blog post content.",  # BlogPostForm field
            "tags": "test, admin, blog",
            "allow_comments": True,
            "status": "published",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify blog post was created
    with app.app_context():
        blog_post = database.session.execute(database.select(BlogPost).filter_by(title="Test Blog Post")).scalars().first()
        assert blog_post is not None
        assert blog_post.author_id == "admin_test"


def test_admin_blog_tags_management(full_db_setup, client):
    """Test GET and POST for admin blog tags management."""
    app = full_db_setup
    from now_lms.db import Usuario, BlogTag
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access admin blog tags management
    get_response = client.get("/admin/blog/tags")
    assert get_response.status_code == 200

    # POST: Create new blog tag
    post_response = client.post(
        "/admin/blog/tags",
        data={
            "nombre": "Test Tag",  # BaseForm field
            "descripcion": "A test tag for end-to-end testing",  # BaseForm field
            "name": "Test Tag",  # BlogTagForm field
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify blog tag was created
    with app.app_context():
        blog_tag = database.session.execute(database.select(BlogTag).filter_by(name="Test Tag")).scalars().first()
        assert blog_tag is not None
        assert blog_tag.name == "Test Tag"


def test_admin_announcements_management(full_db_setup, client):
    """Test GET and POST for admin announcements management."""
    app = full_db_setup
    from now_lms.db import Usuario, Announcement
    from now_lms.auth import proteger_passwd
    from datetime import datetime

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_test",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Test",
            correo_electronico="admin@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_test", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # GET: Access admin announcements
    get_response = client.get("/admin/announcements")
    assert get_response.status_code == 200

    # GET: Access new announcement form
    get_new_response = client.get("/admin/announcements/new")
    assert get_new_response.status_code == 200
    assert "title".encode("utf-8") in get_new_response.data or "titulo".encode("utf-8") in get_new_response.data

    # POST: Create new announcement
    future_date = datetime.now().date().replace(year=datetime.now().year + 1)
    post_response = client.post(
        "/admin/announcements/new",
        data={
            "nombre": "Test Global Announcement",  # BaseForm field
            "descripcion": "This is a test global announcement for end-to-end testing.",  # BaseForm field
            "title": "Test Global Announcement",  # AnnouncementForm field
            "message": "This is a test global announcement for end-to-end testing.",  # AnnouncementForm field
            "expires_at": future_date.strftime("%Y-%m-%d"),
            "is_sticky": True,
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200

    # Verify announcement was created
    with app.app_context():
        announcement = (
            database.session.execute(database.select(Announcement).filter_by(title="Test Global Announcement"))
            .scalars()
            .first()
        )
        assert announcement is not None
        assert announcement.created_by_id == "admin_test"
        assert announcement.course_id is None  # Global announcement
        assert announcement.is_sticky is True


def test_admin_comprehensive_flow(full_db_setup, client):
    """Test comprehensive admin workflow covering multiple admin views."""
    app = full_db_setup
    from now_lms.db import Usuario
    from now_lms.auth import proteger_passwd

    # Create admin user
    with app.app_context():
        admin_user = Usuario(
            usuario="admin_comprehensive",
            acceso=proteger_passwd("admin_pass"),
            nombre="Admin",
            apellido="Comprehensive",
            correo_electronico="admin.comprehensive@nowlms.com",
            tipo="admin",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(admin_user)
        database.session.commit()

    # Login as admin
    login_response = client.post(
        "/user/login",
        data={"usuario": "admin_comprehensive", "acceso": "admin_pass"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200

    # Test multiple admin views in sequence
    admin_routes = [
        "/admin/users/list",
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
        get_response = client.get(route)
        assert get_response.status_code == 200, f"Failed to access {route}"

    # Test instructor-specific route (requires instructor role, but admin should also have access)
    instructor_routes = [
        "/instructor/group/list",
    ]

    # For instructor routes, we need to create an instructor user
    with app.app_context():
        instructor_user = Usuario(
            usuario="instructor_comprehensive",
            acceso=proteger_passwd("instructor_pass"),
            nombre="Instructor",
            apellido="Comprehensive",
            correo_electronico="instructor.comprehensive@nowlms.com",
            tipo="instructor",
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(instructor_user)
        database.session.commit()

    # Logout admin and login as instructor for instructor-specific routes
    client.get("/user/logout")
    instructor_login = client.post(
        "/user/login",
        data={"usuario": "instructor_comprehensive", "acceso": "instructor_pass"},
        follow_redirects=True,
    )
    assert instructor_login.status_code == 200

    for route in instructor_routes:
        log.info(f"Testing instructor route: {route}")
        get_response = client.get(route)
        assert get_response.status_code == 200, f"Failed to access {route}"
