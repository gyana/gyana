from .base import *

# Disable password validators when working locally.
AUTH_PASSWORD_VALIDATORS = []

# Enable cache busting locally.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'