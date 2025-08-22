#!/bin/bash
echo -------------------------------------------------
echo Format Python code
echo -------------------------------------------------
echo
black -v now_lms
echo -------------------------------------------------
echo Check Python code with pylint
echo -------------------------------------------------
echo
python -m pylint now_lms --score=yes --fail-under=9.0
echo -------------------------------------------------
echo Format HTML templates
echo -------------------------------------------------
echo
./node_modules/.bin/prettier --write now_lms/templates/ --parser=html "**/*.j2"
