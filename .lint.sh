#!/bin/bash
echo -------------------------------------------------
echo Format Python code
echo -------------------------------------------------
echo
iosrt now_lms
black now_lms
echo -------------------------------------------------
echo Check python code with flake8
echo -------------------------------------------------
echo
flake8 --ignore E501 now_lms
echo -------------------------------------------------
echo Check python code with ruff
echo -------------------------------------------------
echo
python -m ruff check now_lms
echo
echo -------------------------------------------------
echo Check python types
echo -------------------------------------------------
echo
python -m mypy now_lms --install-types --non-interactive
echo
echo -------------------------------------------------
echo Lint html files wiht curlylint
echo -------------------------------------------------
echo
# python -m curlylint now_lms/templates/
echo -------------------------------------------------
echo Run tests
echo -------------------------------------------------
echo
CI=True pytest  -v --exitfirst --cov=now_lms --slow=True
