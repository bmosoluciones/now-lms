#!/bin/bash

# Fast test execution script that skips slow/comprehensive tests
# Use this during development for quick feedback

# Unset environment variables that could affect test behavior
# This ensures tests run in a clean environment
unset NOW_LMS_DATA_DIR
unset NOW_LMS_THEMES_DIR
unset NOW_LMS_LANG
unset NOW_LMS_CURRENCY
unset NOW_LMS_TIMEZONE

echo -------------------------------------------------
echo Run FAST tests - skipping slow/comprehensive tests
echo -------------------------------------------------
echo
pybabel compile -d now_lms/translations
# Run without coverage for maximum speed during development
CI=True pytest --tb=short -q -m "not slow and not comprehensive" --durations=5