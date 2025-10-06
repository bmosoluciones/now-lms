# Gunicorn Session Storage Configuration

## Problem

When switching from Waitress (single-threaded server) to Gunicorn (multi-process server), users experienced erratic session behavior:

- Sometimes appeared logged in after authentication
- Sometimes appeared logged out after refresh
- "Already logged in" messages appeared inconsistently
- UI flickered between authenticated and anonymous states

## Root Cause

Gunicorn spawns multiple worker processes by default (e.g., `gunicorn app:app --workers 4`), and each worker has its own memory space. Flask's default session handling uses signed cookies stored in each process's memory, which causes issues:

1. User logs in → Request handled by Worker 1 → Session created in Worker 1's memory
2. User refreshes page → Request handled by Worker 2 → Worker 2 doesn't know about the session → User appears logged out
3. User refreshes again → Request handled by Worker 1 → Session found → User appears logged in

This creates the "erratic" behavior where session state is inconsistent.

## Solution

Implement **shared session storage** that all Gunicorn workers can access:

### 1. Redis (Preferred)

Redis provides optimal performance and is the recommended solution for production:

- Fast in-memory storage
- Shared across all workers
- Persistent across server restarts
- Supports session expiration

### 2. Filesystem (Fallback)

When Redis is not available, filesystem-based sessions work as long as all workers share the same filesystem:

- Sessions stored in `/tmp/now_lms_sessions/`
- Slower than Redis but functional
- Works for single-server deployments

### 3. Testing Mode

During tests (when pytest is detected), the system uses Flask's default signed cookie sessions since tests run in a single process.

## Configuration

### Automatic Configuration

The system automatically detects the best available session storage:

```python
# Priority order:
1. Redis (if REDIS_URL or SESSION_REDIS_URL is set)
2. Filesystem (if not in testing mode)
3. Default Flask sessions (for testing)
```

### Redis Configuration

Set the Redis URL in your environment:

```bash
export REDIS_URL=redis://localhost:6379/0
# or
export SESSION_REDIS_URL=redis://localhost:6379/0
```

Then run Gunicorn:

```bash
gunicorn "now_lms:lms_app" --workers 4 --bind 0.0.0.0:8000
```

### Without Redis

If Redis is not available, the system will automatically use filesystem storage. No configuration needed.

### SECRET_KEY (Critical!)

**ALWAYS** set a stable SECRET_KEY in production:

```bash
export SECRET_KEY="your-long-random-secret-key-here"
```

⚠️ **Never use the default "dev" SECRET_KEY in production!** This will cause session issues even with shared storage.

Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Session Settings

All session storage backends use these production-ready settings:

- **SESSION_PERMANENT**: True (sessions persist across browser restarts)
- **SESSION_USE_SIGNER**: True (sessions are cryptographically signed for security)
- **PERMANENT_SESSION_LIFETIME**: 86400 seconds (24 hours)
- **SESSION_KEY_PREFIX**: "session:" (for Redis, to namespace keys)

## Files Modified

1. **`requirements.txt`**: Added `flask-session` dependency
2. **`now_lms/session_config.py`**: New module for session configuration
3. **`now_lms/__init__.py`**: Integrated session initialization
4. **`now_lms/config/__init__.py`**: Added SECRET_KEY warning

## Testing

Run the session configuration tests:

```bash
pytest tests/test_session_gunicorn.py -v
```

Tests verify:
- Redis configuration when REDIS_URL is set
- Filesystem fallback when Redis is unavailable
- Proper settings for production use
- Session persistence across requests

## Gunicorn Best Practices

### Basic Command

```bash
gunicorn "now_lms:lms_app" --workers 4 --threads 2 --bind 0.0.0.0:8000
```

### With Environment Variables

```bash
export SECRET_KEY="your-secret-key"
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

gunicorn "now_lms:lms_app" --workers 4 --bind 0.0.0.0:8000
```

### Worker Count

Choose worker count based on your server:

- **CPU-bound**: `workers = (2 × CPU cores) + 1`
- **I/O-bound**: `workers = (4 × CPU cores) + 1`

Example for 4 CPU cores:
```bash
gunicorn "now_lms:lms_app" --workers 9 --bind 0.0.0.0:8000
```

### With Timeout

```bash
gunicorn "now_lms:lms_app" --workers 4 --timeout 120 --bind 0.0.0.0:8000
```

## Monitoring

Check logs for session configuration:

```
INFO: Configuring Redis-based session storage for Gunicorn workers
INFO: Session storage initialized: redis
INFO: Using Redis for session storage - optimal for Gunicorn
```

or

```
INFO: Configuring filesystem-based session storage for Gunicorn workers
INFO: Session storage initialized: filesystem
INFO: Session directory: /tmp/now_lms_sessions
```

## Troubleshooting

### Sessions still erratic with Redis

1. Verify Redis is running: `redis-cli ping` (should return "PONG")
2. Check Redis URL is correct: `echo $REDIS_URL`
3. Verify SECRET_KEY is set and stable: `echo $SECRET_KEY`
4. Check Gunicorn logs for session initialization messages

### Sessions not persisting

1. Check SECRET_KEY is not "dev": `echo $SECRET_KEY`
2. If using filesystem storage, verify `/tmp/now_lms_sessions` is writable
3. Check session expiration (default 24 hours)

### Redis connection errors

If Redis is configured but not available:

```bash
# Temporarily disable Redis to use filesystem fallback
unset REDIS_URL
unset SESSION_REDIS_URL
```

## Migration from Waitress

When migrating from Waitress to Gunicorn:

1. **Set SECRET_KEY** (if not already set)
2. **Install Redis** (recommended) or accept filesystem fallback
3. **Update deployment command** from `waitress-serve` to `gunicorn`
4. **Test with multiple workers** to verify session persistence

## Performance

### Redis vs Filesystem

| Feature | Redis | Filesystem |
|---------|-------|------------|
| Speed | Very Fast | Moderate |
| Scalability | Excellent | Limited |
| Multi-server | Yes | No |
| Persistence | Configurable | Yes |
| Setup | Requires Redis | No setup |

### Recommendations

- **Single server, low traffic**: Filesystem is sufficient
- **Single server, high traffic**: Use Redis
- **Multiple servers**: Use Redis (required)
- **Development**: Either works
- **Testing**: Automatic (no configuration needed)

## Security Notes

1. **Always use HTTPS in production** - sessions are transmitted in cookies
2. **Set SECRET_KEY to a strong, random value** - never use "dev"
3. **Enable SESSION_USE_SIGNER** (automatic) - prevents session tampering
4. **Use Redis with authentication** if exposed to network
5. **Rotate SECRET_KEY periodically** - invalidates all sessions

## References

- [Flask-Session Documentation](https://flask-session.readthedocs.io/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Redis Documentation](https://redis.io/documentation)
