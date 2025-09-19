# RHEL/Alma/Rocky/Amazon/Fedora Server Administration Best Practices

This comprehensive guide provides practical examples and best practices for administering RHEL-based servers (Red Hat Enterprise Linux, AlmaLinux, Rocky Linux, Amazon Linux, and Fedora) hosting NOW Learning Management System.

## Table of Contents

1. [Initial Server Setup](#initial-server-setup)
2. [User & Access Management](#user--access-management)
3. [System Updates & Software Management](#system-updates--software-management)
4. [Security Hardening with SELinux](#security-hardening-with-selinux)
5. [Network Configuration & Firewalld](#network-configuration--firewalld)
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
# For RHEL/Alma/Rocky/CentOS
sudo dnf update -y

# For Amazon Linux 2
sudo yum update -y

# For Fedora
sudo dnf update -y

# Reboot if kernel was updated
sudo reboot

# Install essential packages
sudo dnf install -y curl wget git vim htop tree unzip epel-release
```

### Enable Additional Repositories

```bash
# Enable EPEL repository (Essential for additional packages)
sudo dnf install -y epel-release

# For Rocky/Alma Linux - enable PowerTools/CRB
sudo dnf config-manager --set-enabled powertools  # Rocky 8
sudo dnf config-manager --set-enabled crb         # Rocky 9/Alma 9

# For RHEL with subscription
sudo subscription-manager repos --enable=rhel-*-optional-rpms
sudo subscription-manager repos --enable=rhel-*-extras-rpms

# Install development tools
sudo dnf groupinstall -y "Development Tools"
```

### Set the Hostname and Timezone

```bash
# Set a meaningful hostname
sudo hostnamectl set-hostname your-lms-server.example.com

# Update /etc/hosts
echo "127.0.0.1 your-lms-server.example.com your-lms-server" | sudo tee -a /etc/hosts

# Set timezone
sudo timedatectl set-timezone America/New_York

# Verify settings
hostnamectl status
timedatectl status
```

---

## User & Access Management

### Create a Non-Root Administrative User

Never use root directly for daily operations:

```bash
# Create a new user with home directory
sudo adduser lmsadmin

# Add user to wheel group (sudo equivalent in RHEL)
sudo usermod -aG wheel lmsadmin

# Verify sudo access
sudo -l -U lmsadmin
```

### Configure SSH Key-Based Authentication

```bash
# Generate SSH key pair (on your local machine)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to server (on your local machine)
ssh-copy-id lmsadmin@your-server-ip

# Or manually add the key on the server
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

# Allow new SSH port through firewall
sudo firewall-cmd --permanent --add-port=2222/tcp
sudo firewall-cmd --reload
```

### Configure Fail2Ban for Brute Force Protection

```bash
# Install fail2ban
sudo dnf install -y fail2ban

# Create custom configuration
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
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
logpath = /var/log/secure
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
# Install dnf-automatic
sudo dnf install -y dnf-automatic

# Configure automatic updates
sudo nano /etc/dnf/automatic.conf
```

```ini
# /etc/dnf/automatic.conf
[commands]
upgrade_type = security
random_sleep = 3600
network_online_timeout = 60
download_updates = yes
apply_updates = yes

[emitters]
emit_via = email
system_name = your-lms-server

[email]
email_from = admin@your-domain.com
email_to = admin@your-domain.com
email_host = localhost
```

```bash
# Enable and start automatic updates
sudo systemctl enable dnf-automatic.timer
sudo systemctl start dnf-automatic.timer
sudo systemctl status dnf-automatic.timer
```

### Package Management Best Practices

```bash
# Clean package cache regularly
sudo dnf autoremove -y
sudo dnf clean all

# List installed packages
sudo dnf list installed

# Remove unnecessary packages
sudo dnf remove package-name

# Lock package versions (prevent updates)
sudo dnf versionlock add package-name

# Check for security updates
sudo dnf updateinfo list security
sudo dnf update --security
```

### YUM/DNF Repository Management

```bash
# List enabled repositories
sudo dnf repolist

# Add custom repository
sudo nano /etc/yum.repos.d/custom.repo
```

```ini
# /etc/yum.repos.d/custom.repo
[custom-repo]
name=Custom Repository
baseurl=https://repo.example.com/el$releasever/
enabled=1
gpgcheck=1
gpgkey=https://repo.example.com/RPM-GPG-KEY
```

---

## Security Hardening with SELinux

### SELinux Configuration and Management

SELinux is the cornerstone of RHEL security:

```bash
# Check SELinux status
sudo sestatus
sudo getenforce

# Ensure SELinux is in enforcing mode
sudo setenforce 1
sudo sed -i 's/SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# Install SELinux management tools
sudo dnf install -y policycoreutils-python-utils setools-console setroubleshoot-server
```

### SELinux Context Management

```bash
# Check file contexts
ls -Z /var/www/html/
ps auxZ | grep nginx

# Set proper context for web files
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1

# Set context for NOW-LMS directory
sudo semanage fcontext -a -t httpd_exec_t "/opt/nowlms/venv/bin/lmsctl"
sudo restorecon -Rv /opt/nowlms/

# Create custom SELinux policy for NOW-LMS
sudo audit2allow -a -M nowlms_policy
sudo semodule -i nowlms_policy.pp
```

### SELinux Troubleshooting

```bash
# Monitor SELinux denials
sudo tail -f /var/log/audit/audit.log | grep AVC

# Use sealert for detailed analysis
sudo sealert -a /var/log/audit/audit.log

# Troubleshoot specific denials
sudo audit2why < /var/log/audit/audit.log

# Temporarily allow specific access (for testing only)
sudo audit2allow -a --enable
```

### Custom SELinux Policy for NOW-LMS

```bash
# Create NOW-LMS SELinux policy
sudo nano /tmp/nowlms.te
```

```selinux
# /tmp/nowlms.te
module nowlms 1.0;

require {
    type httpd_t;
    type httpd_exec_t;
    type httpd_tmp_t;
    type var_lib_t;
    type admin_home_t;
    class file { read write create open getattr execute };
    class dir { search read write add_name remove_name };
}

# Allow httpd to execute NOW-LMS
allow httpd_t httpd_exec_t:file execute;

# Allow NOW-LMS to access its data directory
allow httpd_t var_lib_t:dir { read write search add_name remove_name };
allow httpd_t var_lib_t:file { read write create open getattr };

# Allow access to temporary files
allow httpd_t httpd_tmp_t:file { read write create open getattr };
```

```bash
# Compile and install the policy
sudo checkmodule -M -m -o /tmp/nowlms.mod /tmp/nowlms.te
sudo semodule_package -o /tmp/nowlms.pp -m /tmp/nowlms.mod
sudo semodule -i /tmp/nowlms.pp
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

# Randomize memory layout
kernel.randomize_va_space = 2
```

Apply settings:

```bash
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

---

## Network Configuration & Firewalld

### Firewalld Configuration

Firewalld is the default firewall management tool in RHEL:

```bash
# Enable and start firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Check firewall status
sudo firewall-cmd --state
sudo firewall-cmd --list-all

# Set default zone
sudo firewall-cmd --set-default-zone=public

# Allow essential services
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Custom SSH port
sudo firewall-cmd --permanent --add-port=2222/tcp

# Remove default SSH service if using custom port
sudo firewall-cmd --permanent --remove-service=ssh

# Reload firewall
sudo firewall-cmd --reload
```

### Advanced Firewalld Configuration

```bash
# Create custom service definition
sudo nano /etc/firewalld/services/nowlms.xml
```

```xml
<!-- /etc/firewalld/services/nowlms.xml -->
<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>NOW-LMS</short>
  <description>NOW Learning Management System</description>
  <port protocol="tcp" port="8080"/>
</service>
```

```bash
# Reload and use custom service
sudo firewall-cmd --reload
sudo firewall-cmd --permanent --add-service=nowlms

# Rich rules for advanced access control
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" service name="ssh" accept'
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="0.0.0.0/0" service name="http" accept'

# Rate limiting
sudo firewall-cmd --permanent --add-rich-rule='rule service name="ssh" accept limit value="3/m"'

# Block specific IPs
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="1.2.3.4" drop'

# Apply changes
sudo firewall-cmd --reload
```

### Network Security

```bash
# Disable unused network protocols
echo "install dccp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install sctp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install rds /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf
echo "install tipc /bin/true" | sudo tee -a /etc/modprobe.d/blacklist-rare-network.conf

# Configure TCP wrappers (if installed)
echo "sshd: ALL" | sudo tee -a /etc/hosts.deny
echo "sshd: 192.168.1.0/255.255.255.0" | sudo tee -a /etc/hosts.allow
```

---

## Remote Access & Monitoring

### Install and Configure Cockpit

Cockpit is the default web console for RHEL systems:

```bash
# Install Cockpit (usually pre-installed)
sudo dnf install -y cockpit cockpit-system cockpit-selinux

# Enable and start Cockpit
sudo systemctl enable --now cockpit.socket

# Allow Cockpit through firewall
sudo firewall-cmd --permanent --add-service=cockpit
sudo firewall-cmd --reload

# Access via https://your-server:9090
```

### Configure Cockpit Security

```bash
# Configure Cockpit for secure access
sudo nano /etc/cockpit/cockpit.conf
```

```ini
# /etc/cockpit/cockpit.conf
[WebService]
LoginTitle = NOW-LMS Server Management
LoginTo = false
RequireHost = your-lms-server.example.com
MaxStartups = 3
AllowUnencrypted = false

[Session]
IdleTimeout = 15
Banner = /etc/cockpit/banner.txt
```

```bash
# Create login banner
sudo nano /etc/cockpit/banner.txt
```

```text
WARNING: Authorized access only. All activities are monitored and logged.
```

### System Monitoring Tools

```bash
# Install monitoring tools
sudo dnf install -y htop iotop nethogs glances

# Install and configure Netdata
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Configure Netdata
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
    allow dashboard from = localhost 192.168.1.*
    allow badges from = *
```

### Centralized Logging with rsyslog

```bash
# Configure rsyslog for centralized logging
sudo nano /etc/rsyslog.d/01-nowlms.conf
```

```bash
# /etc/rsyslog.d/01-nowlms.conf
# NOW-LMS application logs
if $programname == 'nowlms' then /var/log/nowlms/application.log
& stop

# Security logs
auth,authpriv.*                  /var/log/secure
mail.*                          /var/log/maillog
cron.*                          /var/log/cron

# Remote logging (optional)
# *.* @@remote-log-server:514
```

```bash
# Restart rsyslog
sudo systemctl restart rsyslog

# Configure logrotate for NOW-LMS logs
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
    create 0644 nowlms nowlms
    postrotate
        systemctl reload nowlms
    endscript
}
```

### Set Up Email Alerting

```bash
# Install and configure postfix
sudo dnf install -y postfix mailx

# Configure postfix for outbound mail
sudo nano /etc/postfix/main.cf
```

```bash
# /etc/postfix/main.cf - Key settings
myhostname = your-lms-server.example.com
mydomain = example.com
myorigin = $mydomain
inet_interfaces = localhost
mydestination = $myhostname, localhost.$mydomain, localhost
relayhost = [smtp.example.com]:587

# SMTP authentication (if required)
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt
```

```bash
# Start postfix
sudo systemctl enable --now postfix

# Create monitoring scripts
sudo mkdir -p /opt/monitoring
sudo nano /opt/monitoring/system-monitor.sh
```

```bash
#!/bin/bash
# /opt/monitoring/system-monitor.sh

HOSTNAME=$(hostname)
EMAIL="admin@example.com"

# Check disk space
DISK_USAGE=$(df -h | awk '$5 > 80 {print $0}')
if [ ! -z "$DISK_USAGE" ]; then
    echo "Disk space warning on $HOSTNAME: $DISK_USAGE" | mail -s "Disk Alert: $HOSTNAME" $EMAIL
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo "Memory usage is ${MEM_USAGE}% on $HOSTNAME" | mail -s "Memory Alert: $HOSTNAME" $EMAIL
fi

# Check service status
for service in nowlms nginx postgresql; do
    if ! systemctl is-active --quiet $service; then
        echo "Service $service is not running on $HOSTNAME" | mail -s "Service Alert: $HOSTNAME" $EMAIL
    fi
done

# Check SELinux denials
DENIALS=$(ausearch -m avc -ts recent 2>/dev/null | wc -l)
if [ $DENIALS -gt 0 ]; then
    echo "SELinux denials detected: $DENIALS" | mail -s "SELinux Alert: $HOSTNAME" $EMAIL
fi
```

```bash
# Make script executable and schedule
sudo chmod +x /opt/monitoring/system-monitor.sh
sudo crontab -e
```

```bash
# System monitoring cron jobs
*/15 * * * * /opt/monitoring/system-monitor.sh
0 6 * * * /bin/df -h | mail -s "Daily disk report $(hostname)" admin@example.com
0 7 * * * /bin/free -h | mail -s "Daily memory report $(hostname)" admin@example.com
```

---

## Backup & Recovery

### Automated Backup Strategy

```bash
# Install backup tools
sudo dnf install -y rsync borgbackup tar gzip

# Create backup directories
sudo mkdir -p /backup/{daily,weekly,monthly}
sudo mkdir -p /backup/scripts
sudo mkdir -p /var/lib/nowlms-backup

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
DB_PASS="your_password"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# PostgreSQL backup
export PGPASSWORD=$DB_PASS
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/nowlms_db_$DATE.sql.gz

# MySQL backup (alternative)
# mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/nowlms_db_$DATE.sql.gz

# SQLite backup (if using SQLite)
# cp /var/lib/nowlms/nowlms.db $BACKUP_DIR/nowlms_db_$DATE.db

# Remove backups older than 7 days
find $BACKUP_DIR -name "nowlms_db_*.sql.gz" -mtime +7 -delete

# Log backup completion
logger "Database backup completed: $DATE"
echo "Database backup completed: $DATE"
```

### System and Application Backup

```bash
# System backup script
sudo nano /backup/scripts/system-backup.sh
```

```bash
#!/bin/bash
# /backup/scripts/system-backup.sh

BACKUP_DIR="/backup/daily"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIRS="/etc /home /var/lib/nowlms /opt/nowlms"
EXCLUDE_FILE="/backup/scripts/exclude.txt"

# Create exclude file
cat > $EXCLUDE_FILE << EOF
/proc/*
/sys/*
/dev/*
/tmp/*
/var/tmp/*
/var/cache/*
/var/log/journal/*
/home/*/.cache/*
/root/.cache/*
*.pyc
__pycache__
EOF

# Create system backup
tar -czf $BACKUP_DIR/system_backup_$DATE.tar.gz \
    --exclude-from=$EXCLUDE_FILE \
    $SOURCE_DIRS

# NOW-LMS specific backup
tar -czf $BACKUP_DIR/nowlms_files_$DATE.tar.gz \
    /var/lib/nowlms \
    /etc/systemd/system/nowlms.service \
    /opt/nowlms

# Configuration backup
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    /etc/nginx \
    /etc/httpd \
    /etc/postgresql \
    /etc/systemd/system

# Remove old backups
find $BACKUP_DIR -name "system_backup_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "nowlms_files_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "config_backup_*.tar.gz" -mtime +7 -delete

logger "System backup completed: $DATE"
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
    --exclude '/tmp' \
    ::'{hostname}-{now}' \
    /etc \
    /home \
    /var/lib/nowlms \
    /opt/nowlms \
    /var/lib/postgresql \
    /root

backup_exit=$?

# Prune old archives
borg prune \
    --list \
    --prefix '{hostname}-' \
    --show-rc \
    --keep-daily 7 \
    --keep-weekly 4 \
    --keep-monthly 6 \
    --keep-yearly 1

prune_exit=$?

# Use highest exit code as global exit code
global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [ ${global_exit} -eq 0 ]; then
    logger "Borg backup and prune finished successfully"
elif [ ${global_exit} -eq 1 ]; then
    logger "Borg backup and/or prune finished with warnings"
else
    logger "Borg backup and/or prune finished with errors"
fi

exit ${global_exit}
```

### Schedule Backups with systemd timers

```bash
# Create backup service
sudo nano /etc/systemd/system/nowlms-backup.service
```

```ini
# /etc/systemd/system/nowlms-backup.service
[Unit]
Description=NOW-LMS Backup Service
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/backup/scripts/db-backup.sh
ExecStart=/backup/scripts/system-backup.sh
User=root
Group=root
```

```bash
# Create backup timer
sudo nano /etc/systemd/system/nowlms-backup.timer
```

```ini
# /etc/systemd/system/nowlms-backup.timer
[Unit]
Description=Run NOW-LMS backup daily
Requires=nowlms-backup.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=30m

[Install]
WantedBy=timers.target
```

```bash
# Enable and start backup timer
sudo systemctl daemon-reload
sudo systemctl enable nowlms-backup.timer
sudo systemctl start nowlms-backup.timer
sudo systemctl status nowlms-backup.timer

# Check timer status
sudo systemctl list-timers
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

### Configure systemd Services for NOW-LMS

```bash
# Create NOW-LMS systemd service
sudo nano /etc/systemd/system/nowlms.service
```

```ini
# /etc/systemd/system/nowlms.service
[Unit]
Description=NOW Learning Management System
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=nowlms
Group=nowlms
WorkingDirectory=/opt/nowlms
Environment=FLASK_APP=now_lms
Environment=SECRET_KEY=your-very-secure-secret-key
Environment=DATABASE_URL=postgresql://user:pass@localhost/nowlms
Environment=LOG_LEVEL=INFO
ExecStart=/opt/nowlms/venv/bin/lmsctl serve
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=3
KillMode=mixed
TimeoutStopSec=30

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/nowlms /tmp

[Install]
WantedBy=multi-user.target
```

```bash
# Create nowlms user
sudo useradd --system --home-dir /opt/nowlms --shell /sbin/nologin nowlms

# Set permissions
sudo chown -R nowlms:nowlms /opt/nowlms
sudo chown -R nowlms:nowlms /var/lib/nowlms

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable nowlms
sudo systemctl start nowlms
sudo systemctl status nowlms
```

### Kernel Live Patching (RHEL)

```bash
# For RHEL with subscription
sudo subscription-manager repos --enable=rhel-*-kpatch-repo
sudo dnf install -y kpatch

# Enable kpatch service
sudo systemctl enable kpatch.service

# Apply available kernel patches
sudo kpatch install

# Check installed patches
sudo kpatch list
```

### Disk Health Monitoring

```bash
# Install smartmontools
sudo dnf install -y smartmontools

# Check disk health
sudo smartctl -a /dev/sda

# Enable SMART monitoring
sudo systemctl enable smartd
sudo systemctl start smartd

# Configure SMART monitoring
sudo nano /etc/smartmontools/smartd.conf
```

```bash
# /etc/smartmontools/smartd.conf
# Monitor all disks
DEVICESCAN -a -o on -S on -n standby,q -s (S/../.././02|L/../../6/03) -W 4,35,40 -m admin@example.com
```

```bash
# Schedule SMART tests
sudo nano /etc/cron.d/smartmon
```

```bash
# /etc/cron.d/smartmon
# Short test every Sunday at 2 AM
0 2 * * 0 root /usr/sbin/smartctl -t short /dev/sda

# Long test first Sunday of every month at 3 AM
0 3 1-7 * 0 root /usr/sbin/smartctl -t long /dev/sda
```

---

## Database Management

### PostgreSQL Setup and Hardening

```bash
# Install PostgreSQL
sudo dnf install -y postgresql-server postgresql-contrib

# Initialize database
sudo postgresql-setup --initdb --unit postgresql

# Start and enable PostgreSQL
sudo systemctl enable --now postgresql

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
sudo nano /var/lib/pgsql/data/postgresql.conf
```

```bash
# /var/lib/pgsql/data/postgresql.conf
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
work_mem = 4MB

# Enable logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%a.log'
log_truncate_on_rotation = on
log_rotation_age = 1d
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

```bash
# Configure authentication
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

```bash
# /var/lib/pgsql/data/pg_hba.conf
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
```

```bash
# Set SELinux context for PostgreSQL
sudo setsebool -P postgresql_can_rsync on
sudo semanage port -a -t postgresql_port_t -p tcp 5432

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### MySQL/MariaDB Setup (Alternative)

```bash
# Install MariaDB
sudo dnf install -y mariadb-server mariadb

# Start and enable MariaDB
sudo systemctl enable --now mariadb

# Secure MariaDB installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
-- MariaDB commands
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
sudo dnf install -y nginx

# Create NOW-LMS site configuration
sudo nano /etc/nginx/conf.d/nowlms.conf
```

```nginx
# /etc/nginx/conf.d/nowlms.conf
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
        proxy_redirect off;
        proxy_connect_timeout 30;
        proxy_send_timeout 30;
        proxy_read_timeout 30;
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

    location ~ /\.ht {
        deny all;
    }

    # Logging
    access_log /var/log/nginx/nowlms_access.log;
    error_log /var/log/nginx/nowlms_error.log;
}
```

```bash
# Test and restart Nginx
sudo nginx -t
sudo systemctl enable --now nginx

# Configure SELinux for Nginx
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1

# Allow Nginx through firewall
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Apache (httpd) Setup (Alternative)

```bash
# Install Apache
sudo dnf install -y httpd mod_ssl

# Create NOW-LMS virtual host
sudo nano /etc/httpd/conf.d/nowlms.conf
```

```apache
# /etc/httpd/conf.d/nowlms.conf
<VirtualHost *:80>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    ServerAlias www.your-domain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/your-domain.com/cert.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your-domain.com/privkey.pem
    SSLCertificateChainFile /etc/letsencrypt/live/your-domain.com/chain.pem

    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

    # NOW-LMS proxy
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/
    ProxyPreserveHost On

    # Static files
    Alias /static/ /opt/nowlms/now_lms/static/
    <Directory "/opt/nowlms/now_lms/static/">
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 30 days"
    </Directory>

    # Logging
    CustomLog /var/log/httpd/nowlms_access.log combined
    ErrorLog /var/log/httpd/nowlms_error.log
</VirtualHost>
```

```bash
# Enable required modules
sudo systemctl enable --now httpd

# Configure SELinux for Apache
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
```

### SSL/TLS with Let's Encrypt

```bash
# Install Certbot
sudo dnf install -y certbot python3-certbot-nginx

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

### Podman Setup (RHEL/Fedora Default)

Podman is the default container runtime in RHEL/Fedora:

```bash
# Install Podman
sudo dnf install -y podman podman-compose

# Create rootless container for NOW-LMS
podman run -d \
  --name nowlms-app \
  --restart=unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -e SECRET_KEY=your-very-secure-secret-key \
  -e DATABASE_URL=postgresql://nowlms:password@host.containers.internal:5432/nowlms \
  -v nowlms-data:/app/data:Z \
  -v nowlms-themes:/app/themes:Z \
  quay.io/bmosoluciones/now_lms:latest

# Create systemd service for rootless container
mkdir -p ~/.config/systemd/user
podman generate systemd --new --name nowlms-app > ~/.config/systemd/user/nowlms-app.service

# Enable user service
systemctl --user daemon-reload
systemctl --user enable nowlms-app.service
systemctl --user start nowlms-app.service

# Enable lingering for user services
sudo loginctl enable-linger $USER
```

### Docker Setup (Alternative)

```bash
# Install Docker
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl enable --now docker

# Add user to docker group
sudo usermod -aG docker $USER

# Configure Docker daemon
sudo nano /etc/docker/daemon.json
```

```json
{
    "log-driver": "journald",
    "log-opts": {
        "tag": "{{.Name}}/{{.ID}}"
    },
    "storage-driver": "overlay2",
    "selinux-enabled": true
}
```

### NOW-LMS Container Compose

```bash
# Create docker-compose configuration
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
            - LOG_LEVEL=INFO
        volumes:
            - nowlms-data:/app/data:Z
            - nowlms-themes:/app/themes:Z
        depends_on:
            - postgres
            - redis
        networks:
            - nowlms-network

    postgres:
        image: postgres:15
        container_name: nowlms-postgres
        restart: unless-stopped
        environment:
            - POSTGRES_DB=nowlms
            - POSTGRES_USER=nowlms
            - POSTGRES_PASSWORD=secure_password_here
        volumes:
            - postgres-data:/var/lib/postgresql/data:Z
        networks:
            - nowlms-network

    redis:
        image: redis:7-alpine
        container_name: nowlms-redis
        restart: unless-stopped
        volumes:
            - redis-data:/data:Z
        networks:
            - nowlms-network

volumes:
    nowlms-data:
    nowlms-themes:
    postgres-data:
    redis-data:

networks:
    nowlms-network:
        driver: bridge
```

```bash
# Set SELinux context for container volumes
sudo setsebool -P container_manage_cgroup 1

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs nowlms
```

---

## Compliance & Documentation

### OpenSCAP Security Compliance

```bash
# Install OpenSCAP
sudo dnf install -y openscap-scanner scap-security-guide

# List available profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel*.xml

# Run security scan
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --results-arf /tmp/arf.xml \
    --report /tmp/compliance-report.html \
    /usr/share/xml/scap/ssg/content/ssg-rhel*.xml

# Generate remediation script
sudo oscap xccdf generate fix \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --template bash \
    /usr/share/xml/scap/ssg/content/ssg-rhel*.xml > /tmp/remediation.sh
```

### Lynis Security Audit

```bash
# Install Lynis
sudo dnf install -y lynis

# Run comprehensive security audit
sudo lynis audit system

# Generate custom report
sudo lynis audit system --report-file /tmp/lynis-report.log

# Review recommendations
sudo lynis show suggestions
```

### Infrastructure as Code with Ansible

```bash
# Install Ansible
sudo dnf install -y ansible

# Create Ansible playbook for NOW-LMS
mkdir -p /opt/ansible/{playbooks,inventories,roles}
nano /opt/ansible/playbooks/nowlms-deployment.yml
```

```yaml
# /opt/ansible/playbooks/nowlms-deployment.yml
---
- name: Deploy NOW-LMS on RHEL
  hosts: localhost
  become: yes
  vars:
      nowlms_user: nowlms
      nowlms_dir: /opt/nowlms
      db_name: nowlms
      db_user: nowlms_user

  tasks:
      - name: Install EPEL repository
        dnf:
            name: epel-release
            state: present

      - name: Install dependencies
        dnf:
            name:
                - python3
                - python3-pip
                - nginx
                - postgresql-server
                - postgresql-contrib
                - git
            state: present

      - name: Create NOW-LMS user
        user:
            name: "{{ nowlms_user }}"
            system: yes
            shell: /sbin/nologin
            home: "{{ nowlms_dir }}"
            create_home: yes

      - name: Install NOW-LMS
        pip:
            name: now-lms
            virtualenv: "{{ nowlms_dir }}/venv"
            virtualenv_python: python3
        become_user: "{{ nowlms_user }}"

      - name: Configure systemd service
        template:
            src: nowlms.service.j2
            dest: /etc/systemd/system/nowlms.service
        notify:
            - reload systemd
            - restart nowlms

      - name: Configure Nginx
        template:
            src: nginx-nowlms.conf.j2
            dest: /etc/nginx/conf.d/nowlms.conf
        notify: restart nginx

      - name: Configure firewall
        firewalld:
            service: "{{ item }}"
            permanent: yes
            state: enabled
            immediate: yes
        loop:
            - http
            - https

      - name: Enable and start services
        systemd:
            name: "{{ item }}"
            enabled: yes
            state: started
        loop:
            - nowlms
            - nginx
            - postgresql

  handlers:
      - name: reload systemd
        systemd:
            daemon_reload: yes

      - name: restart nowlms
        systemd:
            name: nowlms
            state: restarted

      - name: restart nginx
        systemd:
            name: nginx
            state: restarted
```

### Configuration Management with Git

```bash
# Set up configuration repository
mkdir -p /opt/config-management
cd /opt/config-management
git init

# Track important configuration files
mkdir -p {nginx,httpd,postgresql,systemd,firewalld,selinux}
cp /etc/nginx/conf.d/nowlms.conf nginx/ 2>/dev/null || true
cp /etc/httpd/conf.d/nowlms.conf httpd/ 2>/dev/null || true
cp /var/lib/pgsql/data/postgresql.conf postgresql/ 2>/dev/null || true
cp /etc/systemd/system/nowlms.service systemd/ 2>/dev/null || true
firewall-cmd --list-all > firewalld/current-config.txt
semodule -l > selinux/modules.txt

# Create configuration tracking script
nano track-config.sh
```

```bash
#!/bin/bash
# /opt/config-management/track-config.sh

cd /opt/config-management

# Copy current configurations
cp /etc/nginx/conf.d/nowlms.conf nginx/ 2>/dev/null || true
cp /etc/httpd/conf.d/nowlms.conf httpd/ 2>/dev/null || true
cp /var/lib/pgsql/data/postgresql.conf postgresql/ 2>/dev/null || true
cp /etc/systemd/system/nowlms.service systemd/ 2>/dev/null || true

# Update firewall config
firewall-cmd --list-all > firewalld/current-config.txt

# Update SELinux modules
semodule -l > selinux/modules.txt

# Check for changes
if [[ -n $(git status --porcelain) ]]; then
    git add .
    git commit -m "Configuration update - $(date +%Y-%m-%d_%H:%M:%S)"
    echo "Configuration changes committed"
else
    echo "No configuration changes detected"
fi
```

```bash
# Make executable and schedule
chmod +x track-config.sh

# Schedule daily configuration tracking
echo "0 2 * * * /opt/config-management/track-config.sh" | sudo crontab -e
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
sudo journalctl -u postgresql -f

# Check service dependencies
sudo systemctl list-dependencies nowlms

# Restart services in correct order
sudo systemctl restart postgresql
sudo systemctl restart nowlms
sudo systemctl reload nginx
```

#### SELinux Issues

```bash
# Check SELinux denials
sudo ausearch -m avc -ts recent
sudo grep AVC /var/log/audit/audit.log

# Use sealert for detailed analysis
sudo sealert -a /var/log/audit/audit.log

# Temporarily set SELinux to permissive (for testing only)
sudo setenforce 0

# Check current SELinux mode
getenforce

# Re-enable enforcing mode
sudo setenforce 1
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql
sudo -u postgres psql -l

# Test database connectivity
sudo -u postgres psql -d nowlms -c "SELECT version();"

# Check PostgreSQL logs
sudo tail -f /var/lib/pgsql/data/log/postgresql-*.log

# Verify authentication configuration
sudo cat /var/lib/pgsql/data/pg_hba.conf
```

#### Firewall Issues

```bash
# Check firewall status
sudo firewall-cmd --state
sudo firewall-cmd --list-all

# Test port connectivity
sudo ss -tulpn | grep :8080
sudo netstat -tulpn | grep :8080

# Temporary firewall rule for testing
sudo firewall-cmd --add-port=8080/tcp

# Make permanent
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

#### Network and DNS Issues

```bash
# Check network connectivity
curl -I http://localhost:8080
curl -I https://your-domain.com

# Check DNS resolution
nslookup your-domain.com
dig your-domain.com

# Check routing
ip route show
ss -rn
```

### Performance Troubleshooting

```bash
# Monitor system resources
htop
top -u nowlms

# Check I/O performance
iotop
iostat -x 1

# Monitor network traffic
nethogs
ss -tuln

# Check disk usage
df -h
du -sh /var/* | sort -hr

# Monitor memory usage
free -h
vmstat 1

# Check for high CPU processes
ps aux --sort=-%cpu | head -20
```

### Log Analysis Commands

```bash
# Search for errors in system logs
sudo journalctl -p err -n 50
sudo grep -i error /var/log/messages

# Analyze Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo grep "5xx" /var/log/nginx/access.log

# Monitor authentication attempts
sudo grep "Failed password" /var/log/secure
sudo grep "authentication failure" /var/log/secure

# Analyze PostgreSQL logs
sudo grep ERROR /var/lib/pgsql/data/log/postgresql-*.log
```

### Emergency Recovery Procedures

```bash
# Emergency system information
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8080

# Kill problematic processes
sudo pkill -f python
sudo systemctl stop nowlms

# Emergency disk cleanup
sudo dnf autoremove -y
sudo dnf clean all
sudo find /var/log -name "*.log" -mtime +30 -delete
sudo find /tmp -mtime +7 -delete
sudo journalctl --vacuum-time=7d

# Reset SELinux contexts
sudo restorecon -Rv /opt/nowlms/
sudo restorecon -Rv /var/lib/nowlms/

# Emergency firewall reset
sudo firewall-cmd --reload
sudo firewall-cmd --panic-off
```

---

## Security Checklist

Use this checklist to ensure your RHEL-based server follows security best practices:

- [ ] System fully updated with automatic security updates enabled
- [ ] SELinux in enforcing mode with proper contexts configured
- [ ] Non-root administrative user created with sudo privileges
- [ ] SSH hardened with key-based authentication and non-default port
- [ ] Root login disabled
- [ ] Fail2ban configured and active
- [ ] Firewalld enabled with minimal required services
- [ ] Unnecessary services disabled
- [ ] Kernel security parameters configured
- [ ] Automatic security updates configured
- [ ] Regular backups scheduled and tested
- [ ] SSL/TLS certificates configured and auto-renewing
- [ ] System monitoring and alerting configured
- [ ] Log rotation and retention configured
- [ ] Database properly secured and backed up
- [ ] Web server hardened with security headers
- [ ] Regular security audits with OpenSCAP
- [ ] Configuration changes tracked in version control
- [ ] Documentation kept up to date
- [ ] Compliance reports generated regularly

## Additional RHEL-Specific Considerations

### Red Hat Subscription Management

```bash
# Register system with Red Hat
sudo subscription-manager register --username your-username

# Attach subscription
sudo subscription-manager attach --auto

# Enable required repositories
sudo subscription-manager repos --enable=rhel-*-server-optional-rpms
sudo subscription-manager repos --enable=rhel-*-server-extras-rpms
```

### Security Scanning and Compliance

```bash
# Use Red Hat Insights for security analysis
sudo insights-client --register
sudo insights-client --check-results

# Install security scanner
sudo dnf install -y aide

# Initialize AIDE database
sudo aide --init
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Schedule regular integrity checks
echo "0 3 * * * /usr/sbin/aide --check" | sudo crontab -e
```

This comprehensive guide provides a solid foundation for securely administering RHEL-based servers running NOW Learning Management System. The emphasis on SELinux, firewalld, and RHEL-specific tools ensures optimal security and performance for enterprise environments.
