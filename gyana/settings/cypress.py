import dj_database_url

from .base import *

USE_HASHIDS = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "cypress_gyana",
        "USER": "postgres",
        "PASSWORD": "***",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

if "DATABASE_URL" in os.environ:
    # parse DATABASE_URL in heroku-ci
    DATABASES["default"] = dj_database_url.config(conn_max_age=600)

if "REDIS_URL" in os.environ:
    CELERY_BROKER_URL = os.environ.get("REDIS_URL")
    CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")


# URLs to reset and seed the database for testing. Although Cypress supports
# running CLI commands, the overhead of starting up the python interpreter for
# each ./manage.py command is 2-3s, whereas the actual reset/seed is 350ms.

CYPRESS_URLS = True

# like locmem but using JSON to store on disk
EMAIL_BACKEND = "apps.base.cypress_mail.EmailBackend"

CLOUD_NAMESPACE = "cypress"

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)
