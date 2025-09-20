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
ENV NOW_LMS_DATA_DIR=/app/data
ENV NOW_LMS_THEMES_DIR=/app/themes

WORKDIR /app

COPY ./now_lms/static/package.json /app/now_lms/static/package.json
COPY requirements.txt /app/requirements.txt

RUN microdnf update -y --nodocs --best --refresh \
    && microdnf install -y --nodocs --best  nodejs npm pango python3.12 python3.12-pip python3.12-cryptography \
    && /usr/bin/python3.12 -m pip --no-cache-dir install -r /app/requirements.txt  \
    && /usr/bin/python3.12 -m pip --no-cache-dir install mysql-connector-python \
    && cd /app/now_lms/static && npm install --ignore-scripts \
    && rm -rf /root/.cache/pip && rm -rf /tmp \
    && microdnf remove -y --best python3.12-pip nodejs* npm \
    && microdnf clean all \
    && pybabel compile -d now_lms/translations

COPY . /app
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini

RUN chmod +x docker-entry-point.sh && chmod +x /usr/bin/tini

VOLUME ["/app/data", "/app/themes"]

EXPOSE 8080
ENTRYPOINT [ "/usr/bin/tini", "--", "/app/docker-entry-point.sh" ]
CMD ["/bin/sh"]
