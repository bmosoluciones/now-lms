#!/bin/bash
black now_lms
mypy now_lms --install-types --non-interactive 
flake8 now_lms
python -m build
python -m twine check dist/*
pylint now_lms