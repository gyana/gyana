"""
Django settings for Gyana project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Three repetitions of `.parent` as we are climbing the directory tree to the root of the
# project.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "BITuHkgTLhSfOHAewSSxNKRZfvYuzjPhdbIhaztE"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# True in pytest
TEST = False

ALLOWED_HOSTS = ["*"]

# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.contrib.postgres",
    "django.contrib.sitemaps",
]

# Put your third-party apps here
THIRD_PARTY_APPS = [
    "rest_framework",
    "cacheops",
    "heroicons",
    "django_htmx",
    # wagtail
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.core",
    "modelcluster",
    "taggit",
    "wagtail.contrib.modeladmin",
    "wagtailmenus",
]

# Put your project-specific apps here
PROJECT_APPS = ["apps.web", "apps.base", "apps.blog"]

INSTALLED_APPS = DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS + ["django.forms"]

MIDDLEWARE = [
    "honeybadger.contrib.DjangoHoneybadgerMiddleware",
    "beeline.middleware.django.HoneyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s %(message)s"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "loggers": {
        # uncomment to debug segment
        # "segment": {
        #     "handlers": ["console"],
        #     "level": "DEBUG",
        #     "propagate": True,
        # },
        # uncomment to debug django
        # "django": {
        #     "handlers": ["console"],
        #     "level": "DEBUG",
        #     "propagate": True,
        # }
    },
}

ROOT_URLCONF = "gyana.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.web.context_processors.user_meta",
                "apps.web.context_processors.project_meta",
                "apps.web.context_processors.google_analytics_id",
                "gyana.context_processors.django_settings",
                "wagtailmenus.context_processors.wagtailmenus",
            ]
        },
        "APP_DIRS": True,
    },
]

WSGI_APPLICATION = "gyana.wsgi.application"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "website",
        "USER": os.getenv("PG_USER", "postgres"),
        "PASSWORD": os.getenv("PG_PASSWORD", "***"),
        "HOST": "localhost",
        "PORT": "5432",
    }
}


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
)


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = BASE_DIR / "static_root"
STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]
# uncomment to use manifest storage to bust cache when file change
# note: this may break some image references in sass files which is why it is not enabled by default
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Django sites

SITE_ID = 1

# DRF config
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}

# Pegasus config

# replace any values below with specifics for your project
PROJECT_METADATA = {
    "NAME": "Gyana",
    "URL": "http://gyana.com",
    "DESCRIPTION": "Open source, no-code business intelligence",
    "IMAGE": "https://upload.wikimedia.org/wikipedia/commons/2/20/PEO-pegasus_black.svg",
    "KEYWORDS": "SaaS, django",
    "CONTACT_EMAIL": "developers@gyana.com",
}

GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID")
WEBSITE_GTM_ID = os.environ.get("WEBSITE_GTM_ID")

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_BQ_SVC_ACCOUNT = os.environ.get("GCP_BQ_SVC_ACCOUNT")

DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = os.environ.get("GS_BUCKET_NAME")
GS_PUBLIC_BUCKET_NAME = os.environ.get("GS_PUBLIC_BUCKET_NAME")
GS_PUBLIC_CACHE_CONTROL = "public, max-age=31536000"

# Feature flag for Alpha features
FF_ALPHA = True

# django write key
SEGMENT_ANALYTICS_WRITE_KEY = os.environ.get("SEGMENT_ANALYTICS_WRITE_KEY", "")
# web write key
SEGMENT_ANALYTICS_JS_WRITE_KEY = os.environ.get("SEGMENT_ANALYTICS_JS_WRITE_KEY", "")

ENVIRONMENT = os.environ.get("ENVIRONMENT")

HONEYBADGER = {
    "API_KEY": os.environ.get("HONEYBADGER_API_KEY"),
    "ENVIRONMENT": ENVIRONMENT,
    # enables us to use "development" and send data
    "FORCE_REPORT_DATA": True,
    "EXCLUDED_EXCEPTIONS": ["Http404", "DoesNotExist"],
}

WAGTAIL_SITE_NAME = "Gyana CMS"
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    }
}

CACHEOPS_REDIS = "redis://localhost:6379/0"
CACHEOPS = {"*.*": {"timeout": 60 * 60}}
