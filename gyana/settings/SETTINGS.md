# Django Settings

Each file here is a separate settings module inhereting from [base.py](base.py).
Django decides which one to use based on the `DJANGO_SETTINGS_MODULE` environment variable.

You can override Django's choice by setting this explicitly:

```bash
DJANGO_SETTINGS_MODULE=gyana.settings.production python ./manage.py runserver
```
