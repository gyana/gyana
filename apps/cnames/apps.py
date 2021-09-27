from django.apps import AppConfig


class CNamesConfig(AppConfig):
    name = "apps.cnames"
    label = "cnames"

    def ready(self):
        from . import signals
