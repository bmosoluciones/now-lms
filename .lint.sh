#!/bin/bash
rm now_lms.db
python -m black now_lms
python -m bandit -r now_lms
python -m flake8 --ignore=E712 now_lms
python -m pylint now_lms
python -m mypy now_lms --install-types --non-interactive 
python -m curlylint now_lms/templates/
python -m black tests/
python -m flake8 tests/
python -m pytest  -v --exitfirst --cov=now_lms
