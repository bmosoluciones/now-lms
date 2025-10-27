---
draft: false
date: 2025-10-10
slug: wsgi-session-storage
authors:
  - admin
categories:
  - Performance
  - System Administration
  - Deployment
  - WSGI
  - Gunicorn
  - Waitress
---

# WSGI Server Session Storage Configuration

## Problem

When running NOW LMS with production WSGI servers (Gunicorn multi-process or Waitress multi-threaded), users can experience erratic session behavior:

- Sometimes appeared logged in after authentication
- Sometimes appeared logged out after refresh
- "Already logged in" messages appeared inconsistently
- UI flickered between authenticated and anonymous states

## Root Cause

Both Gunicorn and Waitress can cause session issues, but for slightly different reasons:

### Gunicorn (Multi-Process)

Gunicorn spawns multiple worker processes (e.g., `gunicorn app:app --workers 4`), and each worker has its own memory space. Flask's default session handling uses signed cookies stored in each process's memory:

1. User logs in → Request handled by Worker 1 → Session created in Worker 1's memory
2. User refreshes page → Request handled by Worker 2 → Worker 2 doesn't know about the session → User appears logged out
3. User refreshes again → Request handled by Worker 1 → Session found → User appears logged in

### Waitress (Multi-Threaded)

Waitress uses a single process with multiple threads. While threads share memory, concurrent access to session data without proper synchronization can cause race conditions and inconsistent session state, especially under high load.

Both scenarios create "erratic" behavior where session state is inconsistent.

## Solution

Implement **shared session storage** that all workers/threads can safely access:

### 1. Redis (Preferred)

Redis provides optimal performance and is the recommended solution for production with both Gunicorn and Waitress:

- Fast in-memory storage
- Shared across all workers/threads
- Thread-safe operations
- Persistent across server restarts
- Supports session expiration

### 2. Filesystem (Fallback)

When Redis is not available, filesystem-based sessions work for both servers as long as they share the same filesystem:

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

Then run your WSGI server of choice:

```bash
# Using Waitress (default)
lmsctl serve

# Using Gunicorn
lmsctl serve --wsgi-server gunicorn

# Or directly
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

- **SESSION_PERMANENT**: False (sessions expire when browser closes, but PERMANENT_SESSION_LIFETIME still applies)
- **SESSION_USE_SIGNER**: True (sessions are cryptographically signed for security)
- **PERMANENT_SESSION_LIFETIME**: 86400 seconds (24 hours)
- **SESSION_KEY_PREFIX**: "session:" (for Redis, to namespace keys)
- **SESSION_COOKIE_HTTPONLY**: True (prevents JavaScript access to session cookie)
- **SESSION_COOKIE_SECURE**: True in production (enforces HTTPS)
- **SESSION_COOKIE_SAMESITE**: "Lax" (protects against CSRF attacks)
- **SESSION_FILE_THRESHOLD**: 1000 (maximum number of sessions before cleanup)

## Files Modified

1. **`requirements.txt`**: Added `flask-session` dependency
2. **`now_lms/session_config.py`**: Session configuration with cookie security settings
3. **`now_lms/__init__.py`**: Integrated session initialization
4. **`now_lms/config/__init__.py`**: Added SECRET_KEY warning
5. **`run.py`**: Waitress configuration with shared session storage
6. **`now_lms/cli.py`**: Both Gunicorn and Waitress configuration with shared session storage

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

## WSGI Server Configuration

NOW LMS has built-in configuration for both Waitress and Gunicorn in `run.py` and `now_lms/cli.py` with optimal settings for session handling:

### Waitress Configuration

```python
# Key configurations for session support
serve(
    lms_app,
    host="0.0.0.0",
    port=PORT,
    threads=threads,  # Automatically calculated based on system resources
    channel_timeout=120,
    cleanup_interval=30,
)
```

**Important**: 
- Waitress is single-process, multi-threaded
- Thread count is automatically calculated based on CPU and RAM
- Works well with both Redis and filesystem sessions
- Cross-platform (Windows, Linux, macOS)

### Gunicorn Configuration

```python
# Key configurations for session support
options = {
    "preload_app": True,  # Load app before forking workers
    "workers": workers,  # Intelligent calculation based on CPU and RAM
    "threads": threads,  # Default 1, can be >1 for more concurrency
    "worker_class": "gthread" if threads > 1 else "sync",
    "graceful_timeout": 30,
}
```

**Important**: 
- `preload_app = True` ensures consistent app configuration across all workers
- Works with both Redis and filesystem sessions
- Worker/thread counts are automatically calculated based on system resources
- Linux/Unix only (not supported on Windows)

## WSGI Server Best Practices

### Using the CLI Command

The recommended way to run NOW LMS is using the built-in CLI:

```bash
# Using Waitress (default, cross-platform)
lmsctl serve

