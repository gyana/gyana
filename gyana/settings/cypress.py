import django_heroku

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

django_heroku.settings(locals())


# URLs to reset and seed the database for testing. Although Cypress supports
# running CLI commands, the overhead of starting up the python interpreter for
# each ./manage.py command is 2-3s, whereas the actual reset/seed is 350ms.

CYPRESS_URLS = True

# like locmem but using JSON to store on disk
EMAIL_BACKEND = "apps.base.cypress_mail.EmailBackend"

CLOUD_NAMESPACE = "cypress"

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)
