# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 - 2026 BMO Soluciones, S.A.

# =======================================================================================
# Stage 1: Frontend - Build static assets and optimize node_modules
# =======================================================================================
FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4 AS frontend

RUN microdnf install -y --nodocs --best nodejs npm findutils \
    && microdnf clean all

WORKDIR /build

COPY now_lms/static/package.json now_lms/static/package-lock.json* ./now_lms/static/

RUN cd now_lms/static && npm ci --omit=dev --ignore-scripts --no-fund \
    && find node_modules -type d \( \
        -name "test" -o -name "tests" -o -name "doc" -o -name "docs" \
        -o -name "examples" -o -name "icons" -o -name "scss" -o -name "ts" \
    \) -exec rm -rf {} + \
    && find node_modules -type f \( \
        -name "*.md" -o -name "*.ts" -o -name "*.map" \
        -o -name "LICENSE" -o -name "README" -o -name "*.yml" -o -name "*.yaml" \
    \) -exec rm -f {} +

# =======================================================================================
# Stage 2: Python Builder - Install dependencies and remove unnecessary files
# =======================================================================================
FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4 AS python-builder

RUN microdnf install -y --nodocs --best --refresh \
       python3.12 python3.12-pip python3.12-cryptography findutils \
    && microdnf clean all

WORKDIR /build

COPY requirements.lock .

RUN /usr/bin/python3.12 -m pip --no-cache-dir install --require-hashes --prefix=/install -r requirements.lock \
    && find /install -type d \( \
        -name "test" -o -name "tests" -o -name "testing" \
        -o -name "benchmark" -o -name "benchmarks" -o -name "examples" \
        -o -name "__pycache__" \
    \) -exec rm -rf {} + \
    && find /install -type f \( \
        -name "*.pyc" -o -name "*.pyo" -o -name "*.pyd" -o -name "*.exe" \
        -o -name "*.md" -o -name "README*" -o -name "LICENSE*" \
        -o -name "COPYING*" -o -name "CHANGELOG*" \
    \) -exec rm -f {} +

# =======================================================================================
# Stage 3: Caddy Server - Fetch Caddy binary
# =======================================================================================
FROM caddy:2-alpine AS caddy

# =======================================================================================
# Stage 4: Final Image - Production-ready environment
# =======================================================================================
FROM registry.access.redhat.com/ubi9/ubi-minimal:9.4

ENV TINI_VERSION=v0.19.0
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

RUN microdnf update -y --nodocs --best --refresh \
    && microdnf install -y --nodocs --best pango python3.12 python3.12-cryptography \
    && microdnf clean all

# Copy python packages and binaries from python-builder stage
COPY --from=python-builder /install/lib/python3.12/site-packages /usr/lib/python3.12/site-packages
COPY --from=python-builder /install/lib64/python3.12/site-packages /usr/lib64/python3.12/site-packages
COPY --from=python-builder /install/bin /usr/local/bin

# Copy caddy binary from caddy stage
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

WORKDIR /app

# Copy the application source code
COPY . /app

# Copy optimized node_modules from frontend stage
COPY --from=frontend /build/now_lms/static/node_modules /app/now_lms/static/node_modules

# Copy Caddy configuration file
COPY now_lms/config/Caddyfile /etc/caddy/Caddyfile

# Record exactly which commit produced this image, two ways: a file the app or an
# operator can read at runtime, and a label docker can query without starting a
# container. No default on purpose -- a build that forgets BUILD_SHA must FAIL
# rather than mint another unidentifiable image (that blind spot is how the July
# checkout/image/volume three-way drift happened; see fork issue #14).
ARG BUILD_SHA
RUN test -n "${BUILD_SHA}" && echo "${BUILD_SHA}" > /app/BUILD_SHA
LABEL io.intentsolutions.commit="${BUILD_SHA}"

# Compile application translations. The freshness gate catches stale .mo
# files (root-cause fix for the demo 'Gender rendered in Spanish' bug class)
# and fails the build if any locale's catalog cannot resolve its sentinels.
# /usr/bin/python3.12 explicitly: this image installs python3.12 only (see the
# microdnf lines above) and provides NO bare `python` on PATH, so the upstream
# form of this gate exits 127 and fails the build. CI runners do have `python`,
# which is why this passed every check and only broke at image build time.
RUN pybabel compile -d /app/now_lms/translations \
    && /usr/bin/python3.12 -m now_lms.i18n_autocompile --check

# Add Tini for process reaping
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini

RUN chmod +x docker-entry-point.sh && chmod +x /usr/bin/tini \
    && useradd -u 1001 -r -g 0 -d /app -s /sbin/nologin -c "App User" appuser

VOLUME ["/app/data", "/app/themes"]

EXPOSE 8080
USER 1001
ENTRYPOINT [ "/usr/bin/tini", "--", "/app/docker-entry-point.sh" ]
CMD ["/bin/sh"]
