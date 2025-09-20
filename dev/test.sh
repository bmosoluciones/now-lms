#!/bin/bash

# Unset environment variables that could affect test behavior
# This ensures tests run in a clean environment
unset NOW_LMS_DATA_DIR
unset NOW_LMS_THEMES_DIR
unset NOW_LMS_LANG
unset NOW_LMS_CURRENCY
unset NOW_LMS_TIMEZONE

echo -------------------------------------------------
echo Check python code with flake8
echo -------------------------------------------------
echo
flake8 --max-line-length=120 --ignore=E501,E203,E266,W503,E722 now_lms
echo -------------------------------------------------
echo Check python code with ruff
echo -------------------------------------------------
echo
python -m ruff check --fix now_lms
echo
echo -------------------------------------------------
echo Check python code with pylint
echo -------------------------------------------------
echo
python -m pylint now_lms --score=yes --fail-under=9.5
echo
echo -------------------------------------------------
echo Check python types
echo -------------------------------------------------
echo
python -m mypy now_lms --install-types --non-interactive --ignore-missing-imports
echo
echo -------------------------------------------------
echo Run tests
echo -------------------------------------------------
echo
pybabel compile -d now_lms/translations
CI=True pytest --tb=short -q --cov=now_lms -n auto
