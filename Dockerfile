FROM registry.access.redhat.com/ubi9/ubi-minimal:9.2 AS js
RUN microdnf install -y nodejs npm
WORKDIR /usr/app
COPY ./now_lms/static/package.json /usr/app/package.json
RUN npm install --ignore-scripts

FROM registry.access.redhat.com/ubi9/ubi-minimal:9.2

# Copy app code
COPY . /app
# Install nodejs modules from de js image in the final docker image
COPY --from=js /usr/app/node_modules /app/now_lms/static/node_modules
# Dependency files
COPY requirements.txt /tmp/

WORKDIR /app

RUN microdnf install -y --nodocs --best --refresh python39 python3-pip python3-cryptography \
    && microdnf clean all \
    && /usr/bin/python3.9 --version \
    && chmod +x docker-entry-point.sh \
    && /usr/bin/python3.9 -m pip --no-cache-dir install -r /tmp/requirements.txt \
    && /usr/bin/python3.9 -m pip install --no-cache-dir -e . \
    && /usr/bin/python3.9 -m pip list --format=columns \
    && rm -rf /root/.cache/pip && rm -rf /tmp && dnf remove -y --best python3-pip \
    && ls -l /app/now_lms/static/node_modules \
    && ls -a

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
