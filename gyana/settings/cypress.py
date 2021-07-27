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

CYPRESS_URLS = True
