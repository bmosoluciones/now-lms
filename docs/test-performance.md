# Test Performance Optimization

This document describes the test performance optimizations implemented to reduce test execution time.

## Table of Contents
1. [Performance Improvements](#performance-improvements)
2. [Usage](#usage)
3. [Best Practices for Contributors](#best-practices-for-contributors)
4. [Configuration](#configuration)

## Performance Improvements

### Baseline Performance
- **Original execution time**: 3m46s (226 seconds)
- **Total tests**: ~305 tests across 90 test files

### Optimizations Implemented

#### 1. Parallel Test Execution
- **Added**: `pytest-xdist` plugin for parallel test execution
- **Configuration**: `-n auto` automatically detects CPU cores and runs tests in parallel
- **Impact**: ~40% reduction in full test suite execution time
- **New full test time**: 2m14s (134 seconds)

#### 2. Test Categorization with Pytest Marks
- **Added marks**:
  - `@pytest.mark.slow`: For tests taking >1.5 seconds
  - `@pytest.mark.comprehensive`: For comprehensive route/integration tests
  - `@pytest.mark.integration`: For integration tests requiring full setup
  - `@pytest.mark.unit`: For fast unit tests (planned)

#### 3. Fast Test Configuration
- **New script**: `dev/test_fast.sh`
- **Purpose**: Skip slow/comprehensive tests during development
- **Command**: `-m "not slow and not comprehensive"`
- **Performance**: 1m30s (90 seconds) - **60% reduction** from baseline
- **Coverage**: Disabled in fast mode for maximum speed

#### 4. Route Testing Optimizations
- **Route caching**: Added class-level caching to avoid rediscovering routes
- **Marked as slow**: Comprehensive route tests marked to allow selective skipping

#### 5. Test Timeout Configuration
- **Added**: `pytest-timeout` plugin to prevent hanging tests
- **Configuration**: 300-second (5 minute) timeout per test
- **Method**: Thread-based timeout for better compatibility
- **Impact**: Prevents test suite hangs, improves reliability in CI/CD
- **Benefit**: Early detection of infinite loops or deadlocks

#### 6. SQLite Performance Optimizations
- **Optimized PRAGMA settings** for in-memory test databases:
  - `journal_mode=MEMORY`: Use memory journaling instead of WAL for speed
  - `synchronous=NORMAL`: Reduced from FULL for faster writes (safe for in-memory)
  - `cache_size=-10000`: Increased cache to 10MB for better performance
  - `temp_store=MEMORY`: Keep temporary tables in memory
  - `auto_vacuum=NONE`: Disable auto-vacuum for faster operations
  - `page_size=8192`: Increased from default 4096 for better performance
  - `locking_mode=EXCLUSIVE`: Use exclusive locking for single-connection in-memory DBs
- **Impact**: ~10-15% reduction in database-heavy test execution time
- **Safety**: All changes are safe for in-memory test databases while maintaining data integrity

#### 7. Test Profiling Tools
- **New script**: `dev/profile_tests.sh`
- **Purpose**: Identify slow tests and optimization opportunities
- **Shows**: Top 30 slowest test durations with timing breakdown

### Usage

#### Full Test Suite (CI/Production)
```bash
# With coverage and all tests (2m14s)
bash dev/test.sh

# Or directly with pytest
CI=True pytest --tb=short -q --cov=now_lms -n auto
```

#### Fast Development Testing (1m30s)
```bash
# Skip slow/comprehensive tests, no coverage
bash dev/test_fast.sh

# Or directly with pytest
CI=True pytest --tb=short -q -n auto -m "not slow and not comprehensive"
```

#### Selective Testing
```bash
# Run only comprehensive tests
pytest -m "comprehensive"

# Run only slow tests
pytest -m "slow"

# Run only fast tests (excluding slow and comprehensive)
pytest -m "not slow and not comprehensive"

# Run specific test categories
pytest -m "integration"
```

### Test Categories

#### Slow Tests (`@pytest.mark.slow`)
- Comprehensive route testing (all 207 routes)
- Demo mode configuration tests
- Large integration workflows
- End-to-end admin flows

#### Comprehensive Tests (`@pytest.mark.comprehensive`)
- Complete route discovery and testing
- Full application workflow testing
- Multi-user scenario testing

### Performance Summary

| Configuration | Time | Reduction | Use Case |
|---------------|------|-----------|----------|
| Original | 3m46s | - | Baseline |
| Parallel (full) | 2m14s | 40% | CI/Production |
| Fast (parallel, no slow tests, no coverage) | 1m30s | 60% | Development |
| With SQLite + timeout optimizations | ~2m0s | ~45% | CI/Production (improved) |

### Dependencies Added
- `pytest-xdist`: Parallel test execution
- `pytest-timeout`: Test timeout handling to prevent hangs
- `pytest-benchmark`: Performance profiling and benchmarking
- Updated `test.txt` to include all dependencies

### Configuration Files Updated
- `pytest.ini`: Added test markers configuration, timeout settings (300s per test), and strict markers
- `tests/conftest.py`: Optimized SQLite PRAGMA settings for in-memory databases
- `dev/test.sh`: Added parallel execution (`-n auto`)
- `dev/test_fast.sh`: New fast test configuration script
- `dev/profile_tests.sh`: New test profiling script for performance analysis

## Best Practices for Contributors

### Writing Fast Tests

#### 1. Use Session-Scoped Fixtures When Possible
Session-scoped fixtures are created once per test session and shared across tests, significantly reducing setup time.

**Available session fixtures:**
- `session_basic_db_setup`: Minimal database setup with basic configuration and certificates
- `session_full_db_setup`: Full database setup with users, courses, and test data
- `session_full_db_setup_with_examples`: Full setup including example data

**When to use:**
```python
# ✅ Good: Read-only test using session fixture
def test_course_list(session_full_db_setup):
    """Test course list view."""
    client = session_full_db_setup.test_client()
    response = client.get('/course/list')
    assert response.status_code == 200

# ❌ Avoid: Modifying data with session fixture (can affect other tests)
def test_create_course(session_full_db_setup):
    # This could break other tests!
    pass

# ✅ Good: Use isolated_db_session for tests that modify data
def test_create_course(session_full_db_setup, isolated_db_session):
    """Test course creation with isolated session."""
    # Changes are rolled back after test
    pass
```

#### 2. Mark Tests Appropriately
Use pytest markers to categorize tests for selective execution:

```python
import pytest

@pytest.mark.unit
def test_simple_function():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_full_workflow(session_full_db_setup):
    """Integration test with database."""
    pass

@pytest.mark.slow
def test_comprehensive_routes(full_db_setup, client):
    """Slow test that tests many routes."""
    pass

@pytest.mark.comprehensive
def test_all_routes():
    """Comprehensive test of entire system."""
    pass
```

#### 3. Avoid Expensive Setup in Fast Tests
- Don't create users/data if session fixtures already provide them
- Reuse existing test data when possible
- Use `session_basic_db_setup` instead of `session_full_db_setup` if you only need minimal setup

#### 4. Profile Slow Tests
Use the profiling script to identify bottlenecks:
```bash
bash dev/profile_tests.sh
```

### Test Fixture Selection Guide

| Fixture | Setup Time | Use When | Data Available |
|---------|-----------|----------|----------------|
| `session_basic_db_setup` | ~0.3s | Need minimal config | Config, certificates |
| `session_full_db_setup` | ~0.7s | Read-only, need users/courses | Users, courses, test data |
| `session_full_db_setup_with_examples` | ~1.5s | Need complete data | All data + examples |
| `app` | ~0.1s | Need clean database each time | Empty database |
| `full_db_setup` | ~0.8s | Need to modify data | Users, courses, test data |

### Running Tests Efficiently

```bash
# During development - skip slow tests (1m30s)
bash dev/test_fast.sh

# Before committing - run all tests with coverage (2m14s)
bash dev/test.sh

# Profile test performance
bash dev/profile_tests.sh

# Run only integration tests
pytest -m "integration"

# Skip slow and comprehensive tests
pytest -m "not slow and not comprehensive"

# Run specific test file with timing
pytest tests/test_myfeature.py --durations=10
```

### Contributing Guidelines

When adding new tests:
1. **Choose the right fixture**: Use session fixtures for read-only tests
2. **Add markers**: Mark slow (>1.5s) and integration tests appropriately
3. **Keep tests focused**: Test one thing per test when possible
4. **Avoid redundant setup**: Reuse existing data from session fixtures
5. **Profile your tests**: Run `dev/profile_tests.sh` to check performance impact