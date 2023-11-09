# Install NOW - LMS in DreamHost shared host.

NOW - Learning Management System can be hosted at DreamHost shared hosting service, this is usefull if you alredy
have a host plan in DreamHost and you want to serve a few users, in a shared hosting enviroment there will be some
limitations like no separate cache service or memory constraints, but if you alredy have a host plan in DreamHost
adding NOW - Learning Management System can be handy.

Last update: 2023 Nov 09

1. Setup your domain with [Passenger](https://help.dreamhost.com/hc/en-us/articles/215769578-Passenger-overview) support.

2. Login via [SSH](https://help.dreamhost.com/hc/en-us/articles/216041267) to your host.

3. Check your python3 version:

```
$ cat /etc/issue
Ubuntu 20.04.6 LTS
$ python3 --version
Python 3.8.10

```
You need Python >= 3.8 in order to run NOW - LMS, with the current version of Python available in DreamHost you can run a NOW - LMS instance.

4. Go to your domain folder:

```
$ cd your.domain
```

5. Create a python virtual enviroment:

```
$ virtualenv venv
$ ls
public  venv 
```

6. Activate the virtual env:

```
$ source venv/bin/activate
```

7. Install NOW - LMS:

```
$ pip install now_lms
```

8. Create a passenger_wsgi.py file in your.domain directory following the next template:

```
$ ls
public  venv
$ touch passenger_wsgi.py
```

passenger_wsgi.py template:
```
import sys
import os


# Ensure we are using the virtual enviroment.
INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Configure NOW - LMS via enviroment variables before import the app.
# Reference:
#  - https://bmosoluciones.github.io/now-lms/setup-conf.html#list-of-options
os.environ["SECRET_KEY"] = "set_a_very_secure_secret_key"
os.environ["SQLALCHEMY_DATABASE_URI"] = "database_uri"
os.environ["UPLOAD_FILES_DIR"] = os.path.join(os.environ["HOME"], "yourdomain.com", "public", "files")

# Now we can import the app so it can read the configuration from the env.
from now_lms import lms_app as application
```

9. Init NOW - LMS, be sure to run this commands in the same directory that your passenger_wsgi.py file.
You can set the Administrator user and password o let the user use the default values.
Since default values for admin user are publics in documentation they are more suitables
for development purposes that for production usage.

```
$ ls
passenger_wsgi.py venv public
$ ADMIN_USER=setyouruserhere ADMIN_PSWD=setasecurepasswd flask --app passenger_wsgi.py setup
```
You should se the message: NOW - LMS iniciado correctamente.
You can ignore: AssertionError: Popped wrong app context, this message con from the way flask check the current app
running in the command line.

10. You your.dommain folder should be like this:

```
$ ls
passenger_wsgi.py venv public
```

11. You can check your passenger file works running it with python:

```
$ python3.8 passenger_wsgi.py
```

Is there are no errors Passenger should be able to run NOW - LMS without issues.

Make the passenger_wsgi.py

```
$ chmod +x passenger_wsgi.py
```

12. Restart passenger:

```
$ mkdir tmp
$ touch tmp/restart.txt
```

your.domain directory should looks like this:

```
passenger_wsgi.py  public  tmp  venv
```

15. You should be able to acces NOW - LMS in your domain.
