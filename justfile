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