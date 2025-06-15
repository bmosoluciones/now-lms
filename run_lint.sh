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
echo
echo Lint html files wiht curlylint
echo -------------------------------------------------
echo
python -m curlylint now_lms/templates/
