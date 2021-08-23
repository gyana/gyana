from django.apps import AppConfig


class TablesConfig(AppConfig):
    name = "apps.tables"
    label = "tables"

    def ready(self):
        from . import signals
