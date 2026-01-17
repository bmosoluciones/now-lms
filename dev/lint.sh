#!/bin/bash
echo -------------------------------------------------
echo Ensure company headers in Python files
echo -------------------------------------------------
echo
python dev/ensure_headers.py --apply --paths now_lms,tests
echo -------------------------------------------------
echo Format Python code
echo -------------------------------------------------
echo
black -v now_lms
echo -------------------------------------------------
echo Check Python code with pylint
echo -------------------------------------------------
echo
python -m pylint now_lms --score=yes --fail-under=9.5
echo -------------------------------------------------
echo Format HTML templates
echo -------------------------------------------------
echo
./node_modules/.bin/prettier --write now_lms/templates/ --parser=html "**/*.j2"
