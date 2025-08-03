#!/bin/bash
echo -------------------------------------------------
echo Format Python code
echo -------------------------------------------------
echo
black -v now_lms
echo -------------------------------------------------
echo Format HTML templates
echo -------------------------------------------------
echo
./node_modules/.bin/prettier --write now_lms/templates/ --parser=html "**/*.j2"
