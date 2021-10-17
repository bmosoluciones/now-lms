#!/bin/bash
yarn
sudo apt install -y sqlite
git config pull.rebase true
python -m pip install --upgrade pip
python -m pip install --upgrade pip
python -m pip install -r development.txt
python -m pip install -e .
python setup.py develop
mypy now_lms --install-types --non-interactive 
python -m pip install gunicorn inotify
gunicorn --workers=4 --reload wsgi:app