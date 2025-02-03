#!/bin/bash
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
