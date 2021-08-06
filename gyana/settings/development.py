from .base import *

# Allows the debug context processor to add variables into the context.
INTERNAL_IPS = {"127.0.0.1"}

# Disable password validators when working locally.
AUTH_PASSWORD_VALIDATORS = []

# Enable cache busting locally.
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

USE_HASHIDS = False

FIVETRAN_USE_INTERNAL = True
