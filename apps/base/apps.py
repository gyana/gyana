from beeline.patch.requests import *
from django.apps import AppConfig
from django.conf import settings

import analytics


class BaseConfig(AppConfig):
    name = "apps.base"
    label = "base"

    def ready(self):
        # disable sending events unless key is defined
        analytics.send = bool(settings.SEGMENT_ANALYTICS_WRITE_KEY)
        analytics.write_key = settings.SEGMENT_ANALYTICS_WRITE_KEY or ""

        # # Uncomment to use Honeycomb to profile app locally
        # # In production, this is handled in the gunicorn.conf.py
        # import beeline
        # beeline.init(
        #     writekey=settings.HONEYCOMB_API_KEY,
        #     dataset=settings.ENVIRONMENT,
        #     service_name="app",
        #     debug=True,
        # )
