#!/bin/sh

set -e

# Use run.py which supports both Waitress and Gunicorn with shared configuration
# Defaults to Waitress (cross-platform, included in requirements.txt)
# Set WSGI_SERVER=gunicorn to use Gunicorn instead (requires gunicorn in requirements.txt)
exec /usr/bin/python3.12 /app/run.py
