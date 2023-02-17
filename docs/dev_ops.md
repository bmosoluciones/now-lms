# Other deployment options

There are templates available to deploy Now - LMS to these [PAID] services:

[![Deploy to DO](https://img.shields.io/badge/DO-Deploy%20to%20DO-blue "Deploy as Digital Ocean App")](https://cloud.digitalocean.com/apps/new?repo=https://github.com/bmosoluciones/now-lms/tree/main)
[![Deploy to Heroku](https://img.shields.io/badge/Heroku-Deploy%20to%20Heroku-blueviolet "Deploy to Heroku")](https://heroku.com/deploy?template=https://github.com/bmosoluciones/now-lms/tree/heroku)

## Render

On [render](https://render.com/) you can host NOW-LMS for free, just set your project settings as follow:

```
Build Command: pip install -r requirements.txt && cd now_lms/static/ && npm install
Start Command: python -m now_lms
```

Important: You can test NOW-LMS for free on Render, but with the default configuration NOW LMS will use a SQLite database as data store, this database is not goin to persist after system upgrades, to keep your data safe ve sure to set the next enviroment variables:

```
DATABASE_URL=proper_db_connet_string
```

Note that you can host a tiny up to 20MB PostgreSQL database for free in [elephantsql](https://customer.elephantsql.com/instance).
