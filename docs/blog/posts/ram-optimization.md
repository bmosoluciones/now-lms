---
draft: false
date: 2025-10-05
slug: ram-optimization-guide
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

# RAM Optimization Guide for NOW LMS

This guide explains how NOW LMS automatically optimizes RAM usage through intelligent worker and thread configuration for production WSGI servers (Gunicorn and Waitress).

## Overview

NOW LMS implements RAM-aware configuration that automatically calculates the optimal number of workers and threads based on:

- Available system RAM
- Number of CPU cores
- Estimated memory per worker/thread
- Thread configuration
- WSGI server being used

This ensures the application doesn't consume more RAM than available, preventing crashes and performance issues.

<!-- more -->

## How It Works

### Automatic Worker/Thread Calculation

The system follows this formula for both Gunicorn and Waitress:

1. **CPU-based calculation**: `(cpu_count * 2) + 1`
2. **RAM-based calculation**: `available_ram_mb / worker_memory_mb`
3. **Final optimal value**: `min(cpu_based, ram_based)`
4. **With threads**: `optimal / threads` (rounded down, minimum 1)

**For Gunicorn**: Calculates both workers and threads
**For Waitress**: Calculates threads only (single-process server)

### Example Calculations

#### Example 1: Balanced System
- CPU: 4 cores
- RAM: 2 GB (2048 MB)
- Worker memory: 200 MB (default)

**Calculation (applies to both Gunicorn and Waitress):**
```
CPU-based: (4 * 2) + 1 = 9 
RAM-based: 2048 / 200 = 10
Optimal: min(9, 10) = 9

For Gunicorn: 9 workers with 1 thread each
For Waitress: 9 threads (single process)
```

#### Example 2: Low RAM System
- CPU: 4 cores
- RAM: 1 GB (1024 MB)
- Worker memory: 200 MB

**Calculation:**
```
CPU-based: (4 * 2) + 1 = 9
RAM-based: 1024 / 200 = 5
Optimal: min(9, 5) = 5 (RAM-limited)

For Gunicorn: 5 workers with 1 thread each
For Waitress: 5 threads (single process)
```

#### Example 3: Using Threads to Save RAM (Gunicorn)
- CPU: 4 cores
- RAM: 1 GB (1024 MB)
- Worker memory: 200 MB
- Threads: 4

**Calculation:**
```
CPU-based: (4 * 2) + 1 = 9
RAM-based: 1024 / 200 = 5
Base optimal: min(9, 5) = 5
With threads: 5 / 4 = 1 worker with 4 threads (minimum enforced)
Total capacity: 4 concurrent requests
```

#### Example 4: High Thread Count (Waitress)
- CPU: 2 cores
- RAM: 512 MB
- Worker memory: 200 MB
- Threads: 8

**Calculation:**
```
CPU-based: (2 * 2) + 1 = 5
RAM-based: 512 / 200 = 2
Optimal: min(5, 2) = 2

For Waitress: 8 threads (explicitly set, single process)
Estimated RAM: ~200 MB (single process)
```

## Configuration Options

### Environment Variables

#### NOW_LMS_WORKERS / WORKERS
- **Type**: Integer
- **Default**: Auto-calculated based on RAM and CPU
- **Description**: Number of worker processes for Gunicorn
- **Example**: `NOW_LMS_WORKERS=4` or `WORKERS=4`
- **Compatibility**: Both `NOW_LMS_WORKERS` (preferred) and `WORKERS` are supported
- **Note**: Only applies to Gunicorn; Waitress is single-process

When set, this overrides automatic calculation. Use this when you know your specific requirements.

#### NOW_LMS_THREADS / THREADS
- **Type**: Integer
- **Default**: Auto-calculated based on RAM and CPU
- **Description**: Number of threads for concurrent request handling
- **Example**: `NOW_LMS_THREADS=4` or `THREADS=4`
- **Compatibility**: Both `NOW_LMS_THREADS` (preferred) and `THREADS` are supported
- **Note**: For Waitress, this sets total threads; for Gunicorn, threads per worker

