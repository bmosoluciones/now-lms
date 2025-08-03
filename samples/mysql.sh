podman pod create --replace --name now-lms-mysql -p 9999:80 -p 9443:443 -p 9443:443/udp

podman volume create --ignore now-lms-mysql-backup

podman run --pod now-lms-mysql --rm --replace --init --name now-lms-mysql-db \
    --volume now-lms-mysql-backup:/var/lib/mysql  \
    -e MYSQL_ROOT_PASSWORD=nowlearningdb \
    -e MYSQL_DATABASE=nowlearningdb \
    -e MYSQL_USER=nowlearningdb \
    -e MYSQL_PASSWORD=nowlearningdb \
    -d docker.io/library/mysql:8

podman run --pod now-lms-mysql --rm --replace --init --name now-lms-mysql-server \
    -v ./Caddyfile:/etc/caddy/Caddyfile:z \
    -v caddy_data:/data \
    -v caddy_config:/config \
    -d docker.io/library/caddy:alpine

podman run --pod now-lms-mysql --rm --replace --init --name now-lms-mysql-app \
    -e SECRET_KEY=nsjksAAA.ldknsdlkd532445yrVBNyrgfhdyyreys+++++ljdn \
    -e DATABASE_URL=mysql+pymysql://nowlearningdb:nowlearningdb@localhost:3306/nowlearningdb \
    -e LMS_USER=nowlmsadmin \
    -e LMS_PSWD=nowlmsadmin \
    -d quay.io/bmosoluciones/now_lms:main
