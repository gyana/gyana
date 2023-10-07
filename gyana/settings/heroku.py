"""
Used in Heroku config vars:
https://dashboard.heroku.com/apps/gyana-dev/settings
"""
import os

import django_heroku

from .base import *

DEBUG = False

django_heroku.settings(locals())

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

SECRET_KEY = os.environ.get("SECRET_KEY")
CELERY_BROKER_URL = os.environ.get("REDIS_URL")

# fix ssl mixed content issues
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

FF_ALPHA = False

HONEYBADGER = {
    "API_KEY": os.environ.get("HONEYBADGER_API_KEY"),
    "FORCE_REPORT_DATA": True,
    "EXCLUDED_EXCEPTIONS": ["Http404"],
}

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "site": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
}

CACHEOPS_REDIS = os.environ.get("REDIS_URL")

# After django 4.0 update ManifestStaticFilesStorage would fail
# Collecting the sourcemaps for fusioncharts
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
