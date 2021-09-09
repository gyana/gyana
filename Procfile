release: python manage.py migrate
web: gunicorn gyana.wsgi --log-file - --threads 4
worker: celery -A gyana worker -l INFO -c 4
beat: celery -A gyana beat -l INFO
