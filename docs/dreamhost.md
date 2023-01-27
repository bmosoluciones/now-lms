# Install NOW - LMS in DreamHost shared host.

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
3. Go to your domain folder:
```
$ cd you.domain
```
7. Go to the public folder:
```
$ cd public
```
8. Create a python virtual enviroment:
```
$HOME/opt/python-3.10.9/bin/python3 -m venv venv
```
9. Activate the virtual env:
```
$ source venv/bin/activate
```
10. Install NOW - LMS:
```
$ pip install now_lms
```
11. Create a app.py file:
```
from now_lms import lms_app as app
```
12. Init app:
```
$ lmsctl setup
```
12. Your your.domain/public directory should be like this:
```
$ ls
__pycache__  app.py  favicon.gif  favicon.ico  tmp  venv
```

13. Crea a passenger_wsgi.py file in your domain directory:
```
import sys, os

INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "public", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from now_lms import lms_app as application
```
15. You your.dommain folder should be like this:
```
$ ls
passenger_wsgi.py  passenger_wsgi.pyc  public
```
14. Restart passenger:
```
mkdir public/tmp
touch tmp/restart.txt
```
15. You should be able to acces NOW - LMS in your domain.
