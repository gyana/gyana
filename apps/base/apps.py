import analytics
from django.apps import AppConfig
from django.conf import settings


class BaseConfig(AppConfig):
    name = "apps.base"
    label = "base"

    def ready(self):
        # disable sending events unless key is defined
        analytics.send = bool(settings.SEGMENT_ANALYTICS_WRITE_KEY)
        analytics.write_key = settings.SEGMENT_ANALYTICS_WRITE_KEY or ""
