# Ubuntu/Debian Server Administration Best Practices

This comprehensive guide provides practical examples and best practices for administering Ubuntu and Debian-based servers hosting NOW Learning Management System.

## Table of Contents

1. [Initial Server Setup](#initial-server-setup)
2. [User & Access Management](#user--access-management)
3. [System Updates & Software Management](#system-updates--software-management)
4. [Security Hardening](#security-hardening)
5. [Network Configuration & Firewall](#network-configuration--firewall)
6. [Remote Access & Monitoring](#remote-access--monitoring)
7. [Backup & Recovery](#backup--recovery)
8. [Performance & Reliability](#performance--reliability)
9. [Database Management](#database-management)
10. [Web Server Configuration](#web-server-configuration)
11. [Virtualization & Containers](#virtualization--containers)
12. [Compliance & Documentation](#compliance--documentation)
13. [Troubleshooting](#troubleshooting)

---

## Initial Server Setup

### Update the System

Always start with a fully updated system:

```bash
# Update package lists and upgrade installed packages
sudo apt update && sudo apt upgrade -y

# Reboot if kernel was updated
sudo reboot

# Install essential packages
sudo apt install -y curl wget git vim htop tree unzip software-properties-common
```

### Set the Hostname

```bash
# Set a meaningful hostname
sudo hostnamectl set-hostname your-lms-server

# Update /etc/hosts
echo "127.0.0.1 your-lms-server" | sudo tee -a /etc/hosts
```

### Configure Timezone

```bash
# Set timezone
sudo timedatectl set-timezone America/New_York

# Verify timezone setting
timedatectl status
```

---

## User & Access Management

### Create a Non-Root Administrative User

Never use root directly for daily operations:

```bash
# Create a new user with home directory
sudo adduser lmsadmin

# Add user to sudo group
sudo usermod -aG sudo lmsadmin

# Verify sudo access
sudo -l -U lmsadmin
```

### Configure SSH Key-Based Authentication

```bash
# Generate SSH key pair (on your local machine)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to server (on your local machine)
ssh-copy-id lmsadmin@your-server-ip

# Or manually add the key
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "your-public-key-here" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Secure SSH Configuration

```bash
# Backup original SSH configuration
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH configuration
sudo nano /etc/ssh/sshd_config
```

Apply these secure SSH settings:

```bash
# /etc/ssh/sshd_config
Port 2222                          # Change default port
PermitRootLogin no                  # Disable root login
PasswordAuthentication no           # Force key-based auth
PubkeyAuthentication yes            # Enable key authentication
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3                      # Limit login attempts
ClientAliveInterval 300             # Keep connections alive
ClientAliveCountMax 2               # Disconnect idle clients
AllowUsers lmsadmin                 # Restrict allowed users
Protocol 2                          # Use SSH protocol 2
X11Forwarding no                    # Disable X11 forwarding
UsePAM yes                          # Use PAM for authentication
```

Restart SSH service:

```bash
sudo systemctl restart sshd
sudo systemctl status sshd
```

### Configure Fail2Ban for Brute Force Protection

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Create custom configuration
sudo nano /etc/fail2ban/jail.local
```

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
```

```bash
# Enable and start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Check status
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

---

## System Updates & Software Management

### Configure Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt install -y unattended-upgrades

# Configure automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

Edit unattended-upgrades configuration:

```bash
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

```bash
# /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "admin@yourdomain.com";
```

### Package Management Best Practices

```bash
# Clean package cache regularly
sudo apt autoremove -y
sudo apt autoclean

# Remove unnecessary packages
sudo apt list --installed | grep -v "\[installed\]"
sudo apt remove package-name

# Pin critical packages to prevent unwanted updates
echo "Package: nginx\nPin: version 1.18.*\nPin-Priority: 1001" | sudo tee /etc/apt/preferences.d/nginx

# Verify package integrity
sudo apt check
```

---

## Security Hardening

### Configure AppArmor

AppArmor is Ubuntu's mandatory access control system:

```bash
# Check AppArmor status
sudo aa-status

# Install additional profiles
sudo apt install -y apparmor-profiles apparmor-utils

# Enable AppArmor profile for applications
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx
sudo aa-enforce /etc/apparmor.d/usr.bin.python3

# Create custom profile for NOW-LMS
sudo aa-genprof /usr/local/bin/lmsctl
```

### Configure Firewall with UFW

```bash
# Enable UFW firewall
sudo ufw enable

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential services
sudo ufw allow 2222/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow specific IP ranges (replace with your IP)
sudo ufw allow from 192.168.1.0/24 to any port 2222

# Check firewall status
sudo ufw status verbose
```

### Kernel Security Settings

```bash
# Configure kernel security parameters
sudo nano /etc/sysctl.d/99-security.conf
```

```bash
# /etc/sysctl.d/99-security.conf
# IP Spoofing protection
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1

# Ignore ping requests
net.ipv4.icmp_echo_ignore_all = 1

# Ignore Directed pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Hide kernel pointers
kernel.kptr_restrict = 1

# Restrict dmesg access
kernel.dmesg_restrict = 1
```

Apply settings:

```bash
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

### File System Security

```bash
# Set up secure mount options in /etc/fstab
sudo nano /etc/fstab
```

Add security options:

```bash
# Example secure mount options
/dev/sda1 /tmp ext4 defaults,nodev,nosuid,noexec 0 2
/dev/sda2 /var ext4 defaults,nodev 0 2
/dev/sda3 /var/log ext4 defaults,nodev,nosuid,noexec 0 2
```

### Implement Disk Encryption

```bash
# For new installations, use LUKS encryption
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup luksOpen /dev/sdb encrypted-disk
sudo mkfs.ext4 /dev/mapper/encrypted-disk

# Mount encrypted partition
sudo mkdir /mnt/encrypted
sudo mount /dev/mapper/encrypted-disk /mnt/encrypted
```

---

## Network Configuration & Firewall

### Advanced UFW Configuration

```bash
# Rate limiting for SSH
sudo ufw limit 2222/tcp

# Allow from specific networks only
sudo ufw allow from 10.0.0.0/8
sudo ufw allow from 172.16.0.0/12
sudo ufw allow from 192.168.0.0/16

# Block specific countries (requires geoip-database)
sudo apt install -y geoip-database
sudo ufw deny from geoip:CN
sudo ufw deny from geoip:RU

# Application-specific rules
sudo ufw app list
sudo ufw allow "Nginx Full"
sudo ufw allow "OpenSSH"
```

### Configure Network Security

```bash
# Disable unused network protocols
echo "install dccp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install sctp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install rds /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install tipc /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf

# Configure TCP wrappers
echo "sshd: ALL" | sudo tee -a /etc/hosts.deny
echo "sshd: 192.168.1.0/24" | sudo tee -a /etc/hosts.allow
```

---

## Remote Access & Monitoring

### Install and Configure Cockpit

```bash
# Install Cockpit for web-based administration
sudo apt install -y cockpit

# Enable and start Cockpit
sudo systemctl enable --now cockpit.socket

# Allow Cockpit through firewall
sudo ufw allow 9090/tcp comment 'Cockpit Web Console'

# Access via https://your-server:9090
```

### System Monitoring Tools

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs glances

# Install netdata for real-time monitoring
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Configure netdata
sudo nano /etc/netdata/netdata.conf
```

```ini
# /etc/netdata/netdata.conf
[global]
    run as user = netdata
    default port = 19999
    bind to = 127.0.0.1

[web]
    allow connections from = localhost 192.168.1.*
```

### Centralized Logging

```bash
# Configure rsyslog for centralized logging
sudo nano /etc/rsyslog.d/50-default.conf

# Install logrotate
sudo apt install -y logrotate

# Configure log rotation
sudo nano /etc/logrotate.d/nowlms
```

```bash
# /etc/logrotate.d/nowlms
/var/log/nowlms/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
```

### Set Up Alerting

```bash
# Install and configure postfix for email alerts
sudo apt install -y postfix mailutils

# Configure system monitoring with email alerts
sudo nano /etc/cron.d/system-monitoring
```

```bash
# /etc/cron.d/system-monitoring
# Check disk space every hour
0 * * * * root df -h | awk '$5 > 80 {print $0}' | mail -s "Disk space warning on $(hostname)" admin@example.com

# Check memory usage every 30 minutes
*/30 * * * * root free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }' | mail -s "Memory report $(hostname)" admin@example.com

# Check service status every 5 minutes
*/5 * * * * root systemctl is-active nginx >/dev/null || echo "Nginx is down" | mail -s "Service Alert: Nginx down on $(hostname)" admin@example.com
```

---

## Backup & Recovery

### Automated Backup Strategy

```bash
# Install backup tools
sudo apt install -y rsync borgbackup duplicity

# Create backup directories
sudo mkdir -p /backup/{daily,weekly,monthly}
sudo mkdir -p /backup/scripts

# Database backup script
sudo nano /backup/scripts/db-backup.sh
```

```bash
#!/bin/bash
# /backup/scripts/db-backup.sh

BACKUP_DIR="/backup/daily"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="nowlms"
DB_USER="nowlms_user"

# PostgreSQL backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/nowlms_db_$DATE.sql.gz

# MySQL backup (alternative)
# mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/nowlms_db_$DATE.sql.gz

# SQLite backup (if using SQLite)
# cp /path/to/nowlms.db $BACKUP_DIR/nowlms_db_$DATE.db

# Remove backups older than 7 days
find $BACKUP_DIR -name "nowlms_db_*.sql.gz" -mtime +7 -delete

echo "Database backup completed: $DATE"
```

### File System Backup

```bash
# System backup script
sudo nano /backup/scripts/system-backup.sh
```

```bash
#!/bin/bash
# /backup/scripts/system-backup.sh

BACKUP_DIR="/backup/daily"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIRS="/etc /home /var/www /opt"
EXCLUDE_FILE="/backup/scripts/exclude.txt"

# Create exclude file
cat > $EXCLUDE_FILE << EOF
/proc/*
/sys/*
/dev/*
/tmp/*
/var/tmp/*
/var/cache/*
/var/log/*
/home/*/.cache/*
/root/.cache/*
EOF

# Create system backup
tar -czf $BACKUP_DIR/system_backup_$DATE.tar.gz \
    --exclude-from=$EXCLUDE_FILE \
    $SOURCE_DIRS

# NOW-LMS specific backup
tar -czf $BACKUP_DIR/nowlms_files_$DATE.tar.gz \
    /var/lib/nowlms \
    /etc/nowlms \
    /opt/nowlms

# Remove old backups
find $BACKUP_DIR -name "system_backup_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "nowlms_files_*.tar.gz" -mtime +7 -delete

echo "System backup completed: $DATE"
```

### BorgBackup Configuration

```bash
# Initialize borg repository
sudo borg init --encryption=repokey /backup/borg-repo

# Create borg backup script
sudo nano /backup/scripts/borg-backup.sh
```

```bash
#!/bin/bash
# /backup/scripts/borg-backup.sh

export BORG_REPO='/backup/borg-repo'
export BORG_PASSPHRASE='your-secure-passphrase'

# Backup directories
borg create \
    --verbose \
    --filter AME \
    --list \
    --stats \
    --show-rc \
    --compression lz4 \
    --exclude-caches \
    --exclude '/home/*/.cache' \
    --exclude '/var/cache' \
    --exclude '/var/tmp' \
    ::'{hostname}-{now}' \
    /etc \
    /home \
    /var/lib/nowlms \
    /opt/nowlms

# Prune old archives
borg prune \
    --list \
    --prefix '{hostname}-' \
    --show-rc \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 6

echo "Borg backup completed"
```

### Schedule Backups

```bash
# Make scripts executable
sudo chmod +x /backup/scripts/*.sh

# Add to crontab
sudo crontab -e
```

```bash
# Backup schedule
0 2 * * * /backup/scripts/db-backup.sh >> /var/log/backup.log 2>&1
30 2 * * * /backup/scripts/system-backup.sh >> /var/log/backup.log 2>&1
0 3 * * 0 /backup/scripts/borg-backup.sh >> /var/log/backup.log 2>&1

# Weekly full system backup
0 4 * * 0 rsync -av --delete /home/ /backup/weekly/home/
0 5 * * 0 rsync -av --delete /etc/ /backup/weekly/etc/
```

---

## Performance & Reliability

### Optimize System Performance

```bash
# Configure swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize swap usage
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
```

### Configure systemd Services

```bash
# Create NOW-LMS systemd service
sudo nano /etc/systemd/system/nowlms.service
```

```ini
# /etc/systemd/system/nowlms.service
[Unit]
Description=NOW Learning Management System
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/nowlms
Environment=FLASK_APP=now_lms
Environment=SECRET_KEY=your-very-secure-secret-key
Environment=DATABASE_URL=postgresql://user:pass@localhost/nowlms
ExecStart=/opt/nowlms/venv/bin/lmsctl serve
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nowlms
sudo systemctl start nowlms
sudo systemctl status nowlms
```

### Disk Health Monitoring

```bash
# Install smartmontools
sudo apt install -y smartmontools

# Check disk health
sudo smartctl -a /dev/sda

# Schedule regular SMART tests
sudo nano /etc/cron.d/smartmon
```

```bash
# /etc/cron.d/smartmon
# Short test every week
0 2 * * 1 root /usr/sbin/smartctl -t short /dev/sda

# Long test every month
0 3 1 * * root /usr/sbin/smartctl -t long /dev/sda

# Check results
0 4 * * 2 root /usr/sbin/smartctl -l selftest /dev/sda | mail -s "SMART test results $(hostname)" admin@example.com
```

---

## Database Management

### PostgreSQL Setup and Hardening

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Create database and user for NOW-LMS
sudo -u postgres psql
```

```sql
-- PostgreSQL commands
CREATE USER nowlms_user WITH PASSWORD 'secure_password_here';
CREATE DATABASE nowlms_db OWNER nowlms_user;
GRANT ALL PRIVILEGES ON DATABASE nowlms_db TO nowlms_user;
\q
```

```bash
# Configure PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```bash
# /etc/postgresql/14/main/postgresql.conf
listen_addresses = 'localhost'
port = 5432
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

```bash
# Configure authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

```bash
# /etc/postgresql/14/main/pg_hba.conf
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

```bash
# Restart PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### MySQL/MariaDB Setup (Alternative)

```bash
# Install MySQL
sudo apt install -y mysql-server

# Secure MySQL installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
-- MySQL commands
CREATE DATABASE nowlms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nowlms_user'@'localhost' IDENTIFIED BY 'secure_password_here';
GRANT ALL PRIVILEGES ON nowlms_db.* TO 'nowlms_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## Web Server Configuration

### Nginx Setup and Hardening

```bash
# Install Nginx
sudo apt install -y nginx

# Create NOW-LMS site configuration
sudo nano /etc/nginx/sites-available/nowlms
```

```nginx
# /etc/nginx/sites-available/nowlms
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_cache shared:SSL:1m;
    ssl_session_timeout 5m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root directory
    root /var/www/html;
    index index.html index.htm;

    # NOW-LMS proxy
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/nowlms/now_lms/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security
    location ~ /\. {
        deny all;
    }

    # Logging
    access_log /var/log/nginx/nowlms_access.log;
    error_log /var/log/nginx/nowlms_error.log;
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/nowlms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up automatic renewal
sudo crontab -e
```

```bash
# Auto-renew SSL certificates
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## Virtualization & Containers

### Docker Setup for NOW-LMS

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### NOW-LMS Docker Compose Configuration

```bash
# Create docker-compose.yml
mkdir -p /opt/nowlms-docker
cd /opt/nowlms-docker
nano docker-compose.yml
```

```yaml
# docker-compose.yml
version: "3.8"

services:
    nowlms:
        image: quay.io/bmosoluciones/now_lms:latest
        container_name: nowlms-app
        restart: unless-stopped
        ports:
            - "127.0.0.1:8080:8080"
        environment:
            - SECRET_KEY=your-very-secure-secret-key
            - DATABASE_URL=postgresql://nowlms:password@postgres:5432/nowlms
            - REDIS_URL=redis://redis:6379/0
        volumes:
            - nowlms-data:/app/data
            - nowlms-themes:/app/themes
        depends_on:
            - postgres
            - redis

    postgres:
        image: postgres:15
        container_name: nowlms-postgres
        restart: unless-stopped
        environment:
            - POSTGRES_DB=nowlms
            - POSTGRES_USER=nowlms
            - POSTGRES_PASSWORD=secure_password_here
        volumes:
            - postgres-data:/var/lib/postgresql/data
        ports:
            - "127.0.0.1:5432:5432"

    redis:
        image: redis:7-alpine
        container_name: nowlms-redis
        restart: unless-stopped
        volumes:
            - redis-data:/data

volumes:
    nowlms-data:
    nowlms-themes:
    postgres-data:
    redis-data:
```

```bash
# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs nowlms
```

---

## Compliance & Documentation

### CIS Benchmark Implementation

```bash
# Install CIS benchmark tools
sudo apt install -y lynis

# Run security audit
sudo lynis audit system

# Install and run OpenSCAP (if available)
sudo apt install -y libopenscap8 ssg-debian

# Generate compliance report
sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_standard \
    --results-arf /tmp/arf.xml \
    --report /tmp/report.html \
    /usr/share/xml/scap/ssg/content/ssg-debian.xml
```

### Infrastructure as Code

```bash
# Install Ansible for configuration management
sudo apt install -y ansible

# Create Ansible playbook for NOW-LMS
mkdir -p /opt/ansible/playbooks
nano /opt/ansible/playbooks/nowlms.yml
```

```yaml
# /opt/ansible/playbooks/nowlms.yml
---
- name: Deploy NOW-LMS
  hosts: localhost
  become: yes
  vars:
      nowlms_user: www-data
      nowlms_dir: /opt/nowlms

  tasks:
      - name: Install dependencies
        apt:
            name:
                - python3
                - python3-pip
                - nginx
                - postgresql
            state: present
            update_cache: yes

      - name: Create NOW-LMS user
        user:
            name: "{{ nowlms_user }}"
            system: yes
            shell: /bin/false
            home: "{{ nowlms_dir }}"

      - name: Install NOW-LMS
        pip:
            name: now-lms
            virtualenv: "{{ nowlms_dir }}/venv"
            virtualenv_python: python3

      - name: Configure systemd service
        template:
            src: nowlms.service.j2
            dest: /etc/systemd/system/nowlms.service
        notify: restart nowlms

  handlers:
      - name: restart nowlms
        systemd:
            name: nowlms
            state: restarted
            daemon_reload: yes
```

### Documentation and Change Management

```bash
# Set up Git repository for configuration management
mkdir -p /opt/config-management
cd /opt/config-management
git init

# Track important configuration files
mkdir -p {nginx,postgresql,systemd,scripts}
cp /etc/nginx/sites-available/nowlms nginx/
cp /etc/postgresql/*/main/postgresql.conf postgresql/
cp /etc/systemd/system/nowlms.service systemd/
cp -r /backup/scripts/* scripts/

# Commit initial configuration
git add .
git commit -m "Initial configuration backup"

# Create daily configuration backup script
nano /opt/config-management/backup-config.sh
```

```bash
#!/bin/bash
# /opt/config-management/backup-config.sh

cd /opt/config-management

# Copy current configurations
cp /etc/nginx/sites-available/nowlms nginx/
cp /etc/postgresql/*/main/postgresql.conf postgresql/
cp /etc/systemd/system/nowlms.service systemd/
cp -r /backup/scripts/* scripts/

# Check for changes
if [[ -n $(git status --porcelain) ]]; then
    git add .
    git commit -m "Configuration backup - $(date)"
    echo "Configuration changes detected and committed"
else
    echo "No configuration changes detected"
fi
```

```bash
# Schedule daily config backup
echo "0 1 * * * /opt/config-management/backup-config.sh >> /var/log/config-backup.log 2>&1" | sudo crontab -e
```

---

## Troubleshooting

### Common Issues and Solutions

#### Service Issues

```bash
# Check service status
sudo systemctl status nowlms
sudo systemctl status nginx
sudo systemctl status postgresql

# View service logs
sudo journalctl -u nowlms -f
sudo journalctl -u nginx -f

# Restart services
sudo systemctl restart nowlms
sudo systemctl reload nginx
```

#### Database Issues

```bash
# Check PostgreSQL connection
sudo -u postgres psql -l

# Test database connectivity
sudo -u postgres psql -d nowlms_db -c "SELECT version();"

# Monitor database performance
sudo -u postgres psql -d nowlms_db -c "SELECT * FROM pg_stat_activity;"
```

#### Network Issues

```bash
# Check open ports
sudo netstat -tulpn
sudo ss -tulpn

# Test connectivity
curl -I http://localhost:8080
curl -I https://your-domain.com

# Check DNS resolution
nslookup your-domain.com
dig your-domain.com
```

#### Performance Issues

```bash
# Monitor system resources
htop
iotop
netstat -i

# Check disk usage
df -h
du -sh /var/*

# Monitor network traffic
nethogs
iftop
```

### Log Analysis

```bash
# Search for errors in logs
sudo grep -i error /var/log/nginx/error.log
sudo grep -i error /var/log/syslog
sudo journalctl -p err -n 50

# Analyze access patterns
sudo tail -f /var/log/nginx/access.log | grep -v "bot\|crawler"

# Monitor failed login attempts
sudo grep "Failed password" /var/log/auth.log | tail -20
```

### Emergency Procedures

```bash
# Emergency system information
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8080

# Kill runaway processes
sudo pkill -f python
sudo systemctl stop nowlms

# Emergency disk cleanup
sudo apt autoremove -y
sudo apt autoclean
sudo find /var/log -name "*.log" -mtime +30 -delete
sudo find /tmp -mtime +7 -delete
```

---

## Security Checklist

Use this checklist to ensure your Ubuntu/Debian server follows security best practices:

- [ ] System fully updated with automatic security updates enabled
- [ ] Non-root administrative user created with sudo privileges
- [ ] SSH hardened with key-based authentication and non-default port
- [ ] Root login disabled
- [ ] Fail2ban configured and active
- [ ] UFW firewall enabled with minimal required ports
- [ ] AppArmor profiles enabled for critical services
- [ ] Kernel security parameters configured
- [ ] Unattended upgrades configured for security updates
- [ ] Regular backups scheduled and tested
- [ ] SSL/TLS certificates configured and auto-renewing
- [ ] System monitoring and alerting configured
- [ ] Log rotation and retention configured
- [ ] Database properly secured and backed up
- [ ] Web server hardened with security headers
- [ ] Regular security audits scheduled
- [ ] Configuration changes tracked in version control
- [ ] Documentation kept up to date

This comprehensive guide provides a solid foundation for securely administering Ubuntu and Debian servers running NOW Learning Management System. Regular review and updates of these practices are essential for maintaining security and reliability.
