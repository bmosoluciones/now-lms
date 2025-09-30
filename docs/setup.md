# Setup NOW-LMS

To run Now - LMS you need:

1. A WSGI server to execute the Python Code (Gunicorn is included by default).
2. A database backend.
3. A HTTP server, most of the times you will not want to expose your WSGI server to the wild.
4. An optional cache service like Redis or Memcached.

Now-LMS requires very low resources to run, a RaspberryPI can serve as an appropriate host, also a minimal VPS, a Shared Host service with support for Python 3.11 or greater and serverless services like Render, Heroku or similar.

Now-LMS is available as:

- [Source Code](https://github.com/bmosoluciones/now-lms).
- [Python Package](https://pypi.org/project/now-lms/).
- [OCI Image available](https://quay.io/repository/bmosoluciones/now_lms).
