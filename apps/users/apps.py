import analytics
from django.apps import AppConfig
from django.conf import settings


class UserConfig(AppConfig):
    name = "apps.users"
    label = "users"

    def ready(self):
        # disable sending events unless key is defined
        analytics.send = bool(settings.SEGMENT_ANALYTICS_WRITE_KEY)
        analytics.write_key = settings.SEGMENT_ANALYTICS_WRITE_KEY or ""

        from allauth.account.admin import EmailAddress
        from django.contrib import admin

        # remove app registered automatically by allauth
        admin.site.unregister(EmailAddress)
