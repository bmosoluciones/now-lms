from os import environ


def test_command_line_interface(session_full_db_setup):
    environ["FLASK_APP"] = "now_lms"
    with session_full_db_setup.app_context():
        runner = session_full_db_setup.test_cli_runner()
        commands = ("database", "db", "info", "routes", "run", "serve", "settings", "shell", "version")
        for command in commands:
            result = runner.invoke(args=[command])
        info_commands = ("course", "path", "routes", "system")
        for command in info_commands:
            result = runner.invoke(args=["info", command])
        settings_commands = ("theme_get", "theme_list")
        for command in settings_commands:
            result = runner.invoke(args=["settings", command])
        resurlt = runner.invoke(args=["settings", "theme_set"], input="finance")
