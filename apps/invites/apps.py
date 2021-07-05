from django.apps import AppConfig


class InvitesConfig(AppConfig):
    name = "apps.invites"
    label = "invites"

    def ready(self):
        from . import signals
