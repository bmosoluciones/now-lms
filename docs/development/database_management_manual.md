# Database Management Manual

This manual provides guidelines for database administrators (DBAs) to ensure proper operation, maintenance, and recovery of databases. It covers PostgreSQL, MySQL, and SQLite as supported by the NOW LMS system.

## Table of Contents

1. [PostgreSQL](#postgresql)
2. [MySQL / MariaDB](#mysql--mariadb)
3. [SQLite](#sqlite)
4. [Best Practices](#best-practices-all-databases)
5. [Connection Pool Configuration](#connection-pool-configuration)
6. [Security Guidelines](#security-guidelines)

---

## PostgreSQL

### 🔄 Periodic Management Tasks

#### Database Maintenance

- [ ] **VACUUM regularly** to reclaim storage and prevent bloat:
  ```sql
  -- Regular vacuum (can run online)
  VACUUM;
  
  -- Full vacuum (requires exclusive lock)
  VACUUM FULL;
  
  -- Vacuum specific table
  VACUUM ANALYZE table_name;
  ```

- [ ] **Run ANALYZE** to refresh statistics for the query planner:
  ```sql
  ANALYZE;
  -- Or for specific table
  ANALYZE table_name;
  ```

- [ ] **Monitor and rotate PostgreSQL logs**:
  ```bash
  # Check log location
  psql -c "SHOW log_directory;"
  
  # Configure log rotation in postgresql.conf
  log_rotation_age = 1d
  log_rotation_size = 100MB
  ```

- [ ] **Check replication health** (if streaming replication is enabled):
  ```sql
  -- On primary
  SELECT * FROM pg_stat_replication;
  
  -- On replica
  SELECT * FROM pg_stat_wal_receiver;
  ```

- [ ] **Apply security patches** and update extensions:
  ```sql
  -- Check installed extensions
  SELECT * FROM pg_extension;
  
  -- Update extension
  ALTER EXTENSION extension_name UPDATE;
  ```

- [ ] **Monitor query performance** using EXPLAIN ANALYZE:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM usuario WHERE correo_electronico = 'user@example.com';
  ```

- [ ] **Rebuild indexes** if fragmentation is high:
  ```sql
  -- Check index bloat
  SELECT schemaname, tablename, indexname, 
         pg_size_pretty(pg_relation_size(indexrelid)) as size
  FROM pg_stat_user_indexes;
  
  -- Rebuild index
  REINDEX INDEX index_name;
  
  -- Rebuild all indexes for a table
  REINDEX TABLE table_name;
  ```

#### Performance Monitoring

- [ ] **Enable pg_stat_statements** for query analysis:
  ```sql
  -- Add to postgresql.conf
  shared_preload_libraries = 'pg_stat_statements'
  
  -- Create extension
  CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
  
  -- View slow queries
  SELECT query, calls, total_time, mean_time 
  FROM pg_stat_statements 
  ORDER BY total_time DESC LIMIT 10;
  ```

### 💾 Backup & Recovery

#### Full Backup (pg_dump / pg_dumpall)

```bash
# Single database backup
pg_dump -U username -F c -d database_name -f backup_file.dump

# All databases backup
pg_dumpall -U username > full_backup.sql

# Compressed backup
pg_dump -U username -F c -Z 9 -d database_name -f backup_file.dump.gz

# Schema-only backup
pg_dump -U username -s -d database_name -f schema_backup.sql
```

#### Point-in-Time Recovery (PITR)

1. **Enable archive mode** in `postgresql.conf`:
   ```
   archive_mode = on
   wal_level = replica
   archive_command = 'cp %p /path/to/archive/%f'
   ```

2. **Take base backup**:
   ```bash
   pg_basebackup -U username -D /path/to/backup -F tar -z -P
   ```

3. **Restore and replay WAL logs**:
   ```bash
   # Restore base backup
   tar -xzf base.tar.gz -C /path/to/data
   
   # Create recovery.conf
   echo "restore_command = 'cp /path/to/archive/%f %p'" > recovery.conf
   echo "recovery_target_time = '2024-01-01 12:00:00'" >> recovery.conf
   ```

#### Restore Operations

```bash
# Restore from custom format dump
pg_restore -U username -d database_name backup_file.dump

# Restore with clean (drop existing objects)
pg_restore -U username -d database_name -c backup_file.dump

# Restore specific table
pg_restore -U username -d database_name -t table_name backup_file.dump
```

---

## MySQL / MariaDB

### 🔄 Periodic Management Tasks

#### Database Maintenance

- [ ] **Run ANALYZE TABLE** to update optimizer statistics:
  ```sql
  ANALYZE TABLE table_name;
  
  -- For all tables in database
  SELECT CONCAT('ANALYZE TABLE ', table_schema, '.', table_name, ';') 
  FROM information_schema.tables 
  WHERE table_schema = 'your_database';
  ```

- [ ] **Optimize fragmented tables**:
  ```sql
  OPTIMIZE TABLE table_name;
  
  -- Check table fragmentation
  SELECT table_name, data_free, data_length
  FROM information_schema.tables 
  WHERE table_schema = 'your_database' 
  AND data_free > 0;
  ```

- [ ] **Monitor slow query log** and tune queries/indexes:
  ```sql
  -- Enable slow query log
  SET GLOBAL slow_query_log = 'ON';
  SET GLOBAL long_query_time = 2;
  
  -- Check slow queries
  SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
  ```

- [ ] **Rotate and archive binary logs**:
  ```sql
  -- Show binary logs
  SHOW BINARY LOGS;
  
  -- Purge old binary logs
  PURGE BINARY LOGS BEFORE '2024-01-01 00:00:00';
  ```

- [ ] **Verify replication status**:
  ```sql
  -- On replica
  SHOW SLAVE STATUS\G
  
  -- On primary
  SHOW PROCESSLIST;
  ```

- [ ] **Apply security patches** and keep MySQL updated
- [ ] **Monitor buffer pool usage**:
  ```sql
  SHOW ENGINE INNODB STATUS;
  
  -- Check buffer pool efficiency
  SELECT 
    (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100 
    AS buffer_pool_hit_ratio;
  ```

### 💾 Backup & Recovery

#### Logical Backup (mysqldump)

```bash
# Single database backup
mysqldump -u username -p database_name > backup.sql

# All databases backup
mysqldump -u username -p --all-databases > all_databases.sql

# Compressed backup
mysqldump -u username -p database_name | gzip > backup.sql.gz

# Schema-only backup
mysqldump -u username -p --no-data database_name > schema_backup.sql

# Specific tables backup
mysqldump -u username -p database_name table1 table2 > tables_backup.sql
```

#### Physical Backup (Percona XtraBackup)

```bash
# Full backup
xtrabackup --backup --target-dir=/path/to/backup

# Incremental backup
xtrabackup --backup --target-dir=/path/to/incremental \
           --incremental-basedir=/path/to/full-backup

# Prepare backup
xtrabackup --prepare --target-dir=/path/to/backup
```

#### Restore Operations

```bash
# Restore from logical backup
mysql -u username -p database_name < backup.sql

# Restore all databases
mysql -u username -p < all_databases.sql

# Restore from compressed backup
gunzip < backup.sql.gz | mysql -u username -p database_name
```

#### Replication-based Recovery

- **Promote a replica** if the primary fails
- **Reconfigure replication** after restoring:
  ```sql
  CHANGE MASTER TO 
    MASTER_HOST='new_primary_host',
    MASTER_USER='replication_user',
    MASTER_PASSWORD='password';
  START SLAVE;
  ```

---

## SQLite

### 🔄 Periodic Management Tasks

#### Database Maintenance

- [ ] **Run VACUUM** periodically to reclaim unused space:
  ```sql
  VACUUM;
  
  -- Check if vacuum is needed
  PRAGMA integrity_check;
  ```

- [ ] **Use ANALYZE** to refresh query planner statistics:
  ```sql
  ANALYZE;
  
  -- For specific table
  ANALYZE table_name;
  ```

- [ ] **Keep database file size in check**, archive old data if necessary
- [ ] **Enable WAL mode** for better performance under concurrent writes:
  ```sql
  PRAGMA journal_mode=WAL;
  ```

- [ ] **Monitor for database file corruption**:
  ```sql
  PRAGMA integrity_check;
  PRAGMA foreign_key_check;
  ```

- [ ] **Optimize database file**:
  ```sql
  -- Rebuild database file
  VACUUM;
  
  -- Check page count and size
  PRAGMA page_count;
  PRAGMA page_size;
  ```

### 💾 Backup & Recovery

#### Simple Backup (file copy)

```bash
# Safely copy database file when no active writes
cp mydatabase.db backup_mydatabase.db

# With timestamp
cp mydatabase.db "backup_$(date +%Y%m%d_%H%M%S).db"
```

#### Online Backup (without downtime)

```sql
-- Using SQLite's backup API
.backup backup_file.db

-- Or using VACUUM INTO (SQLite 3.27+)
VACUUM main INTO 'backup_file.db';
```

#### Export to SQL

```bash
# Export database to SQL
sqlite3 database.db .dump > backup.sql

# Export specific table
sqlite3 database.db "SELECT sql FROM sqlite_master WHERE name='table_name';" > table_schema.sql
```

#### Recovery Operations

```bash
# Replace corrupted database with backup
cp backup_mydatabase.db mydatabase.db

# Restore from SQL dump
sqlite3 new_database.db < backup.sql

# Import specific table
sqlite3 database.db < table_data.sql
```

---

## Best Practices (All Databases)

### ✅ General Guidelines

#### Backup Strategy

- [ ] **Implement regular automated backups** (daily, weekly, monthly retention)
- [ ] **Test recovery procedures** at least quarterly
- [ ] **Store backups in multiple locations** (local, remote, cloud)
- [ ] **Verify backup integrity** regularly
- [ ] **Document backup schedules** and retention policies

#### Monitoring and Alerting

- [ ] **Use monitoring tools** (e.g., pgAdmin, Percona Monitoring, Grafana)
- [ ] **Set up alerts** for disk space, connection limits, slow queries
- [ ] **Monitor key metrics**:
  - Connection count
  - Query response times
  - Disk usage
  - Replication lag (if applicable)

#### Security

- [ ] **Enforce role-based access control**
- [ ] **Apply principle of least privilege**
- [ ] **Apply security updates** to database engine and OS
- [ ] **Use encrypted connections** (SSL/TLS)
- [ ] **Audit database access** and modifications

#### Performance

- [ ] **Regular index maintenance**
- [ ] **Query optimization**
- [ ] **Resource monitoring**
- [ ] **Connection pooling configuration**

---

## Connection Pool Configuration

### SQLAlchemy Pool Settings for NOW LMS

The NOW LMS system uses SQLAlchemy for database connectivity. Proper pool configuration is crucial for performance and stability.

#### Recommended Settings

```python
# In your configuration
DATABASE_URL = "postgresql://user:pass@host:port/db"

# Pool configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,              # Number of connections to maintain
    'max_overflow': 20,           # Additional connections beyond pool_size
    'pool_timeout': 30,           # Seconds to wait for connection
    'pool_recycle': 3600,         # Seconds to recycle connections
    'pool_pre_ping': True,        # Validate connections before use
}
```

#### Pool Monitoring

```python
# Check pool status
from sqlalchemy import event
from sqlalchemy.pool import Pool

@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
```

#### Database-Specific Pool Settings

**PostgreSQL:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {
        'sslmode': 'require',
        'application_name': 'NOW_LMS'
    }
}
```

**MySQL:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {
        'charset': 'utf8mb4',
        'sql_mode': 'STRICT_TRANS_TABLES'
    }
}
```

**SQLite:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,              # Higher for SQLite
    'max_overflow': 0,            # No overflow for SQLite
    'pool_timeout': 20,
    'pool_recycle': -1,           # No recycling for SQLite
    'connect_args': {
        'check_same_thread': False
    }
}
```

---

## Security Guidelines

### Database User Management

#### Principle of Least Privilege

- [ ] **Create dedicated application user** (never use superuser)
- [ ] **Grant only required permissions**:
  ```sql
  -- PostgreSQL example
  CREATE USER now_lms_app WITH PASSWORD 'secure_password';
  GRANT CONNECT ON DATABASE now_lms TO now_lms_app;
  GRANT USAGE ON SCHEMA public TO now_lms_app;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO now_lms_app;
  
  -- MySQL example
  CREATE USER 'now_lms_app'@'%' IDENTIFIED BY 'secure_password';
  GRANT SELECT, INSERT, UPDATE, DELETE ON now_lms.* TO 'now_lms_app'@'%';
  ```

#### Connection Security

- [ ] **Use SSL/TLS connections**
- [ ] **Restrict network access** (firewall rules)
- [ ] **Use connection strings with SSL**:
  ```
  postgresql://user:pass@host:5432/db?sslmode=require
  mysql://user:pass@host:3306/db?ssl=true
  ```

#### Audit and Compliance

- [ ] **Enable audit logging**:
  ```sql
  -- PostgreSQL: Enable in postgresql.conf
  log_statement = 'all'
  log_connections = on
  log_disconnections = on
  
  -- MySQL: Enable in my.cnf
  general_log = 1
  log_output = TABLE
  ```

- [ ] **Monitor failed login attempts**
- [ ] **Regular security assessments**
- [ ] **Password rotation policies**

### Environment-Specific Configurations

#### Development
- Use local database instances
- Enable query logging for debugging
- Relaxed connection limits

#### Staging
- Mirror production configuration
- Use production-like data volumes
- Test backup/restore procedures

#### Production
- Strict security policies
- Optimized performance settings
- Comprehensive monitoring
- Regular backups with tested recovery

---

## Troubleshooting Common Issues

### Connection Issues

**Problem**: Connection pool exhaustion
```
Solution: Increase pool_size or max_overflow, check for connection leaks
```

**Problem**: SSL connection failures
```
Solution: Verify SSL certificates, check sslmode settings
```

### Performance Issues

**Problem**: Slow queries
```
Solution: Add appropriate indexes, optimize queries, update statistics
```

**Problem**: High disk usage
```
Solution: Run VACUUM, archive old data, check for index bloat
```

### Data Integrity Issues

**Problem**: Foreign key violations
```
Solution: Check referential integrity, validate data migration scripts
```

**Problem**: Inconsistent data
```
Solution: Run integrity checks, validate audit trails
```

---

## Documentation Updates

This manual should be updated whenever:
- [ ] Database schema changes are made
- [ ] New indexes are added
- [ ] Configuration changes are implemented
- [ ] New backup procedures are established
- [ ] Security policies are updated

**Last Updated**: [DATE]
**Version**: 1.0
**Maintainer**: Database Administration Team
