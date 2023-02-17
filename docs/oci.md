# Install NOW - LMS with the OCI image.
[![Docker Repository on Quay](https://quay.io/repository/bmosoluciones/now_lms/status "Docker Repository on Quay")](https://quay.io/repository/bmosoluciones/now_lms)

## OCI Image

There is also a OCI image disponible if you prefer to user containers, in this example we use [podman](https://podman.io/):

```
# <---------------------------------------------> #
# Install the podman command line tool.
# DNF family (CentOS, Rocky, Alma):
sudo dnf -y install podman

# APT family (Debian, Ubuntu):
sudo apt install -y podman

# OpenSUSE:
sudo zypper in podman


# <---------------------------------------------> #
# Run the software.
# Create a new pod:
podman pod create --name now-lms -p 80:80 -p 443:443

# Database:
podman run --pod now-lms --rm --name now-lms-db --volume now-lms-postgresql-backup:/var/lib/postgresql/data -e POSTGRES_DB=nowlearning -e POSTGRES_USER=nowlearning -e POSTGRES_PASSWORD=nowlearning -d postgres:13

# App:
podman run --pod now-lms --rm --name now-lms-app -e LMS_KEY=nsjksldknsdlkdsljdnsdjñasññqldñaas554dlkallas -e LMS_DB=postgresql+pg8000://nowlearning:nowlearning@localhost:5432/nowlearning -e LMS_USER=administrator -e LMS_PSWD=administrator -d quay.io/bmosoluciones/now-lms

# Web Server
# Download nginx configuration template:
cd
mkdir now_lms_dir
cd now_lms_dir
curl -O https://raw.githubusercontent.com/bmosoluciones/now-lms/main/docs/nginx.conf

# In the same directoy run the web server pod:
podman run --pod now-lms --name now-lms-server --rm -v $PWD/nginx.conf:/etc/nginx/nginx.conf:ro -d nginx:stable

```

NOW-LMS also will work with MySQL or MariaDB just change the image of the database container and set the correct connect string. SQLite also will work if you will serve a few users.
