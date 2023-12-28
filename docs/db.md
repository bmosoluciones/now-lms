# Database setup

NOW Learning Management System requires access to a database engine to store and consult data,
like users, courses, programs, etc, etc.

We support by default SQLite, MySQL and PostgreSQL.

### SQLite

[SQLite](https://www.sqlite.org/index.html) works out of the box and if the default option for development,
if you want to use the sytem to serve a small amount of user SQLite will work fine, but many hosting options
do not provide access to persisten storage out of the box so many tines you will need a separate database host
to save your data.

If not other database service if defined in the configuration NOW - LMS will default to a local SQLite database:

```
python -m now_lms
```

### PostgreSQL

For many user [PostreSQL](https://www.postgresql.org/) is the best open source database engine, NOW - LMS support
PostgreSQL as a primary database host, and there many cloud providers ofering PostgreSQL as a service like:

-   [ElephantSQL](https://www.elephantsql.com/)
-   [Google Cloud SQL for PostgreSQL](https://cloud.google.com/sql/postgresql)
-   [Amazon RDS para PostgreSQL](https://aws.amazon.com/es/rds/postgresql/)

Also you can setup a PostgreSQL service in a Linux server following the next steps:

```
# On Fedora, Rocky Linux, Alma or RHEL:
sudo dnf install postgresql-server postgresql-contrib
sudo postgresql-setup --initdb --unit postgresql
sudo systemctl start postgresql
sudo -u postgres psql
# We use "postgresdb"  as the demo user, password and database name, you must
# use another database name or secure user credentials and update the
# conection string before running the NOW - LMS service.
postgres=# CREATE USER postgresdb WITH PASSWORD 'postgresdb';
postgres=# CREATE DATABASE postgresdb OWNER postgresdb;
postgres=# \q
```

Allow connet with user and password:

```
sudo gedit /var/lib/pgsql/data/pg_hba.conf
```

And edit the line `host all all 127.0.0.1/32 ident` and set it to `host all all 127.0.0.1/32 md5`

In this example the database server and the aplication server runs in the same host, if you want to user a
diferent server for the database service please read the PostgreSQL docs.

Refer to the [configuration guide](setup-conf.md) about how to configure the connection to the database server.

## MySQL

In the begining of the modern web there were 4 main tecnologies powering the
[dot-com boom](https://en.wikipedia.org/wiki/Dot-com_bubble): Linux, MySQL, Apache Web Server and {PHP, Python, Perl},
as today [MySQL](https://www.mysql.com/) is still a massive option for database service and is the default option for
shared host services, NOW - LMS support MySQL by default.

There are many cloud providers oferring MySQL as a service like:

-   [Oracle MySQL HeatWave Database Service](https://www.oracle.com/mysql/)
-   [Google Cloud SQL for MySQL](https://cloud.google.com/sql/mysql)

```
# On Fedora, Rocky Linux, Alma and RHEL
sudo dnf install community-mysql-server -y
sudo systemctl start mysqld
sudo mysql_secure_installation
sudo mysql -u root -p
# We use "mysqldatabase"  as the default user, password and database name, you
# must use another database and secure name or user credentials and update the
# conection string before running the service.
CREATE USER 'mysqldatabase'@'localhost' IDENTIFIED BY 'mysqldatabase';
CREATE DATABASE mysqldatabase;
GRANT ALL PRIVILEGES ON mysqldatabase.* TO 'mysqldatabase'@'localhost';
FLUSH PRIVILEGES;
```

For the most the users, this script will work fine but if it asks you for the password, you can retrieve a temporary password from mysqld.log at /var/log/ by the given command:

```
sudo grep 'temporary password' /var/log/mysqld.log
```

In this example the database server and the aplication server runs in the same host, if you want to user a
diferent server for the database service please read the MySQL docs.

Refer to the [configuration guide](setup-conf.md) about how to configure the connection to the database server.
