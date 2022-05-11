from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "apps.users"
    label = "users"

    def ready(self):

        from allauth.account.admin import EmailAddress
        from django.contrib import admin

        from . import signals  # noqa

        # remove app registered automatically by allauth
        admin.site.unregister(EmailAddress)
