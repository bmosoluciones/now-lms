# Session Troubleshooting for Multi-Worker WSGI Servers

This guide helps diagnose and fix session issues when running NOW LMS with production WSGI servers like Gunicorn or Waitress that use multiple workers or threads.

## Quick Diagnostic

If you're experiencing session issues (login not persisting, data loss between requests), follow these steps:

1. **Enable debug endpoints temporarily**:
   ```bash
   export NOW_LMS_DEBUG_ENDPOINTS=1
   ```

2. **Check your session configuration**:
   ```bash
   curl http://localhost:8080/debug/config
   ```

3. **Verify session persistence**:
   ```bash
   # Login first
   curl -c cookies.txt -X POST http://localhost:8080/user/login \
     -d "usuario=admin@example.com" -d "acceso=yourpassword"
   
   # Then test session across multiple requests
   for i in {1..5}; do
     curl -b cookies.txt http://localhost:8080/debug/session | jq '.worker.pid, .authenticated'
   done
   ```

   **Expected**: PID may change (different workers) but `authenticated` should remain `true`.

## Understanding Multi-Worker Sessions

### The Problem

By default, Flask stores sessions in signed cookies. While this works for single-process servers, it can cause issues with multi-worker WSGI servers because:

- **Multiple workers = multiple OS processes**: Each has separate memory
- **Session data might not persist**: Default session storage won't work across processes
- **Remember me cookies and session cookies are different**: Both must work correctly

### The Solution

NOW LMS automatically configures shared session storage:

1. **Redis (Recommended)**: Best for production with multiple workers
2. **CacheLib FileSystemCache**: Fallback when Redis isn't available
3. **Default Flask sessions**: Used only in testing mode

## Configuration

### Option 1: Redis (Recommended for Production)

Redis provides the best performance and reliability for multi-worker setups.

**Install Redis**:
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

**Configure NOW LMS**:
```bash
export REDIS_URL="redis://localhost:6379/0"
# Or use the specific session Redis URL
export SESSION_REDIS_URL="redis://localhost:6379/0"
```

**Verify Redis connection**:
```bash
curl http://localhost:8080/debug/redis
```

### Option 2: CacheLib FileSystemCache (Fallback)

When Redis is not available, NOW LMS automatically uses filesystem-based sessions.

**Requirements**:
- All workers must have access to the same filesystem
- Shared storage for containers/distributed systems

**Configuration**:
```bash
# No configuration needed - automatically enabled
# Sessions stored in /dev/shm/now_lms_sessions (Linux)
# or temp directory on other systems
```

**Note**: Not recommended for high-traffic production environments.

### Required: SECRET_KEY

**Critical**: All workers must use the **same SECRET_KEY**.

```bash
# Generate a secure key
export SECRET_KEY=$(openssl rand -hex 32)

# For systemd services
echo "SECRET_KEY=your-generated-key-here" >> /etc/now-lms/environment

# For containers
docker run -e SECRET_KEY="your-key" williamjmorenor/now-lms
```

**Verify**:
```bash
curl http://localhost:8080/debug/config | jq '.config.secret_key_is_default'
# Should return false
```

## Common Issues and Solutions

### Issue 1: Sessions Don't Persist Across Requests

**Symptoms**:
- Login works but immediately logged out on next request
- Different PID shows different session data

**Diagnosis**:
```bash
curl -b cookies.txt http://localhost:8080/debug/session
# Check if current_user changes between requests
```

**Solutions**:

1. **Enable Redis**:
   ```bash
   export REDIS_URL="redis://localhost:6379/0"
   ```

2. **Verify SECRET_KEY is consistent**:
   ```bash
   # Check in debug config
   curl http://localhost:8080/debug/config | jq '.config.secret_key_is_default'
   ```

3. **Check worker configuration**:
   ```bash
   # Reduce workers if testing
   export NOW_LMS_WORKERS=1
   export NOW_LMS_THREADS=4
   ```

### Issue 2: Redis Connection Failures

**Symptoms**:
- Sessions work initially then fail
- Error logs show "Redis connection failed"

**Diagnosis**:
```bash
curl http://localhost:8080/debug/redis
```

**Solutions**:

1. **Verify Redis is running**:
   ```bash
   redis-cli ping
   # Should return PONG
   ```

2. **Check Redis URL**:
   ```bash
   echo $REDIS_URL
   # Should be: redis://host:port/db
   ```

3. **Test connection manually**:
   ```bash
   redis-cli -u "$REDIS_URL" ping
   ```

### Issue 3: Cookie Not Being Sent

**Symptoms**:
- Login works but subsequent requests not authenticated
- No session cookie in browser

**Solutions**:

1. **Check cookie settings**:
   ```bash
   curl http://localhost:8080/debug/config | jq '.config | {
     session_cookie_httponly,
     session_cookie_secure,
     session_cookie_samesite
   }'
   ```

2. **For HTTPS deployments**:
   ```bash
   export SESSION_COOKIE_SECURE=True
   export SESSION_COOKIE_SAMESITE=Lax
   ```

3. **For development (HTTP)**:
   ```bash
   # Ensure SESSION_COOKIE_SECURE is False or unset
   unset SESSION_COOKIE_SECURE
   ```

### Issue 4: Different Workers, Different Sessions

**Symptoms**:
- Session data varies by worker PID
- Debug endpoint shows different users for different PIDs

**Solutions**:

1. **This is the core multi-worker session problem**
   ```bash
   # Enable Redis immediately
   export REDIS_URL="redis://localhost:6379/0"
   ```

2. **Restart all workers** after configuration change:
   ```bash
   # Gunicorn
   sudo systemctl restart now-lms

   # Or manually
   pkill -HUP gunicorn
   ```