# Using Gunicorn (Linux/Unix only)
lmsctl serve --wsgi-server gunicorn
```

Or directly with Python:

```bash
# Uses Waitress by default
python run.py
```

The CLI command automatically configures your chosen WSGI server with:
- Intelligent worker/thread calculation based on CPU and RAM
- Environment variable support (NOW_LMS_WORKERS, NOW_LMS_THREADS)
- Proper session storage configuration

### With Environment Variables

```bash
export SECRET_KEY="your-secret-key"
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export NOW_LMS_WORKERS=4  # For Gunicorn only
export NOW_LMS_THREADS=4  # For both Waitress and Gunicorn

# Using Waitress (default)
lmsctl serve

# Using Gunicorn
lmsctl serve --wsgi-server gunicorn
```

### Advanced: Direct Server Commands

#### Waitress
```bash
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 now_lms:lms_app
```

#### Gunicorn
```bash
gunicorn "now_lms:lms_app" --workers 4 --threads 2 --bind 0.0.0.0:8000
```

Note: Using the CLI command (`lmsctl serve`) is recommended as it automatically configures the server with optimal settings.

### Worker/Thread Count Recommendations

NOW LMS automatically calculates optimal counts, but you can override:

#### For Gunicorn (Multi-Process)
- **CPU-bound workloads**: `workers = (2 × CPU cores) + 1`
- **I/O-bound workloads**: Use more threads per worker instead

Example for 4 CPU cores:
```bash
export NOW_LMS_WORKERS=9
lmsctl serve --wsgi-server gunicorn
```

#### For Waitress (Single-Process Multi-Threaded)
- **Threads**: Automatically calculated based on available RAM and CPU
- **I/O-bound workloads**: Can benefit from higher thread counts

Example:
```bash
export NOW_LMS_THREADS=8
lmsctl serve
```

### Additional Server Options

#### Gunicorn with Timeout
```bash
gunicorn "now_lms:lms_app" --workers 4 --timeout 120 --bind 0.0.0.0:8000
```

#### Waitress with Custom Settings
```bash
waitress-serve --host=0.0.0.0 --port=8000 --threads=8 --channel-timeout=120 now_lms:lms_app
```

## Monitoring

Check logs for session configuration:

```
INFO: Configuring Redis-based session storage for multi-worker/multi-threaded WSGI servers
INFO: Session storage initialized: redis
INFO: Using Redis for session storage - optimal for multi-worker WSGI servers
```

or

```
INFO: Configuring CacheLib FileSystemCache-based session storage for multi-worker/multi-threaded WSGI servers
INFO: Session storage initialized: cachelib
INFO: Session cache directory: /tmp/now_lms_sessions
```

## Troubleshooting

### Sessions still erratic with Redis

1. Verify Redis is running: `redis-cli ping` (should return "PONG")
2. Check Redis URL is correct: `echo $REDIS_URL`
3. Verify SECRET_KEY is set and stable: `echo $SECRET_KEY`
4. Check WSGI server logs for session initialization messages

### Sessions not persisting

1. Check SECRET_KEY is not "dev": `echo $SECRET_KEY`
2. If using filesystem storage, verify `/tmp/now_lms_sessions` (or `/dev/shm/now_lms_sessions`) is writable
3. Check session expiration (default 24 hours)

### Redis connection errors

If Redis is configured but not available:

```bash
# Temporarily disable Redis to use filesystem fallback
unset REDIS_URL
unset SESSION_REDIS_URL
```

## Choosing Between Waitress and Gunicorn

Both servers work well with NOW LMS and support the same session storage configuration:

### Use Waitress When:
- Running on Windows (Gunicorn not supported)
- Want simple, single-process deployment
- Prefer Python-only dependencies
- Need cross-platform compatibility
- Single server with moderate traffic

### Use Gunicorn When:
- Running on Linux/Unix
- Need multiple worker processes for better CPU utilization
- Want traditional Unix-style process management
- High-traffic production environment
- Want to use `preload_app` for memory efficiency

### Switching Between Servers

The configuration is designed to work seamlessly with both:

```bash
# No configuration changes needed!

# Using Waitress
lmsctl serve

# Using Gunicorn
lmsctl serve --wsgi-server gunicorn
```

Session storage configuration is shared and works identically with both servers.

## Performance

### Redis vs Filesystem

| Feature | Redis | Filesystem |
|---------|-------|------------|
| Speed | Very Fast | Moderate |
| Scalability | Excellent | Limited |
| Multi-server | Yes | No |
| Persistence | Configurable | Yes |
| Setup | Requires Redis | No setup |
| Thread-safe | Yes | Yes (with proper locking) |

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
