from os import environ


def test_postgresl_connection():
    if environ.get("DATABASE_URL"):
        if "postgres:" in environ.get("DATABASE_URL") or "postgresql:" in environ.get("DATABASE_URL"):
            import pg8000.native

            con = pg8000.native.Connection("postgresdb", host="postgres", database="postgresdb", port=5432, password="postgresdb")
            test = con.run()
            assert test is not None


def test_mysql_connection():
    if environ.get("DATABASE_URL"):
        if "mysql:" in environ.get("DATABASE_URL"):
            import pymysql.cursors

            connection = pymysql.connect(
                host="mysql", user="mysqldb", password="mysqldb", database="mysqldb", cursorclass=pymysql.cursors.DictCursor
            )

            with connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION();")
                    result = cursor.fetchone()
                    assert result is not None
