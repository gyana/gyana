release: python manage.py migrate
web: gunicorn gyana.wsgi --log-file -
worker: celery -A gyana worker -l INFO
beat: celery -A gyana beat -l INFO
