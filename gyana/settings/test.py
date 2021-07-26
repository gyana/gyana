from .base import *

USE_HASHIDS = False

# Enables us to use `./manage.py testserver` to setup the test server
# and `./manage.py dumpdata` generate fixtures.

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "test_gyana",
        "USER": "postgres",
        "PASSWORD": "***",
        "HOST": "localhost",
        "PORT": "5432",
        "TEST": {
            "NAME": "test_gyana",
            # faster to directly build the tables and avoid migrations
            "MIGRATE": False,
        },
    }
}
