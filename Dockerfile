FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4 AS js
RUN microdnf install -y nodejs npm
WORKDIR /usr/app
COPY ./now_lms/static/package.json /usr/app/package.json
RUN npm install --ignore-scripts

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4

COPY requirements.txt /tmp/

RUN microdnf update -y --nodocs --best \
    && microdnf install -y --nodocs --best --refresh python3.12 python3.12-pip python3.12-cryptography \
    && microdnf clean all \
    && /usr/bin/python3.12 --version \
    && /usr/bin/python3.12 -m pip --no-cache-dir install -r /tmp/requirements.txt \
    && rm -rf /root/.cache/pip && rm -rf /tmp && microdnf remove -y --best python3.12-pip \
    && microdnf clean all

COPY . /app
WORKDIR /app

COPY --from=js /usr/app/node_modules /app/now_lms/static/node_modules

RUN chmod +x docker-entry-point.sh

ENV FLASK_APP="now_lms"
ENV FLASK_DEBUG=0

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
ENTRYPOINT [ "/bin/sh" ]
CMD [ "/app/docker-entry-point.sh" ]
