service_account := "gyana-1511894275181-50f107d4db00.json"

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
    
dev:
    python ./manage.py runserver

celery:
    celery -A gyana worker -l info

dev-celery:
    watchexec -w apps -e py -r "celery -A gyana worker -l info"

export:
    poetry export -f requirements.txt --output requirements.txt

format:
    # autoflake --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports .
    black .
    isort .

startapp:
    pushd apps && cookiecutter cookiecutter-app && popd