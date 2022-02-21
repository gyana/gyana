from django.apps import AppConfig


class InvitesConfig(AppConfig):
    name = "apps.invites"
    label = "invites"

    def ready(self):
        from django.contrib import admin

        from . import signals  # noqa
        from .models import Invite

        # remove app registered automatically by django-invitations
        admin.site.unregister(Invite)
