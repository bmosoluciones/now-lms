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
  - Gunicorn
---

# RAM Optimization Guide for NOW LMS

This guide explains how NOW LMS automatically optimizes RAM usage through intelligent worker and thread configuration for Gunicorn.

## Overview

NOW LMS implements RAM-aware worker configuration that automatically calculates the optimal number of workers and threads based on:

- Available system RAM
- Number of CPU cores
- Estimated memory per worker
- Thread configuration

This ensures the application doesn't consume more RAM than available, preventing crashes and performance issues.

<!-- more -->

## How It Works

### Automatic Worker Calculation

The system follows this formula:

1. **CPU-based calculation**: `(cpu_count * 2) + 1`
2. **RAM-based calculation**: `available_ram_mb / worker_memory_mb`
3. **Final workers**: `min(cpu_based, ram_based)`
4. **With threads**: `workers / threads` (rounded down, minimum 1)

### Example Calculations

#### Example 1: Balanced System
- CPU: 4 cores
- RAM: 2 GB (2048 MB)
- Worker memory: 200 MB (default)

**Calculation:**
```
CPU-based: (4 * 2) + 1 = 9 workers
RAM-based: 2048 / 200 = 10 workers
Result: min(9, 10) = 9 workers with 1 thread
```

#### Example 2: Low RAM System
- CPU: 4 cores
- RAM: 1 GB (1024 MB)
- Worker memory: 200 MB

**Calculation:**
```
CPU-based: (4 * 2) + 1 = 9 workers
RAM-based: 1024 / 200 = 5 workers
Result: min(9, 5) = 5 workers with 1 thread
```

#### Example 3: Using Threads to Save RAM
- CPU: 4 cores
- RAM: 1 GB (1024 MB)
- Worker memory: 200 MB
- Threads: 4

**Calculation:**
```
CPU-based: (4 * 2) + 1 = 9 workers
RAM-based: 1024 / 200 = 5 workers
Base optimal: min(9, 5) = 5 workers
With threads: 5 / 4 = 1 worker (minimum) with 4 threads
```

#### Example 4: Very Low RAM (512 MB)
- CPU: 2 cores
- RAM: 512 MB
- Worker memory: 200 MB
- Threads: 4

**Calculation:**
```
CPU-based: (2 * 2) + 1 = 5 workers
RAM-based: 512 / 200 = 2 workers
Base optimal: min(5, 2) = 2 workers
With threads: 2 / 4 = 0.5 → 1 worker (minimum enforced) with 4 threads
```

## Configuration Options

### Environment Variables

#### NOW_LMS_WORKERS / WORKERS
- **Type**: Integer
- **Default**: Auto-calculated based on RAM and CPU
- **Description**: Explicitly set the number of Gunicorn workers
- **Example**: `NOW_LMS_WORKERS=4` or `WORKERS=4`
- **Compatibility**: Both `NOW_LMS_WORKERS` (preferred) and `WORKERS` are supported

When set, this overrides automatic calculation. Use this when you know your specific requirements.

#### NOW_LMS_THREADS / THREADS
- **Type**: Integer
- **Default**: 1
- **Description**: Number of threads per worker
- **Example**: `NOW_LMS_THREADS=4` or `THREADS=4`
- **Compatibility**: Both `NOW_LMS_THREADS` (preferred) and `THREADS` are supported

Setting threads > 1:
- Automatically switches to `gthread` worker class
- Reduces worker count proportionally to save RAM
- Better for I/O-bound applications

#### NOW_LMS_WORKER_MEMORY_MB / WORKER_MEMORY_MB
- **Type**: Integer
- **Default**: 200
- **Description**: Estimated memory usage per worker in MB
- **Example**: `NOW_LMS_WORKER_MEMORY_MB=250` or `WORKER_MEMORY_MB=250`
- **Compatibility**: Both `NOW_LMS_WORKER_MEMORY_MB` (preferred) and `WORKER_MEMORY_MB` are supported

Adjust this based on your application's actual memory usage. To measure:

```bash
# Monitor memory usage of workers
ps aux | grep gunicorn
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
# Automatic: 9 workers, 1 thread
venv/bin/lmsctl serve
```

Expected configuration:
- Workers: 9 (CPU-limited)
- Threads: 1
- Estimated RAM: ~1.8 GB

### Scenario 2: Small VPS (1 GB RAM, 2 cores)

Use threads to reduce RAM usage:
```bash
export NOW_LMS_THREADS=4
venv/bin/lmsctl serve
```

Expected configuration:
- Workers: 1 (RAM-limited, adjusted for threads)
- Threads: 4
- Estimated RAM: ~200 MB

### Scenario 3: Container with Limited RAM (512 MB, 2 cores)

Explicitly limit workers and use threads:
```bash
export NOW_LMS_WORKERS=1
export NOW_LMS_THREADS=4
export NOW_LMS_WORKER_MEMORY_MB=150
venv/bin/lmsctl serve
```

Expected configuration:
- Workers: 1 (explicit)
- Threads: 4
- Estimated RAM: ~150 MB

### Scenario 4: High-Traffic Server (16 GB RAM, 8 cores)

Maximize workers for high concurrency:
```bash
export NOW_LMS_WORKER_MEMORY_MB=300
venv/bin/lmsctl serve
```

Expected configuration:
- Workers: 17 (CPU-based: (8*2)+1)
- Threads: 1
- Estimated RAM: ~5.1 GB

With threads for even more concurrency:
```bash
export NOW_LMS_THREADS=2
export NOW_LMS_WORKER_MEMORY_MB=300
venv/bin/lmsctl serve
```

Expected configuration:
- Workers: 8 (17/2)
- Threads: 2
- Estimated RAM: ~2.4 GB
- Total thread capacity: 16 concurrent requests

## Best Practices

### 1. Monitor Your Application

Always monitor actual RAM usage to tune settings:

```bash
# Check total system memory
free -m

# Monitor Gunicorn processes
ps aux | grep gunicorn | awk '{sum+=$6} END {print "Total RAM: " sum/1024 " MB"}'

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
