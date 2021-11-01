#! /usr/bin/bash

black now_lms
mypy now_lms
flake8 now_lms
pylint now_lms
pytest -x -v