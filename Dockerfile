FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4

ENV TINI_VERSION v0.19.0
ENV TINI_SUBREAPER=1
ENV FLASK_APP="now_lms"
ENV FLASK_DEBUG=0
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHON_DISABLE_REMOTE_DEBUG=1
ENV NOW_LMS_AUTO_MIGRATE=1
ENV WSGI_SERVER=gunicorn
ENV NOW_LMS_DATA_DIR=/app/data
ENV NOW_LMS_THEMES_DIR=/app/themes

WORKDIR /app

COPY ./now_lms/static/package.json /app/now_lms/static/package.json
COPY ./now_lms/static/package-lock.json /app/now_lms/static/package-lock.json
COPY requirements.lock /app/requirements.lock

RUN microdnf update -y --nodocs --best --refresh \
    && microdnf install -y --nodocs --best  nodejs npm pango python3.12 python3.12-pip python3.12-cryptography \
    && /usr/bin/python3.12 -m pip --no-cache-dir install --require-hashes -r /app/requirements.lock  \
    && cd /app/now_lms/static && npm ci --ignore-scripts \
    && rm -rf /root/.cache/pip && rm -rf /tmp \
    && microdnf remove -y --best python3.12-pip nodejs* npm \
    && microdnf clean all

COPY . /app

# Record exactly which commit produced this image, two ways: a file the app or an
# operator can read at runtime, and a label docker can query without starting a
# container. No default on purpose -- a build that forgets BUILD_SHA must FAIL
# rather than mint another unidentifiable image (that blind spot is how the July
# checkout/image/volume three-way drift happened; see fork issue #14).
ARG BUILD_SHA
RUN test -n "${BUILD_SHA}" && echo "${BUILD_SHA}" > /app/BUILD_SHA
LABEL io.intentsolutions.commit="${BUILD_SHA}"

RUN pybabel compile -d /app/now_lms/translations

ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini

RUN chmod +x docker-entry-point.sh && chmod +x /usr/bin/tini \
    && useradd -u 1001 -r -g 0 -d /app -s /sbin/nologin -c "App User" appuser

VOLUME ["/app/data", "/app/themes"]

EXPOSE 8080
USER 1001
ENTRYPOINT [ "/usr/bin/tini", "--", "/app/docker-entry-point.sh" ]
CMD ["/bin/sh"]
