#!/bin/sh

set -e

# Use run.py which supports both Waitress and Gunicorn with shared configuration
# The Linux container defaults to Gunicorn; set WSGI_SERVER=waitress to use
# the cross-platform single-process server instead.
exec /usr/bin/python3.12 /app/run.py
