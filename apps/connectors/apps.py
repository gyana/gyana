from django.apps import AppConfig


class ConnectorsConfig(AppConfig):
    name = "apps.connectors"
    label = "connectors"

    def ready(self):
        from . import signals  # noqa
