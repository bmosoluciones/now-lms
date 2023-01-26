# Reference:
# - https://www.brettsbeta.com/blog/2020/07/flask-on-dreamhost-shared-website-hosting/

import sys, os

INTERP = os.path.join(os.environ["HOME"], "yourdomain.com", "public", "venv", "bin", "python3")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.append(os.getcwd())

from now_lms import lms_app as application
