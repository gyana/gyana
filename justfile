# Repository-wide commands.
# Read https://github.com/casey/just#quick-start before editing.

service_account := "gyana-1511894275181-50f107d4db00.json"
excludes := "-e admin -e auth.permission -e contenttypes -e sessions -e silk"
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

compile:
    # TODO: remove dependency on django-heroku
    pip-compile --unsafe-package psycopg2 --unsafe-package setuptools
    pip-compile requirements-dev.in

sync:
    pip-sync requirements.txt requirements-dev.txt

update:
    npm install
    sync

format:
    autoflake --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports --exclude 'apps/*/migrations' gyana apps
    black .
    isort .

alias bf := branchformat
branchformat:
    git diff --diff-filter=M --name-only main '***.scss' | xargs --no-run-if-empty npm run prettier:write
    git diff --diff-filter=M --name-only main '***.py' | xargs --no-run-if-empty black
    git diff --diff-filter=M --name-only main '***.py' | xargs --no-run-if-empty isort

# Count total lines of code that need to be maintained
cloc:
    cloc $(git ls-files) --exclude-dir=migrations,tests,vendors --exclude-ext=svg,csv,json,yaml,md,toml

startapp:
    pushd apps && cookiecutter cookiecutter-app && popd

test TEST=".":
    python -m pytest --no-migrations --ignore=apps/base/tests/e2e --ignore=apps/cookiecutter-app --disable-pytest-warnings -k {{TEST}}

test-ci:
    python -m pytest --cov --cov-report xml --no-migrations --disable-pytest-warnings --ignore=apps/base/tests/e2e --ignore=apps/cookiecutter-app 

test-e2e:
    python -m pytest --no-migrations --disable-pytest-warnings --reruns 2 apps/base/tests/e2e

# calls to run app in docker containers
docker-setup-env:
	@[ ! -f ./.env.docker ] && cp ./.env.example ./.env.docker || echo ".env.docker file already exists."

docker-start: ## Start the docker containers
	@echo "Starting the docker containers"
	@docker-compose up --build -d
	@echo "Containers started - http://localhost:8000"
	@echo "Run make refresh-image to refresh the images"

docker-stop: ## Stop Containers
	@docker compose down

docker-restart: docker-stop docker-start ## Restart Containers

docker-start-bg:  ## Run containers in the background
	@docker compose up -d

docker-build: ## Build Containers
	@docker compose build

docker-migrations: ## Create DB migrations in the container
	@docker compose run --rm --no-deps web python manage.py makemigrations

docker-migrate: ## Run DB migrations in the container
	@docker compose run --rm --no-deps web python manage.py migrate

docker-init: docker-setup-env docker-start-bg docker-migrations docker-migrate  ## Quickly get up and running (start containers and migrate DB)

docker-pip-compile: ## Compiles your requirements.in file to requirements.txt
	@docker compose run --rm --no-deps web pip-compile requirements/requirements.in
	@docker compose run --rm --no-deps web pip-compile requirements/dev-requirements.in
	@docker compose run --rm --no-deps web pip-compile requirements/prod-requirements.in

docker-requirements: docker-pip-compile docker-build docker-restart  ## Rebuild your requirements and restart your containers

docker-npm-install: ## Runs npm install in the container
	@docker compose run --rm --no-deps web npm install $(filter-out $@,$(MAKECMDGOALS))

docker-npm-build: ## Runs npm build in the container (for production assets)
	@docker compose run --rm --no-deps web npm run build

docker-npm-dev: ## Runs npm dev in the container
	@docker compose run --rm --no-deps web npm run build:dev

docker-npm-watch: ## Runs npm watch in the container (recommended for dev)
	@docker compose run --rm --no-deps web npm run build:watch