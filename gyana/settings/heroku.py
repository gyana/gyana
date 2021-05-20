"""
Used in Heroku config vars:
https://dashboard.heroku.com/apps/gyana-mvp/settings
"""
import os

import django_heroku

from .base import *

django_heroku.settings(locals())

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

SECRET_KEY = os.environ.get("SECRET_KEY", SECRET_KEY)
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

# fix ssl mixed content issues
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEBUG = False
ALLOWED_HOSTS = [
    ".gyana.com",
    "gyana-mvp.herokuapp.com",
    "gyana-beta.herokuapp.com",
]

EXTERNAL_URL = os.environ.get("EXTERNAL_URL", "https://gyana-mvp.herokuapp.com")

FF_ALPHA = False
