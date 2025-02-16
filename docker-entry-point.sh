#!/bin/sh

set -e

FLASK_APP=now_lms /usr/bin/python3.12 -m flask setup
FLASK_APP=now_lms /usr/bin/python3.12 -m flask serve
