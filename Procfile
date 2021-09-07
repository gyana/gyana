release: python manage.py migrate
web: gunicorn gyana.wsgi --log-file -
worker: celery -A gyana worker -l INFO -c 4
beat: celery -A gyana beat -l INFO
