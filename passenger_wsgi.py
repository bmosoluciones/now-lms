# Reference:
# - https://help.dreamhost.com/hc/en-us/articles/215769548-Passenger-and-Python-WSGI

import sys, os

INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "public", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from now_lms import lms_app as application
