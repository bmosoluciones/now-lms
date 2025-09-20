# Test Performance Optimization

This document describes the test performance optimizations implemented to reduce test execution time.

## Performance Improvements

### Baseline Performance
- **Original execution time**: 3m46s (226 seconds)
- **Total tests**: ~305 tests across 88 test files

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

### Dependencies Added
- `pytest-xdist`: Parallel test execution
- Updated `test.txt` to include the new dependency

### Configuration Files Updated
- `pytest.ini`: Added test markers configuration
- `dev/test.sh`: Added parallel execution (`-n auto`)
- `dev/test_fast.sh`: New fast test configuration script