#!/bin/bash
sudo apt install -y sqlite
git config pull.rebase true
cd ..
cd ..
pwd
cd now_lms/static
npm install
python -m pip install --upgrade pip
python -m pip install --upgrade -r development.txt
python -m pip install -e .
/home/gitpod/.pyenv/versions/3.8.12/bin/hupper -m waitress --port=8080 now_lms:app