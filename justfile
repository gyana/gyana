service_account := "gyana-1511894275181-50f107d4db00.json"

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

startapp:
    pushd apps && cookiecutter cookiecutter-app && popd