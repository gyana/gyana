# Repository-wide commands.
# Read https://github.com/casey/just#quick-start before editing.

service_account := "gyana-1511894275181-50f107d4db00.json"

# Default command, do not add any commands above it.
default:
  @just dev

dev:
    python ./manage.py runserver

celery:
    watchexec -w apps -e py -r "celery -A gyana worker -Q celery,priority -l INFO"

beat:
    watchexec -w apps -e py -r "celery -A gyana beat -l INFO"

migrate app='' migration='':
    ./manage.py migrate {{app}} {{migration}}

seed:
    ./manage.py flush --noinput
    ./manage.py loaddata cypress/fixtures/fixtures.json

fixtures:
    ./manage.py dumpdata --natural-foreign -e admin -e auth.permission -e contenttypes -e sessions -e silk \
        -e wagtailcore.groupcollectionpermission -e wagtailcore.grouppagepermission -e wagtailimages.rendition \
         > cypress/fixtures/fixtures.json
    yarn prettier --write cypress/fixtures/fixtures.json

shell:
    ./manage.py shell -i ipython

collectstatic:
    ./manage.py collectstatic --noinput

celery-ci:
    celery -A gyana worker -l info

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

export:
    poetry export -f requirements.txt --output requirements.txt --without-hashes

update:
    yarn install
    poetry install

format:
    # autoflake --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports .
    black .
    isort .

alias bf := branchformat
branchformat:
    git diff --diff-filter=M --name-only main '***.py' | xargs black
    git diff --diff-filter=M --name-only main '***.py' | xargs isort

# Count total lines of code that need to be maintained
cloc:
    cloc $(git ls-files) --exclude-dir=migrations,tests,vendors --exclude-ext=svg,csv,json,yaml,md,toml

startapp:
    pushd apps && cookiecutter cookiecutter-app && popd

test TEST=".":
    python -m pytest --no-migrations --ignore=apps/cookiecutter-app --disable-pytest-warnings -k {{TEST}}

test-retry:
    python -m pytest --no-migrations --disable-pytest-warnings --last-failed --ignore=apps/cookiecutter-app 

test-ci:
    python -m pytest --cov --cov-report xml --no-migrations --disable-pytest-warnings --ignore=apps/cookiecutter-app 