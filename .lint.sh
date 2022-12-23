#!/bin/bash
python -m pip install --upgrade -r development.txt
python -m black now_lms
python -m bandit -r now_lms
python -m flake8 --ignore=E712 now_lms
python -m pylint now_lms
python -m mypy now_lms --install-types --non-interactive 
python -m curlylint now_lms/templates/
rm -rf build
python -m build
python -m twine check dist/*
python -m pytest