import analytics
from django.apps import AppConfig
from django.conf import settings


class UserConfig(AppConfig):
    name = "apps.users"
    label = "users"

    def ready(self):
        analytics.debug = bool(settings.DEBUG and settings.SEGMENT_ANALYTICS_WRITE_KEY)
        analytics.write_key = settings.SEGMENT_ANALYTICS_WRITE_KEY or ""
