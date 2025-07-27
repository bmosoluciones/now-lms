# Setup NOW Learning Management System in EL9

Update: 2025-05-24
Host: Rocky Linux 9.3

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
Create a run script file to start your system_

```
cd
touch run.py
vi run.py
```

Use this template
```
#! /home/serveradmin/venv/bin/python
from waitress import serve


from now_lms import lms_app, init_app

lms_app.config["SECRET_KEY"] = "a_very_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

if init_app():
    serve(app=lms_app, port=int(8080))
```

### Test your run scritp and setup ypur system
Create the database and the `admin` user with:

```
ADMIN_USER=adminuser ADMIN_PSWD=passSECURE123+ /home/serveradmin/run.py
```

This command will:
1. Setup a new database for the system
2. Create the user administrator
3. Start the WSGI server

You can check your system now at `https://your_ip` and see your new site, type `Ctrl + C` to stop the WSGI server.
