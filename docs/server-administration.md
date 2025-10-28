# Server Administration Best Practices

This section provides comprehensive server administration guides for deploying and maintaining NOW Learning Management System in production environments.

## Available Guides

### [Ubuntu/Debian Server Administration](server-admin-ubuntu.md)

Complete best practices guide for Ubuntu and Debian-based systems including:

- **Security Hardening** - AppArmor configuration, UFW firewall, SSH hardening
- **User Management** - Non-root users, sudo configuration, SSH key authentication
- **System Updates** - Unattended upgrades, package management
- **Monitoring & Alerts** - Cockpit, Netdata, email alerting, log management
- **Backup & Recovery** - Automated backups, BorgBackup, disaster recovery
- **Performance Optimization** - Swap configuration, systemd services, disk health
- **Database Management** - PostgreSQL/MySQL setup and hardening
- **Web Server Configuration** - Nginx/Apache setup with SSL/TLS
- **Container Support** - Docker configuration for NOW-LMS

### [RHEL/Alma/Rocky/Amazon/Fedora Server Administration](server-admin-rhel.md)

Comprehensive guide for Red Hat Enterprise Linux family systems including:

- **SELinux Security** - Mandatory access control, custom policies, troubleshooting
- **Firewalld Configuration** - Advanced firewall rules, rich rules, custom services
- **Enterprise Security** - OpenSCAP compliance, CIS benchmarks, security auditing
- **System Management** - DNF package management, systemd configuration
- **Monitoring & Compliance** - Cockpit, Red Hat Insights, security scanning
- **Backup Strategies** - Enterprise backup solutions, automation
- **Container Support** - Podman (RHEL default), Docker alternatives
- **Database Hardening** - PostgreSQL/MariaDB enterprise configuration
- **Web Server Setup** - Nginx/Apache with enterprise security

### [Rocky Linux Quick Setup](rocky.md)

Quick deployment guide for EL9 systems - ideal for development and testing environments.

## Key Differences Between Platforms

| Feature                | Ubuntu/Debian       | RHEL Family                |
| ---------------------- | ------------------- | -------------------------- |
| **Security Framework** | AppArmor            | SELinux                    |
| **Firewall**           | UFW/iptables        | firewalld                  |
| **Package Manager**    | apt/dpkg            | dnf/rpm                    |
| **Auto Updates**       | unattended-upgrades | dnf-automatic              |
| **Container Runtime**  | Docker (default)    | Podman (default)           |
| **Web Console**        | Cockpit (optional)  | Cockpit (built-in)         |
| **Compliance Tools**   | Lynis, manual CIS   | OpenSCAP, Red Hat Insights |

## Security Considerations

Both guides emphasize:

- **Zero-trust principles** - Minimal attack surface, least privilege access
- **Defense in depth** - Multiple security layers
- **Automated security** - Automatic updates, monitoring, alerting
- **Compliance standards** - CIS benchmarks, security best practices
- **Regular auditing** - Scheduled security scans and reports
- **Backup strategies** - Automated, tested backup and recovery procedures

## Getting Started

1. **Choose your platform guide** based on your operating system
2. **Follow the initial setup** section to secure your base system
3. **Implement security hardening** before deploying NOW-LMS
4. **Set up monitoring and alerting** for ongoing maintenance
5. **Configure automated backups** to protect your data
6. **Deploy NOW-LMS** following the platform-specific instructions
7. **Implement ongoing maintenance** procedures

## Additional Resources

- [Setup Guide](setup.md) - Basic NOW-LMS installation
- [Configuration Guide](setup-conf.md) - Application configuration options
- [Session Troubleshooting](session-troubleshooting.md) - Multi-worker session configuration and debugging
- [Development Guide](development/) - Development environment setup
- [FAQ](faq.md) - Frequently asked questions

For questions or improvements to these guides, please refer to the [Contributing Guidelines](CONTRIBUTING.md).
