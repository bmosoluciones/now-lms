FROM registry.access.redhat.com/ubi8/ubi-minimal AS js
RUN rpm --import https://dl.yarnpkg.com/rpm/pubkey.gpg \
    && curl -sL https://dl.yarnpkg.com/rpm/yarn.repo -o /etc/yum.repos.d/yarn.repo \
    && microdnf -y install yarn
COPY package.json .
COPY yarn.lock .
RUN yarn

FROM registry.access.redhat.com/ubi8/ubi-minimal

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED = 1
ENV FLASK_ENV "production"

RUN microdnf install -y --nodocs --best --refresh python38 python38-pip python38-cryptography \
    && microdnf clean all

# Install dependencies in a layer
COPY requirements.txt /tmp/
RUN /usr/bin/python3.8 --version \
    && /usr/bin/python3.8 -m pip --no-cache-dir install -r /tmp/requirements.txt \
    && /usr/bin/python3.8 -m pip --no-cache-dir install pg8000 pymysql \
    && rm -rf /root/.cache/

# Copy and install app
COPY . /app
WORKDIR /app
RUN chmod +x docker-entry-point.sh

# Install nodejs modules in the final docker image    
COPY --from=js node_modules /app/now_lms/static/node_modules

RUN /usr/bin/python3.8 -m pip install -e .
RUN /usr/bin/python3.8 -m pip list --format=columns

EXPOSE 8080
ENTRYPOINT [ "/bin/sh" ]
CMD [ "/app/docker-entry-point.sh" ]
