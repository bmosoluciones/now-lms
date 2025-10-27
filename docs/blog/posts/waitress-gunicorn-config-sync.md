---
draft: false
date: 2025-10-27
slug: waitress-gunicorn-config-sync
authors:
  - admin
categories:
  - Development
  - System Administration
  - Deployment
  - WSGI
  - Gunicorn
  - Waitress
---

# Synchronized Configuration for Waitress and Gunicorn

We've improved NOW LMS to ensure both Waitress and Gunicorn WSGI servers work seamlessly out-of-the-box with identical configuration.

<!-- more -->

## What Changed?

Previously, the codebase and documentation focused primarily on Gunicorn, with Waitress treated as a secondary option. This update brings both servers to equal status with fully synchronized configuration.

### Code Updates

1. **Session Configuration (`session_config.py`)**
   - Updated all log messages and docstrings to mention "multi-worker/multi-threaded WSGI servers" instead of just "Gunicorn"
   - Session storage (Redis or filesystem) now explicitly supports both servers
   - Clarified that shared session storage is needed for both multi-process (Gunicorn) and multi-threaded (Waitress) environments

2. **Worker Configuration (`worker_config.py`)**
   - Updated docstrings to clarify the formula is used by both servers
   - Made it clear that Gunicorn uses workers+threads while Waitress uses threads only
   - Both servers use the same `get_worker_config_from_env()` function

### Documentation Updates

1. **Setup Configuration Guide (`docs/setup-conf.md`)**
   - Updated environment variable descriptions to reflect both servers equally
   - Clarified which settings apply to which server
   - Added notes about server-specific behaviors (e.g., Waitress is single-process)

2. **Blog Posts**
   - Renamed "Gunicorn Session Storage Configuration" → "WSGI Server Session Storage Configuration"
   - Updated to cover both Waitress and Gunicorn session handling
   - Added comprehensive comparison and guidance for choosing between servers
   - Updated RAM Optimization Guide with Waitress examples and scenarios

## Shared Configuration

Both servers now use identical environment variables:

- `NOW_LMS_WORKERS` / `WORKERS` - Number of worker processes (Gunicorn only)
- `NOW_LMS_THREADS` / `THREADS` - Number of threads (both servers)
- `NOW_LMS_WORKER_MEMORY_MB` / `WORKER_MEMORY_MB` - Memory estimation for calculations (both servers)

### Worker/Thread Calculation Formula

Both servers use the same intelligent calculation:

```
CPU-based: (cpu_count * 2) + 1
RAM-based: available_ram_mb / worker_memory_mb
Optimal: min(cpu_based, ram_based)
With threads: optimal / threads (minimum 1)
```

**For Gunicorn**: Calculates both workers and threads
**For Waitress**: Calculates threads (single-process server)

## Usage Examples

### Default Configuration (Automatic)

Both servers automatically calculate optimal settings:

```bash
# Using Waitress (default, cross-platform)
lmsctl serve

# Using Gunicorn (Linux/Unix only)
lmsctl serve --wsgi-server gunicorn
```

### Custom Configuration

Set the same environment variables for both:

```bash
export NOW_LMS_THREADS=8
export NOW_LMS_WORKER_MEMORY_MB=250

# Works with both servers
lmsctl serve
lmsctl serve --wsgi-server gunicorn
```

## Server Comparison

| Feature | Waitress | Gunicorn |
|---------|----------|----------|
| Platform | Cross-platform | Linux/Unix only |
| Architecture | Single-process, multi-threaded | Multi-process, multi-threaded |
| Workers | N/A (single process) | Configurable |
| Threads | Configurable | Configurable per worker |
| RAM Usage | Lower (single process) | Higher (multiple processes) |
| CPU Utilization | Good for I/O-bound | Better for CPU-bound |

## Choosing a Server

### Use Waitress When:
- Running on Windows
- Want simple, single-process deployment
- Prefer lower memory footprint
- Need cross-platform compatibility
- Running in resource-constrained environments (containers, small VPS)

### Use Gunicorn When:
- Running on Linux/Unix
- Need multiple worker processes for CPU-intensive tasks
- Want traditional Unix-style process management
- High-traffic production environment with available RAM
- Want to leverage `preload_app` for memory efficiency

## Session Storage

Both servers support identical session storage configurations:

1. **Redis** (recommended): Fast, scalable, works with both servers
2. **Filesystem** (fallback): Works when Redis unavailable, thread-safe
3. **Testing mode**: Uses default Flask sessions (single-process tests)

Configuration is automatic - both servers detect and use the best available option.

## Migration Guide

If you were using Gunicorn and want to try Waitress (or vice versa):

```bash
# No configuration changes needed!

# From Gunicorn
lmsctl serve --wsgi-server gunicorn

# To Waitress
lmsctl serve
```

Session storage, worker/thread calculations, and all environment variables work identically.

## Testing

Added comprehensive tests to verify configuration synchronization:

- `test_wsgi_config_sync.py`: Validates both servers use the same configuration
- All 5 new tests pass
- Existing worker_config and session tests continue to pass
- 82% code coverage maintained

## Benefits

1. **Consistency**: Both servers use identical configuration approach
2. **Flexibility**: Easy to switch between servers without reconfiguration  
3. **Documentation**: Equal treatment of both servers in all docs
4. **Reliability**: Shared session storage works the same way for both
5. **Performance**: Same intelligent resource optimization for both

## Conclusion

With this update, NOW LMS treats Waitress and Gunicorn as equal first-class WSGI servers. Choose the one that best fits your deployment environment, knowing that configuration, session storage, and resource optimization work identically.

For detailed configuration options, see:
- [WSGI Server Session Storage Configuration](wsgi-session-storage)
- [RAM Optimization Guide](ram-optimization-guide)
- [Setup Configuration Guide](../../setup-conf.md)
