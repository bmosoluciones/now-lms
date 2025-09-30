#!/bin/sh

set -e

exec /usr/bin/python3.12 -m gunicorn --bind 0.0.0.0:8080 --workers 4 --worker-class sync --timeout 120 --access-logfile - --error-logfile - "now_lms:create_app()"
