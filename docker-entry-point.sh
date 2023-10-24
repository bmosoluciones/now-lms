#!/bin/sh
set -e

/usr/bin/python3.9 -m flask db upgrade
/usr/bin/python3.9 -m now_lms
