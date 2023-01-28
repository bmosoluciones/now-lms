# Install NOW - LMS in DreamHost shared host.

NOW - Learning Management System can be hosted at DreamHost shared hosting service, this is usefull if you alredy
have a host plan in DreamHost and you want to serve a few users, in a shared hosting enviroment there will be some
limitations like no separate cache service or memory constraints, but if you alredy have a host plan in DreamHost
adding NOW - Learning Management System  can be handy.

Last update: 2023 Jan 26

1. Setup your domain with [Passenger](https://help.dreamhost.com/hc/en-us/articles/215769578-Passenger-overview) support.

2. Login via [SSH](https://help.dreamhost.com/hc/en-us/articles/216041267) to your host.

3. Install a recent version of python:

```
$ mkdir ~/py3_tmp
$ cd ~/py3_tmp/
$ wget https://www.python.org/ftp/python/3.10.9/Python-3.10.9.tar.xz
$ tar -xf Python-3.10.9.tar.xz
$ cd Python-3.10.9
$ ./configure --prefix=$HOME/opt/python-3.10.9
$ make
$ make install
$ $HOME/opt/python-3.10.9/bin/python3 --version
Python 3.10.9
```

4. Go to your domain folder:

```
$ cd you.domain
```

5. Create a python virtual enviroment:

```
$HOME/opt/python-3.10.9/bin/python3 -m venv venv
```

6. Activate the virtual env:

```
$ source venv/bin/activate
```

7. Install NOW - LMS:

```
$ pip install now_lms
```

8. Go to the public directory in your.domain directory:

```
$ cd public
```

9. Create a app.py file following this template:

```
from now_lms import lms_app
# Configure your app:
lms_app.config["ADMIN_USER"] = "your_admin_user"
lms_app.config["ADMIN_PSWD"] = "your_admin_user_password"
lms_app.config["SECRET_KEY"] = "set_a_very_secure_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

app = lms_app
```

10. Init app:
Be sure to run ```lmsctl``` commands in the same directory that your app.py file.


```
$ lmsctl setup
```

11. Your your.domain/public directory should be like this:

```
$ ls
app.py  favicon.gif  favicon.ico
```

12. Create a passenger_wsgi.py file in your.domain directory following the next template:

```
import sys, os

INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from now_lms import lms_app
# Copy paste the same configuration from /public/app.py
lms_app.config["SECRET_KEY"] = "set_a_very_secure_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"
# Or set proper ENVIROMENT VARIABLES

 application = lms_app
```

13. You your.dommain folder should be like this:

```
$ ls
passenger_wsgi.py venv public
```

14. Restart passenger:

```
mkdir public/tmp
touch tmp/restart.txt
```

15. You should be able to acces NOW - LMS in your domain.
