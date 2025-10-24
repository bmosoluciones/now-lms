from os import environ


def test_command_line_interface(session_full_db_setup):
    environ["FLASK_APP"] = "now_lms"
    with session_full_db_setup.app_context():
        runner = session_full_db_setup.test_cli_runner()
        commands = (
            "admin",
            "cache",
            "database",
            "db",
            "info",
            "routes",
            "run",
            "serve",
            "settings",
            "shell",
            "user",
            "version",
        )
        for command in commands:
            result = runner.invoke(args=[command])
        info_commands = ("course", "path", "routes", "system")
        for command in info_commands:
            result = runner.invoke(args=["info", command])
        settings_commands = ("theme_get", "theme_list")
        for command in settings_commands:
            result = runner.invoke(args=["settings", command])
        resurlt = runner.invoke(args=["settings", "theme_set"], input="classic")

        # Test new admin and user commands
        admin_commands = ("reset-password", "set")
        for command in admin_commands:
            result = runner.invoke(args=["admin", command, "--help"])

        user_commands = ("new", "set-password")
        for command in user_commands:
            result = runner.invoke(args=["user", command, "--help"])

        # Test new cache commands
        cache_commands = ("clear", "info", "stats")
        for command in cache_commands:
            result = runner.invoke(args=["cache", command])


def test_serve_command_wsgi_server_option():
    """Test that serve command has --wsgi-server option."""
    from now_lms import lms_app

    runner = lms_app.test_cli_runner()
    result = runner.invoke(args=["serve", "--help"])
    assert result.exit_code == 0
    assert "--wsgi-server" in result.output
    assert "waitress" in result.output
    assert "gunicorn" in result.output
