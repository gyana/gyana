# Development

## Prerequisites

Packages and software required to develop the tool. Install via homebrew, unless indicated otherwise.

Required:

- just
- direnv
- poetry
- yarn
- watchexec
- postgres 13 (https://postgresapp.com/)
- redis 6 (https://jpadilla.github.io/redisapp/)

Optional / Recommended

- virtualenvwrapper
- heroku

## Setup

Authorize direnv to configure your local environment:

```bash
direnv allow .
```

Build a python virtual environment:

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

Make sure to authenticate using gcloud and generate the relevant env variables:

```bash
gcloud auth login
gcloud config set project gyana-1511894275181
just env # decrypt secrets stored in repository
```

## Develop

Commands:

```bash
just dev
just dev-celery # optionally for celery tasks
yarn build:watch
```

Create a new CRUDL Django app with `just startapp`.

## Testing with Cypress

Setup your test app:

- `createdb cypress_gyana`
- `just cypress-setup`

Run cypress + app with hot-reloading:

- `just cypress-server`
- `just cypress-celery`
- `yarn build:watch`
- `yarn cypress:open`

The app is seeded with the fixtures defined in `cypress/fixtures/fixtures.json`. To modify the fixtures:

- Reset the database `just cypress-setup`
- Go to the app in the browser and modify it
- Dump the fixtures `just cypress-fixtures`
- Commit your changes

## Deployment

For more in-depth information see [DEPLOYMENT.md](DEPLOYMENT.md)

Run `just export` and push to main. View errors on
[Heroku](https://dashboard.heroku.com/apps/gyana-mvp).

## Adding new data science nodes

To add new nodes, you need to add the new node kind to the model choices and the required fields as new columns. The current naming convention for these columns is `<kind>_property`. You can then add a form object to the `KIND_TO_FORM` map in _workflows/forms.py_. Inheriting from `ModelForm` is the easiest way to implement these forms.

To display the nodes data and add to the flows SQL query add a function `NODE_FROM_CONFIG` in _workflows/nodes.py_.
