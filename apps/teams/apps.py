from django.apps import AppConfig


class TeamsConfig(AppConfig):
    name = "apps.teams"
    label = "teams"

    def ready(self):
        from . import signals  # noqa