Setting threads > 1:
- For Gunicorn: Automatically switches to `gthread` worker class and reduces worker count proportionally to save RAM
- For Waitress: Sets the total number of threads in the single process
- Better for I/O-bound applications

#### NOW_LMS_WORKER_MEMORY_MB / WORKER_MEMORY_MB
- **Type**: Integer
- **Default**: 200
- **Description**: Estimated memory usage per worker/process in MB
- **Example**: `NOW_LMS_WORKER_MEMORY_MB=250` or `WORKER_MEMORY_MB=250`
- **Compatibility**: Both `NOW_LMS_WORKER_MEMORY_MB` (preferred) and `WORKER_MEMORY_MB` are supported
- **Note**: Affects automatic calculation for both Gunicorn workers and Waitress threads

Adjust this based on your application's actual memory usage. To measure:

```bash
# For Gunicorn
ps aux | grep gunicorn

# For Waitress
ps aux | grep waitress
```

#### LMS_PORT / PORT
- **Type**: Integer
- **Default**: 8080
- **Description**: Port number for the server
- **Example**: `LMS_PORT=8080`

## Deployment Scenarios

### Scenario 1: Production Server (8 GB RAM, 4 cores)

**No configuration needed** - automatic calculation works well:
```bash
# Using Waitress (default)
venv/bin/lmsctl serve

# Using Gunicorn
venv/bin/lmsctl serve --wsgi-server gunicorn
```

Expected configuration:
- **Waitress**: 9 threads, single process, ~200 MB RAM
- **Gunicorn**: 9 workers, 1 thread each, ~1.8 GB RAM

### Scenario 2: Small VPS (1 GB RAM, 2 cores)

Use threads for better concurrency with less RAM:
```bash
export NOW_LMS_THREADS=4

# Using Waitress (recommended for small VPS)
venv/bin/lmsctl serve
```

Expected configuration:
- **Waitress**: 4 threads, single process, ~200 MB RAM
- **Gunicorn**: 1 worker with 4 threads, ~200 MB RAM

### Scenario 3: Container with Limited RAM (512 MB, 2 cores)

Waitress is ideal for constrained environments:
```bash
export NOW_LMS_THREADS=4
export NOW_LMS_WORKER_MEMORY_MB=150

# Using Waitress (recommended for containers)
venv/bin/lmsctl serve
```

Expected configuration:
- **Waitress**: 4 threads, single process, ~150 MB RAM
- **Gunicorn** (alternative): 1 worker, 4 threads, ~150 MB RAM

### Scenario 4: High-Traffic Server (16 GB RAM, 8 cores)

Gunicorn with multiple workers for maximum throughput:
```bash
export NOW_LMS_WORKER_MEMORY_MB=300

# Using Gunicorn for multi-process
venv/bin/lmsctl serve --wsgi-server gunicorn
```

Expected configuration:
- **Gunicorn**: 17 workers (CPU-based: (8*2)+1), 1 thread each, ~5.1 GB RAM
- **Waitress** (alternative): 17 threads, single process, ~300 MB RAM

With threads for even more concurrency (Gunicorn):
```bash
export NOW_LMS_THREADS=2
export NOW_LMS_WORKER_MEMORY_MB=300
venv/bin/lmsctl serve --wsgi-server gunicorn
```

Expected configuration:
- Workers: 8 (17/2)
- Threads: 2 per worker
- Estimated RAM: ~2.4 GB
- Total concurrent capacity: 16 requests

## Best Practices

### 1. Monitor Your Application

Always monitor actual RAM usage to tune settings:

```bash
# Check total system memory
free -m

# Monitor WSGI server processes
ps aux | grep -E "(gunicorn|waitress)" | awk '{sum+=$6} END {print "Total RAM: " sum/1024 " MB"}'

# Use htop for interactive monitoring
htop
```

### 2. Start Conservative

When deploying to a new environment:
1. Use default settings initially
2. Monitor RAM usage for 24-48 hours
3. Adjust `NOW_LMS_WORKER_MEMORY_MB` based on actual usage
4. Consider adding threads if CPU is underutilized

