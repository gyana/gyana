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

ALLOWED_HOSTS = ["*"]
# custom allowed hosts middleware for cnames
CNAME_ALLOWED_HOSTS = []


# Application definition

ADMIN_TOOLS_APPS = [
    "admin_tools",
    "admin_tools.theming",
    "admin_tools.menu",
    "admin_tools.dashboard",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django.forms",
    "django.contrib.postgres",
]

# Put your third-party apps here
THIRD_PARTY_APPS = [
    "allauth",  # allauth account/registration management
    "turbo_allauth",
    "turbo_response",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "celery_progress",
    "crispy_forms",
    "crispy_tailwind",
    "django_filters",
    "django_tables2",
    "invitations",
    "hijack",
    "hijack.contrib.admin",
    "waffle",
]

# Put your project-specific apps here
PROJECT_APPS = [
    "apps.users.apps.UserConfig",
    "apps.web",
    "apps.teams.apps.TeamsConfig",
    "apps.projects",
    "apps.integrations",
    "apps.workflows",
    "apps.dashboards",
    "apps.widgets",
    "apps.filters",
    "apps.tables.apps.TablesConfig",
    "apps.invites.apps.InvitesConfig",
    "apps.base.apps.BaseConfig",
    "apps.nodes",
    "apps.columns",
    "apps.uploads",
    "apps.sheets",
    "apps.connectors.apps.ConnectorsConfig",
    "apps.appsumo",
    "apps.templates",
    "apps.cnames.apps.CNamesConfig",
]

INSTALLED_APPS = ADMIN_TOOLS_APPS + DJANGO_APPS + PROJECT_APPS + THIRD_PARTY_APPS

MIDDLEWARE = [
    "apps.cnames.middleware.HostMiddleware",
    "honeybadger.contrib.DjangoHoneybadgerMiddleware",
    "beeline.middleware.django.HoneyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.base.middleware.HoneybadgerUserContextMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "waffle.middleware.WaffleMiddleware",
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
    # uncomment to debug segment
    # "loggers": {
    #     "segment": {
    #         "handlers": ["console"],
    #         "level": "DEBUG",
    #         "propagate": True,
    #     }
    # },
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
            ],
            # equivalent of APP_DIRS=True, plus admin_tools template loader
            "loaders": [
                "django.template.loaders.app_directories.Loader",
                "admin_tools.template_loaders.Loader",
            ],
        },
    },
]

WSGI_APPLICATION = "gyana.wsgi.application"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "gyana",
        "USER": "postgres",
        "PASSWORD": "***",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# Auth / login stuff

# Django recommends overriding the user model even if you don't think you need to because it makes
# future changes much easier.
AUTH_USER_MODEL = "users.CustomUser"
LOGIN_REDIRECT_URL = "/"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Allauth setup

ACCOUNT_ADAPTER = "apps.users.adapter.UsersAccountAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

ACCOUNT_FORMS = {
    "login": "apps.users.forms.UserLoginForm",
    "signup": "apps.teams.forms.TeamSignupForm",
}


# User signup configuration: change to "mandatory" to require users to confirm email before signing in.
# or "optional" to send confirmation emails but not require them
ACCOUNT_EMAIL_VERIFICATION = "optional"
LOGIN_URL = "account_login"


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)


# enable social login
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}
SOCIALACCOUNT_ADAPTER = "apps.users.adapter.SocialAccountAdapter"


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

# Email setup

# use in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django sites

SITE_ID = 1

# DRF config
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
}


# Celery setup (using redis)
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"


# Pegasus config

# replace any values below with specifics for your project
PROJECT_METADATA = {
    "NAME": "Gyana",
    "URL": "http://gyana.com",
    "DESCRIPTION": "No-Code Data Analytics",
    "IMAGE": "https://upload.wikimedia.org/wikipedia/commons/2/20/PEO-pegasus_black.svg",
    "KEYWORDS": "SaaS, django",
    "CONTACT_EMAIL": "developers@gyana.com",
}

GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID")


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

GCP_PROJECT = os.environ.get("GCP_PROJECT")
GCP_BQ_SVC_ACCOUNT = os.environ.get("GCP_BQ_SVC_ACCOUNT")

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"

CRISPY_TEMPLATE_PACK = "tailwind"

DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
GS_BUCKET_NAME = os.environ.get("GS_BUCKET_NAME")

FIVETRAN_KEY = os.environ.get("FIVETRAN_KEY")
FIVETRAN_URL = "https://api.fivetran.com/v1"
FIVETRAN_GROUP = os.environ.get("FIVETRAN_GROUP")
FIVETRAN_HEADERS = {
    "Authorization": f"Basic {FIVETRAN_KEY}",
    "Accept": "application/json;version=2",
}

EXTERNAL_URL = "http://localhost:8000"
# for local development
MOCK_FIVETRAN = os.environ.get("MOCK_FIVETRAN", "False") == "True"

BIGQUERY_COLUMN_NAME_LENGTH = 300
BIGQUERY_TABLE_NAME_LENGTH = 1024
BIGQUERY_LOCATION = "EU"

# Namespace based on git email to avoid collisions in PKs on local dev
CLOUD_NAMESPACE = os.environ.get("CLOUD_NAMESPACE")

# Feature flag for Alpha features
FF_ALPHA = True

# django write key
SEGMENT_ANALYTICS_WRITE_KEY = os.environ.get("SEGMENT_ANALYTICS_WRITE_KEY", "")
# web write key
SEGMENT_ANALYTICS_JS_WRITE_KEY = os.environ.get("SEGMENT_ANALYTICS_JS_WRITE_KEY", "")

INVITATIONS_INVITATION_MODEL = "invites.Invite"
INVITATIONS_INVITATION_EXPIRY = 7
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER

HASHIDS_SALT = os.environ.get("HASHIDS_SALT", "")

FUSIONCHARTS_LICENCE = os.environ.get("FUSIONCHARTS_LICENCE")

CYPRESS_URLS = False

ADMIN_TOOLS_MENU = "apps.base.menu.CustomMenu"
ADMIN_TOOLS_INDEX_DASHBOARD = "apps.base.dashboard.CustomIndexDashboard"

MOCK_REMOTE_OBJECT_DELETION = False

ENVIRONMENT = os.environ.get("ENVIRONMENT")
HONEYCOMB_API_KEY = os.environ.get("HONEYCOMB_API_KEY")

HONEYBADGER = {
    "API_KEY": os.environ.get("HONEYBADGER_API_KEY"),
    "ENVIRONMENT": ENVIRONMENT,
    # enables us to use "development" and send data
    "FORCE_REPORT_DATA": True,
}

HELLONEXT_SSO_TOKEN = os.environ.get("HELLONEXT_SSO_TOKEN")

HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY")
HEROKU_APP = os.environ.get("HEROKU_APP")

CNAME_DOMAIN = os.environ.get("CNAME_DOMAIN")
