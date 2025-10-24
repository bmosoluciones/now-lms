# Setup NOW Learning Management System in EL9

Update: 2025-01-14
Host: Rocky Linux 9.3

!!! info "Comprehensive Server Administration Guide"
For complete server administration best practices including security hardening, monitoring, backup strategies, and enterprise compliance, see the **[RHEL/Alma/Rocky/Fedora Server Administration Guide](server-admin-rhel.md)**.

This document provides a quick setup guide for NOW-LMS on EL9 systems. For production environments, we strongly recommend following the comprehensive server administration practices.

## Update your server

Keep your server up to date:

```
dnf update -y
```

## Enable the web console

With Cockpit you can administer the server with out a SSH daemon.

```
sudo dnf install cockpit firewalld -y
sudo systemctl enable --now cockpit.socket
sudo systemctl enable firewalld --now
sudo firewall-cmd --add-service=cockpit
sudo firewall-cmd --add-service=cockpit --permanent
```

## Create a sudo user

Do not use the `root` user:

```
adduser serveradmin # User a custom user to make it more secure and hard to guest
passwd serveradmin
usermod -aG wheel serveradmin
```

Now you can admin your server from the web console and there is no need of the SSH daemon, be sure you can loggin with the sudo user at: `your_ip:9090`

## Secure the server

Block access to the `root` user:

```
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config_backup
# No root access
sudo vi /etc/ssh/sshd_config # Set: PermitRootLogin no
systemctl restart sshd
```

Or disable the SSHD service and use the web console to admin the server [recomended]

```
systemctl disable --now sshd
```

Only disable the SSHD server after you have logedin in the web console and verified you can perform administrative tasks.

## Install the Caddy Server:

Nginx is another good option:

```
sudo dnf install -y epel-release
sudo dnf install -y caddy
sudo firewall-cmd --permanent --zone=public --add-service=http
sudo firewall-cmd --permanent --zone=public --add-service=https
```

### Configure the Caddy Server:

```
mkdir /etc/caddy/
touch /etc/caddy/Caddyfile
vi /etc/caddy/Caddyfile
```

Set the Caddy Server to act as a reverse proxy:

```
:443 {
    reverse_proxy localhost:8080
}
```

### Start the Caddy Server

```
systemctl enable --now caddy
```

## Install NOW - Learning Management System

Install NOW - LMS

### Install system requirements

```
dnf install -y npm pango python3.12 python3.12-pip python3.12-cryptography git
```

### Create a virtual enviroment and install now-lms

Do not create the virtual enviroment using `root` or `sudo`:

```
python3.12 -m venv venv
source venv/bin/activate
git clone https://github.com/bmosoluciones/now-lms.git
cd now-lms/now_lms/static/
npm install
cd ..
dc ..
pip install -e .


# Postgresql
pip install pg8000

# MySQL
pip install mysqlclient
```

### Create a start script

Create a run script file to start your system\_

```
cd
touch run.py
vi run.py
```

Use this template

```
#! /home/serveradmin/venv/bin/python
from now_lms import create_app

app = create_app()
app.config["SECRET_KEY"] = "a_very_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

if __name__ == "__main__":
    # This script is designed to be used with a WSGI server like Waitress or Gunicorn
    # Run with Waitress (default, cross-platform): python run.py
    # Or with Gunicorn (Linux only): gunicorn --bind 0.0.0.0:8080 --workers 4 run:app
    pass
```

### Test your run script and setup your system

You can test the application factory works:

```
python /home/serveradmin/run.py
```

If there are no errors, you can now use a WSGI server to serve the application.

### Setup WSGI Server

NOW-LMS supports both Waitress (default, cross-platform) and Gunicorn (Linux only) as WSGI servers.

#### Option 1: Using Waitress (Recommended - Default)

Waitress is the default WSGI server and works on both Linux and Windows:

```
source /home/serveradmin/venv/bin/activate
pip install waitress
```

Run with Waitress:

```
python /home/serveradmin/run.py
```

Or using the CLI:

```
/home/serveradmin/venv/bin/lmsctl serve
# or specify explicitly: lmsctl serve --wsgi-server waitress
```

#### Option 2: Using Gunicorn (Linux Only)

Install Gunicorn in your virtual environment:

```
source /home/serveradmin/venv/bin/activate
pip install gunicorn
```

### Run with Gunicorn

Start the WSGI server with Gunicorn:

```
/home/serveradmin/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 4 --chdir /home/serveradmin run:app
```

Or using the CLI:

```
/home/serveradmin/venv/bin/lmsctl serve --wsgi-server gunicorn
```

### Create the database and admin user

Before starting the server for the first time, initialize the database:

```
export SECRET_KEY="a_very_secret_key"
export SQLALCHEMY_DATABASE_URI="database_uri"
ADMIN_USER=adminuser ADMIN_PSWD=passSECURE123+ /home/serveradmin/venv/bin/lmsctl database init
```

This command will:

1. Setup a new database for the system
2. Create the administrator user

You can check your system now at `https://your_ip` and see your new site.

For production, consider using a systemd service to manage the Gunicorn process.
