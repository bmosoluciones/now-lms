#!/bin/bash
echo -------------------------------------------------
echo Check python code with bandit
echo -------------------------------------------------
echo
python -m bandit -r now_lms
echo -------------------------------------------------
echo Check python code with flake8
echo -------------------------------------------------
echo
python -m flake8 --verbose --ignore=E712 now_lms
echo
echo -------------------------------------------------
echo Lint python code with pylint
echo -------------------------------------------------
echo
python -m pylint now_lms
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
python -m curlylint now_lms/templates/
