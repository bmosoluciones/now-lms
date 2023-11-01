# Install NOW - LMS in DreamHost shared host.

NOW - Learning Management System can be hosted at DreamHost shared hosting service, this is usefull if you alredy
have a host plan in DreamHost and you want to serve a few users, in a shared hosting enviroment there will be some
limitations like no separate cache service or memory constraints, but if you alredy have a host plan in DreamHost
adding NOW - Learning Management System  can be handy.

Last update: 2023 Nov 01

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

8. Go to the public directory in your.domain directory:

```
$ cd public
```

9. Create a app.py file following this template:

```
$ touch app.py
```

app.py template:
```
from now_lms import lms_app
# Configure your app:
lms_app.config["SECRET_KEY"] = "set_a_very_secure_secret_key"
lms_app.config["SQLALCHEMY_DATABASE_URI"] = "database_uri"

app = lms_app

from now_lms import serve, init_app

app.app_context().push()

if __name__ == "__main__":
    init_app(with_examples=False)
```

10. Init app:
Be sure to run ```lmsctl``` commands in the same directory that your app.py file.
You can set the Administrator user and password o let the user use the default values.
Since default values for admin user are publics in documentation they are more suitables
for development purposes that for production usage.

```
$ ls
app.py  favicon.gif  favicon.ico
$ ADMIN_USER=setyouruserhere ADMIN_PSWD=setasecurepasswd flask --app app.py setup
```

11. Your your.domain/public directory should be like this:

```
$ ls
app.py  favicon.gif  favicon.ico
```

12. Create a passenger_wsgi.py file in your.domain directory following the next template:

```
$ cd ..
# ls
public  venv
```

passenger_wsgi.py template:
```
import sys
import os


# Ensure we are using the virtual enviroment.
INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.environ["HOME"], "yourdomain.com", "public"))

# Now we can import the configured app from the current directory
from public.app import lms_app as application
```

13. You your.dommain folder should be like this:

```
$ ls
passenger_wsgi.py venv public
```

You can check your passenger file works running it with python:

```
$ python3.8 passenger_wsgi.py
```

Is there are no errors Passenger should be able to run NOW - LMS without issues.

Make the passenger_wsgi.py

```
$ chmod +x passenger_wsgi.py
```

14. Restart passenger:

```
mkdir tmp
touch tmp/restart.txt
```

your.domain directory should looks like this:

```
passenger_wsgi.py  public  tmp  venv
```

15. You should be able to acces NOW - LMS in your domain.
