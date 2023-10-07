from .base import *

# Allows the debug context processor to add variables into the context.
INTERNAL_IPS = {"127.0.0.1"}

# Disable admin-style browsable api endpoint
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

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