## Production Deployment Checklist

Before deploying to production with multiple workers:

- [ ] **Redis configured**: `REDIS_URL` environment variable set
- [ ] **SECRET_KEY set**: Unique, at least 32 characters, same across all workers
- [ ] **Redis connection verified**: `curl http://localhost:8080/debug/redis` returns OK
- [ ] **Session persistence tested**: Login persists across multiple requests with different PIDs
- [ ] **Cookie settings correct**: `SESSION_COOKIE_SECURE=True` for HTTPS
- [ ] **Worker configuration optimal**: Based on available RAM and CPU
- [ ] **Debug endpoints disabled**: Remove `NOW_LMS_DEBUG_ENDPOINTS=1` in production

## Testing Session Configuration

### Local Testing with Gunicorn

```bash
# Start Redis
redis-server --daemonize yes

# Set environment
export SECRET_KEY=$(openssl rand -hex 32)
export REDIS_URL="redis://localhost:6379/0"
export NOW_LMS_DEBUG_ENDPOINTS=1

# Start with multiple workers
cd /path/to/now-lms
gunicorn -w 3 -b 127.0.0.1:8000 wsgi:app

# In another terminal, test
curl -c cookies.txt -X POST http://localhost:8000/user/login \
  -d "usuario=lms-admin" -d "acceso=lms-admin"

# Verify session persists
for i in {1..10}; do
  curl -b cookies.txt http://localhost:8000/debug/session | \
    jq '{pid: .worker.pid, authenticated: .authenticated}'
done
```

**Expected output**: PID varies, but `authenticated` is always `true`.

### Automated Testing

```bash
# Run session tests
pytest tests/test_session_gunicorn.py tests/test_debug_endpoints.py -v
```

## Debug Endpoints Reference

### GET /debug/session

Shows current session state, useful for verifying:
- Process ID (worker identification)
- Session data
- Current user
- Session backend type

**Example**:
```bash
curl http://localhost:8080/debug/session
```

**Response**:
```json
{
  "worker": {
    "pid": 12345,
    "workers_env": "4",
    "threads_env": "2"
  },
  "session_backend": "redis",
  "session_data": {
    "_user_id": "[hidden]",
    "custom_key": "custom_value"
  },
  "current_user": {
    "id": 1,
    "usuario": "admin",
    "tipo": "admin",
    "activo": true
  },
  "authenticated": true
}
```

### GET /debug/config

Shows configuration affecting sessions:
- SECRET_KEY status (masked)
- Session type
- Cookie settings
- Environment variables
- Warnings for common misconfigurations

**Example**:
```bash
curl http://localhost:8080/debug/config
```

### GET /debug/redis

Tests Redis connection and shows statistics.

**Example**:
```bash
curl http://localhost:8080/debug/redis
```

**Response**:
```json
{
  "status": "ok",
  "message": "Redis connection successful",
  "stats": {
    "redis_version": "7.0.0",
    "uptime_in_seconds": 12345,
    "connected_clients": 5
  },
  "session_keys_count": 42
}
```

## Environment Variables

### Session Configuration

| Variable | Description | Default | Production |
|----------|-------------|---------|------------|
| `REDIS_URL` | Redis connection URL | None | **Required** |
| `SESSION_REDIS_URL` | Specific Redis URL for sessions | Uses `REDIS_URL` | Optional |
| `SECRET_KEY` | Flask secret key | "dev" | **Required** (unique) |
| `SESSION_COOKIE_SECURE` | Use secure cookies (HTTPS only) | False | True for HTTPS |
| `SESSION_COOKIE_SAMESITE` | SameSite cookie attribute | "Lax" | "Lax" or "Strict" |
| `NOW_LMS_DEBUG_ENDPOINTS` | Enable debug endpoints | 0 | 0 (disable) |

### Worker Configuration

| Variable | Description | Default | Recommendation |
|----------|-------------|---------|----------------|
| `NOW_LMS_WORKERS` | Number of worker processes | Auto-calculated | 2-4 for small sites |
| `NOW_LMS_THREADS` | Threads per worker | 1 | 2-4 |
| `WSGI_SERVER` | WSGI server (gunicorn/waitress) | waitress | gunicorn for Linux |

## Architecture Notes

### Flask-Session Initialization Order

NOW LMS ensures Flask-Session is initialized **before** Flask-Login:

1. Flask app created
2. **Flask-Session initialized** (`init_session()`)
3. Flask-Login initialized (`administrador_sesion.init_app()`)

This order is critical for proper session handling.

### Session Backends

```
┌─────────────────────────────────────────┐
│         Flask Application               │
├─────────────────────────────────────────┤
│  Flask-Session                          │
│  ├─ Testing: Default (cookie)           │
│  ├─ Production (preferred): Redis       │
│  └─ Production (fallback): CacheLib     │
└─────────────────────────────────────────┘
          │
          ├─ Redis ────────► Multi-worker safe ✓
          └─ FileSystemCache ─► Multi-worker compatible
                                (shared filesystem required)
```

## Additional Resources

- [Flask-Session Documentation](https://flask-session.readthedocs.io/)
- [Redis Quick Start](https://redis.io/docs/getting-started/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
- [NOW LMS Configuration Guide](configure.md)

## Security Notes

⚠️ **Never enable debug endpoints in production**:
```bash
# In production, ensure this is NOT set
unset NOW_LMS_DEBUG_ENDPOINTS
```

⚠️ **Never commit SECRET_KEY to version control**:
```bash
# Use environment variables or secure secrets management
export SECRET_KEY=$(openssl rand -hex 32)
```

⚠️ **Use HTTPS in production**:
```bash
export SESSION_COOKIE_SECURE=True
export NOW_LMS_FORCE_HTTPS=1
```
