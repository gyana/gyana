# Repository-wide commands.
# Read https://github.com/casey/just#quick-start before editing.

service_account := "gyana-1511894275181-50f107d4db00.json"

# Default command, do not add any commands above it.
default:
  @just dev

mk_bq:
    python ./manage.py make_bq_dataset

dev:
    python ./manage.py runserver

# Encrypt or decrypt file via GCP KMS
gcloud_kms OP FILE:
    gcloud kms {{OP}} --location global --keyring gyana-kms --key gyana-kms --ciphertext-file {{FILE}}.enc --plaintext-file {{FILE}}

# Decrypt environment file and export it to local env
env:
    just gcloud_kms decrypt .env
    just gcloud_kms decrypt {{service_account}}

# Encrypt .env file using KMS
enc_env:
    just gcloud_kms encrypt .env
    just gcloud_kms encrypt {{service_account}}

celery:
    celery -A gyana worker -l info

dev-celery:
    watchexec -w apps -e py -r "celery -A gyana worker -l info"

export:
    poetry export -f requirements.txt --output requirements.txt

update:
    yarn install
    poetry install

migrate: update
    python manage.py migrate

format:
    # autoflake --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports .
    black .
    isort .

# Count total lines of code that need to be maintained
cloc:
    cloc $(git ls-files) --exclude-dir=migrations --exclude-ext=svg,csv,json

startapp:
    pushd apps && cookiecutter cookiecutter-app && popd

cypress-setup:
    ./manage.py migrate --settings gyana.settings.cypress
    ./manage.py flush --settings gyana.settings.cypress --noinput
    ./manage.py loaddata --settings gyana.settings.cypress cypress/fixtures/fixtures.json

cypress-server:
    ./manage.py runserver --settings gyana.settings.cypress

cypress-celery:
    watchexec -w apps -e py -r "DJANGO_SETTINGS_MODULE=gyana.settings.cypress celery -A gyana worker -l info"

cypress-fixtures:
    ./manage.py dumpdata -e admin -e auth -e contenttypes -e sessions -e sites --settings gyana.settings.cypress > cypress/fixtures/fixtures.json
    yarn prettier --write cypress/fixtures/fixtures.json
