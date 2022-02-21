from django.apps import AppConfig


class RunsConfig(AppConfig):
    name = "apps.runs"
    label = "runs"

    def ready(self):
        from . import signals  # noqa
