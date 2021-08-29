from .base import *

USE_HASHIDS = False

# Allows the debug context processor to add variables into the context.
INTERNAL_IPS = {"127.0.0.1"}

# Disable password validators when working locally.
AUTH_PASSWORD_VALIDATORS = []

# Enable cache busting locally.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# URLs to reset and seed the database for testing. Although Cypress supports
# running CLI commands, the overhead of starting up the python interpreter for
# each ./manage.py command is 2-3s, whereas the actual reset/seed is 350ms.

CYPRESS_URLS = True

# like locmem but using JSON to store on disk
EMAIL_BACKEND = "apps.base.cypress_mail.EmailBackend"

CLOUD_NAMESPACE = "cypress"

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)
