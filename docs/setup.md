# Setup NOW-LMS

To run Now - LMS you need:

1. A SWGI server to execute the Python Code.
2. A database backend.
3. A HTTP server, most of the times you will no want to expose your SWGI server to the wild.
4. A optional cache service like Redis or Memcached.

Now -LMS requires very low resources to run, a RaspberryPI can serve as a apropiate host, also a minimal VPS, a Shared Host service with support for Python 3.8 or greatter and serverless services like Render, Heroko or similar.

Now-LMS is available as:

-   [Source Code](https://github.com/bmosoluciones/now-lms).
-   [Python Package](https://pypi.org/project/now-lms/).
-   [OCI Image available](https://quay.io/repository/bmosoluciones/now_lms).
