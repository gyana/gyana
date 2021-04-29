# Development

## Prerequisites

Packages and software required to develop the tool.

Required:

- Direnv
- Poetry
- Postgres
- Redis
- Yarn

Optional / Recommended

- Virtualenvwrapper
- Watchexec
- Heroku-cli

## Setup

After installing virtualenvwrapper, create an environment:

```bash
mkvirtualenv --no-site-packages gyana -p python3
```

Install all required python and node dependencies:

```bash
poetry install
yarn install
```

On MacOS you may run into a bug with `psycopg2` due to an outdated package `django-heroku`, after
the install fails the first time run and run `poetry install` again. For more details on this see:
<https://stackoverflow.com/questions/26288042/error-installing-psycopg2-library-not-found-for-lssl>

```bash
env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pip install psycopg2
```

Create a local database and run migrations on it:

```bash
createdb gyana
python manage.py migrate
```

You now need to run webpack to bundle all the client side code and styles:

```bash
yarn dev
```

You can also run `yarn dev-watch` to watch for file changes.

At this point you should be able to run the app, make sure that postgresql is running (and redis-server if running celery).

```bash
just dev
just dev-celery # Optional
```

## Develop

Commands:

- `just dev`
- `just dev-celery`
- `yarn dev-watch`

Create a new CRUDL Django app with `just startapp`.

## Deployment

For more in-depth information see [DEPLOYMENT.md](DEPLOYMENT.md)

Run `just export` and push to main. View errors on
[Heroku](https://dashboard.heroku.com/apps/gyana-mvp).
