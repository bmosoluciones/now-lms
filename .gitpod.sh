#!/bin/bash
yarn
sudo apt install -y sqlite
git config pull.rebase true
python -m pip install --upgrade pip
python -m pip install --upgrade pip
python -m pip install --upgrade -r development.txt
python -m pip install -e .
python setup.py develop
mypy now_lms --install-types --non-interactive 
python -m pip install hupper
python -m flask setup
/home/gitpod/.pyenv/versions/3.8.12/bin/hupper -m waitress --port=8080 now_lms:app
git push heroku mastergit remote add heroku https://git.heroku.com/app.git