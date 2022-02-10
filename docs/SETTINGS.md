# Django Settings

We are using separate settings modules inheriting from [gyana/settings/base.py](base.py).
Django decides which one to use based on the `DJANGO_SETTINGS_MODULE` environment variable.

You can override Django's choice by setting this explicitly:

```bash
DJANGO_SETTINGS_MODULE=gyana.settings.production python ./manage.py runserver
```
