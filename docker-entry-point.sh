#!/bin/sh

set -e

# Start Caddy in background
/usr/bin/caddy start --config /etc/caddy/Caddyfile --adapter caddyfile

# Ensure Python WSGI application runs on internal port 8000
export PORT=8000

# Use run.py which supports both Waitress and Gunicorn with shared configuration
# The Linux container defaults to Gunicorn; set WSGI_SERVER=waitress to use
# the cross-platform single-process server instead.
exec /usr/bin/python3.12 /app/run.py
