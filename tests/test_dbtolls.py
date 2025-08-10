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
        