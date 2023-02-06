FROM registry.access.redhat.com/ubi9/ubi-minimal AS js
RUN microdnf install -y nodejs npm && microdnf clean all
WORKDIR /usr/app
COPY ./now_lms/static/package.json /usr/app/package.json 
RUN npm install

FROM registry.access.redhat.com/ubi9/ubi-minimal

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED = 1
ENV FLASK_ENV "production"

RUN microdnf install -y --nodocs --best --refresh python39 python3-pip python3-cryptography \
    && microdnf clean all

# Install dependencies in a layer
COPY requirements.txt /tmp/
RUN /usr/bin/python3.9 --version \
    && /usr/bin/python3.9 -m pip --no-cache-dir install -r /tmp/requirements.txt \
    && rm -rf /root/.cache/

# Copy and install app
COPY . /app
WORKDIR /app
RUN chmod +x docker-entry-point.sh

# Install nodejs modules in the final docker image    
COPY --from=js /usr/app/node_modules /app/now_lms/static/node_modules

RUN /usr/bin/python3.9 -m pip install -e . && /usr/bin/python3.9 -m pip list --format=columns

EXPOSE 8080
ENTRYPOINT [ "/bin/sh" ]
CMD [ "/app/docker-entry-point.sh" ]
