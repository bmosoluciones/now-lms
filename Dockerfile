FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4 AS js
RUN microdnf install -y nodejs npm
WORKDIR /usr/app
COPY ./now_lms/static/package.json /usr/app/package.json
RUN npm install --ignore-scripts

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4

# Dependencies
COPY requirements.txt /tmp/
RUN microdnf install -y --nodocs --best --refresh python3.12 python3.12-pip python3.12-cryptography \
    && microdnf clean all \
    && /usr/bin/python3.12 --version \
    && /usr/bin/python3.12 -m pip --no-cache-dir install -r /tmp/requirements.txt \
    && /usr/bin/python3.12 -m pip list --format=columns \
    && rm -rf /root/.cache/pip && rm -rf /tmp && microdnf remove -y --best python3.12-pip

# App code
COPY . /app
WORKDIR /app
RUN chmod +x docker-entry-point.sh

# NodeJS modules
COPY --from=js /usr/app/node_modules /app/now_lms/static/node_modules

ENV FLASK_APP="now_lms"
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=0
ENV NOTLOGTOFILE=1

EXPOSE 8080

ENTRYPOINT [ "/bin/sh" ]

CMD [ "/app/docker-entry-point.sh" ]
