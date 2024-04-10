from .base import *

USE_HASHIDS = False
ACCOUNT_EMAIL_VERIFICATION = "optional"

# Allows the debug context processor to add variables into the context.
INTERNAL_IPS = {"127.0.0.1"}

# Disable password validators when working locally.
AUTH_PASSWORD_VALIDATORS = []

# TODO: Disabling because it breaks the collection of the fusionchart files.
# For this to work we will need to copy the sourcemaps as well.
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# If using mailhog to debug emails uncomment these lines
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_HOST = "0.0.0.0"
# EMAIL_PORT = 1025
# EMAIL_HOST_USER = ""
# EMAIL_HOST_PASSWORD = ""
# EMAIL_USE_TLS = False

CLOUD_NAMESPACE = "cypress"

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

MOCK_REMOTE_OBJECT_DELETION = True

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True  # for flamegraphs
SILKY_ANALYZE_QUERIES = True

INSTALLED_APPS = INSTALLED_APPS + ["silk"]
MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE

# for code coverage
TEMPLATES[0]["OPTIONS"]["debug"] = True

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "site": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}

CACHEOPS_ENABLED = False
