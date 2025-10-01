#!/bin/bash

# Test profiling script to identify slow tests and optimization opportunities
# Use this to analyze test performance and identify bottlenecks

# Unset environment variables that could affect test behavior
unset NOW_LMS_DATA_DIR
unset NOW_LMS_THEMES_DIR
unset NOW_LMS_LANG
unset NOW_LMS_CURRENCY
unset NOW_LMS_TIMEZONE

echo -------------------------------------------------
echo Profile test execution - identify slow tests
echo -------------------------------------------------
echo

pybabel compile -d now_lms/translations

echo "Running tests with detailed timing information..."
echo

# Run tests with detailed durations (top 30 slowest)
CI=True pytest --tb=short -q -n auto --durations=30

echo
echo -------------------------------------------------
echo Profile complete
echo -------------------------------------------------