### 3. I/O-Bound vs CPU-Bound

**For I/O-bound applications** (database queries, API calls):
- Use more threads per worker
- Reduces total RAM usage
- Better concurrency during I/O waits

**For CPU-bound applications** (heavy processing):
- Use more workers with fewer threads
- Better CPU utilization
- More predictable performance

### 4. Leave Headroom

Don't use 100% of available RAM:
- Leave 20-30% for OS and other processes
- Account for traffic spikes
- Consider peak usage patterns

### 5. Container Deployments

For Docker/Kubernetes:
- Set explicit limits using `NOW_LMS_WORKERS` and `NOW_LMS_THREADS`
- Don't rely solely on automatic calculation
- Test memory limits before deploying

Example Dockerfile configuration:
```dockerfile
ENV NOW_LMS_WORKERS=2
ENV NOW_LMS_THREADS=4
ENV NOW_LMS_WORKER_MEMORY_MB=150
```

## Troubleshooting

### Application Crashes with OOMKilled

**Symptoms**: Container/process killed by OS due to out-of-memory

**Solutions**:
1. Reduce workers: `export NOW_LMS_WORKERS=1`
2. Use threads: `export NOW_LMS_THREADS=4`
3. Lower worker memory estimate: `export NOW_LMS_WORKER_MEMORY_MB=150`
4. Check for memory leaks in application code

### Slow Response Times

**Symptoms**: High latency, timeouts

**Solutions**:
1. Increase workers if RAM allows
2. Add threads for I/O-bound workloads
3. Monitor worker utilization
4. Consider scaling horizontally

### Workers Dying/Restarting

**Symptoms**: Workers restart frequently, error logs

**Solutions**:
1. Check application logs for errors
2. Increase timeout: Add `--timeout 240` to Gunicorn config
3. Monitor memory per worker
4. Reduce workers if causing memory pressure

## Measuring Worker Memory

To accurately measure worker memory usage:

```bash
# Method 1: Using ps
ps aux | grep "gunicorn: worker" | awk '{print $6}' | \
  awk '{sum+=$1; count++} END {print "Average: " sum/count/1024 " MB"}'

# Method 2: Using memory_profiler (requires installation)
python -m memory_profiler run.py

# Method 3: Using psutil in Python
python -c "
import psutil
import os
proc = psutil.Process(os.getpid())
print(f'Memory: {proc.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## Advanced Configuration

### Custom run.py Script

If using custom `run.py` instead of `lmsctl`:

```python
from os import environ
from now_lms import lms_app, init_app
from now_lms.worker_config import get_worker_config_from_env

if init_app():
    from gunicorn.app.base import BaseApplication
    
    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()
        
        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)
        
        def load(self):
            return self.application
    
    # Get optimal configuration
    workers, threads = get_worker_config_from_env()
    
    options = {
        "bind": "0.0.0.0:8080",
        "workers": workers,
        "threads": threads,
        "worker_class": "gthread" if threads > 1 else "sync",
        "timeout": 120,
        "accesslog": "-",
        "errorlog": "-",
    }
    
    print(f"Starting with {workers} workers and {threads} threads")
    StandaloneApplication(lms_app, options).run()
```

### Programmatic Configuration

For advanced use cases, use the API directly:

```python
from now_lms.worker_config import calculate_optimal_workers

# Calculate for specific constraints
workers = calculate_optimal_workers(
    worker_memory_mb=250,  # Your measured usage
    min_workers=2,         # Minimum for redundancy
    max_workers=8,         # Maximum for your setup
    threads=2              # Threads per worker
)

print(f"Optimal workers: {workers}")
```

## Related Documentation

- [Configuration Guide](../../setup-conf.md) - Full configuration reference
- [Performance Tuning](../../test-performance.md) - Application performance optimization

## References

- [Gunicorn Design](https://docs.gunicorn.org/en/stable/design.html)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Python psutil Documentation](https://psutil.readthedocs.io/)
