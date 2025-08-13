def test_database_info_tools(full_db_setup):
    with full_db_setup.app_context():
        from now_lms.db.tools import database_is_populated

        assert database_is_populated(full_db_setup)
        from now_lms.db.info import course_info

        assert course_info("now")
        from now_lms.db.info import config_info

        assert config_info()
        from now_lms.db.info import lms_info

        assert lms_info()
        from now_lms.db.info import _obtener_info_sistema

        assert _obtener_info_sistema()


def test_db_tools_negative():
    from now_lms import lms_app

    with lms_app.app_context():
        from now_lms.db.tools import database_is_populated, check_db_access, get_current_theme

        assert not database_is_populated(lms_app)
        assert check_db_access(lms_app)  # True with SQLite
        assert get_current_theme() == "now_lms"


def test_user_access_negative(lms_application):
    with lms_application.app_context():
        from now_lms.auth import proteger_passwd
        from now_lms.db import Usuario, database

        user = Usuario(
            usuario="instructor1",
            acceso=proteger_passwd("testpass"),
            nombre="Test",
            apellido="Instructor",
            tipo="instructor",  # Rol requerido por la vista
            activo=True,
            correo_electronico_verificado=True,
        )
        database.session.add(user)
        database.session.commit()

        # Iniciar sesión como instructor
        with lms_application.test_client() as client:
            login_response = client.post(
                "/user/login",
                data={"usuario": "instructor1", "acceso": "testpass"},
                follow_redirects=True,
            )
            assert login_response.status_code == 200
            from now_lms.db.tools import verifica_docente_asignado_a_curso, verifica_moderador_asignado_a_curso

            assert verifica_docente_asignado_a_curso("now") is False
            assert verifica_moderador_asignado_a_curso("now") is False
