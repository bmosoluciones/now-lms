podman pod create --replace --name now-lms-psql -p 8888:80 -p 9444:443 -p 9444:443/udp

podman volume create --ignore now-lms-psql-backup

podman run --pod now-lms-psql --rm --replace --init --name now-lms-psql-db \
    --volume now-lms-psql-backup:/var/lib/postgresql/data \
    -e POSTGRES_DB=nowlearningdb \
    -e POSTGRES_USER=nowlearningdb \
    -e POSTGRES_PASSWORD=nowlearningdb \
    -d docker.io/library/postgres:17-alpine

podman run --pod now-lms-psql --rm --replace --init --name now-lms-psql-server \
    -v ./Caddyfile:/etc/caddy/Caddyfile:z \
    -v caddy_pg_data:/data \
    -v caddy_pg_config:/config \
    -d docker.io/library/caddy:alpine

podman run --pod now-lms-psql --rm --replace --init --name now-lms-psql-app \
    -e SECRET_KEY=nsjksAAA.ldknsdlkd532445yrVBNyrgfhdyyreys+++++ljdn \
    -e DATABASE_URL=postgresql+pg8000://nowlearningdb:nowlearningdb@localhost:5432/nowlearningdb \
    -e LMS_USER=nowlmsadmin \
    -e LMS_PSWD=nowlmsadmin \
    -d quay.io/bmosoluciones/now_lms:main
