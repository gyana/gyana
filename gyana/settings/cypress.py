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


# URLs to reset and seed the database for testing. Although Cypress supports
# running CLI commands, the overhead of starting up the python interpreter for
# each ./manage.py command is 2-3s, whereas the actual reset/seed is 350ms.

CYPRESS_URLS = True
