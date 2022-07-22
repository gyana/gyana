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

CNAME_ALLOWED_HOSTS = [
    ".gyana.com",
    "gyana-dev.herokuapp.com",
    "gyana-release.herokuapp.com",
    "gyana-beta.herokuapp.com",
]

EXTERNAL_URL = os.environ.get("EXTERNAL_URL")

FF_ALPHA = False

EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@gyana.com"
ANYMAIL = {"SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY")}

USE_HASHIDS = True

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
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": None},
        },
    },
    "site": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"ssl_cert_reqs": None},
        },
    },
}

CACHEOPS_REDIS = f'{os.environ.get("REDIS_URL")}?ssl_cert_reqs=none'

# After django 4.0 update ManifestStaticFilesStorage would fail
# Collecting the sourcemaps for fusioncharts
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
