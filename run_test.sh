#!/bin/bash
echo -------------------------------------------------
echo Format Python code
echo -------------------------------------------------
echo
black now_lms
echo -------------------------------------------------
echo Format HTML templates
echo -------------------------------------------------
echo
./node_modules/.bin/prettier --write now_lms/templates/
echo -------------------------------------------------
echo Check python code with flake8
echo -------------------------------------------------
echo
flake8 --max-line-length=120 --ignore=E501,E203,E266,W503,E722 now_lms
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
python -m mypy now_lms --install-types --non-interactive --ignore-missing-imports
echo
echo -------------------------------------------------
echo Lint html files wiht curlylint
echo -------------------------------------------------
echo
python -m curlylint now_lms/templates/
echo -------------------------------------------------
echo Run tests
echo -------------------------------------------------
echo
CI=True pytest  -v --exitfirst --cov=now_lms --slow=True --testpdf=True
