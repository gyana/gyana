"""
Used in Heroku config vars:
https://dashboard.heroku.com/apps/gyana-mvp/settings
"""

import django_heroku

from .settings import *

django_heroku.settings(locals())

SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

# fix ssl mixed content issues
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEBUG = False
ALLOWED_HOSTS = ["gyana.com", "gyana-mvp.herokuapp.com"]
