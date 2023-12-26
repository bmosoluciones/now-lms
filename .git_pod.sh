#!/bin/bash
sudo apt install -y sqlite
git config pull.rebase true
cd now_lms/static
npm install
cd ..
cd ..
python -m pip install --upgrade pip
python -m pip install --upgrade -r development.txt
python -m pip install -e .
hupper -m now_lms