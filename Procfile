release: python manage.py migrate
# workaround for memory leaks in django:
# https://adamj.eu/tech/2019/09/19/working-around-memory-leaks-in-your-django-app/#gunicorn
web: gunicorn gyana.wsgi --log-file - --threads 4 --max-requests 1000 --max-requests-jitter 50
