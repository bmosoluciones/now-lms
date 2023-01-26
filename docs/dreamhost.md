# Install NOW - LMS in DreamHost shared host.

1. Setup your domain with [Passenger](https://help.dreamhost.com/hc/en-us/articles/215769578-Passenger-overview) support.
2. Login via [SSH](https://help.dreamhost.com/hc/en-us/articles/216041267) to your host.
3. Updrage pip:
```
python3 -m pip install --upgrade pip
```
4. Install virtualenv:
```
python3 -m pip install virtualenv
```
5. Go to your domain folder:
```
cd you.domain
```
6. Go to the public folder:
```
cd public
```
7. Create a python virtual enviroment:
```
$HOME/.local/bin/virtualenv venv
```
8. Activate the virtual env:
```
source venv/bin/activate
```
9. Install NOW - LMS:
```
pip install now_lms
```
10. Init app:
```
lmsctl setup
```
11. Crea a passenger_wsgi.py file:
```
import sys, os

INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "public", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from now_lms import lms_app as application
```
11. Restart passenger:
```
touch tmp/restart.txt
```



