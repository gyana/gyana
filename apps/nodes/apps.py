from django.apps import AppConfig


class NodesConfig(AppConfig):
    name = "apps.nodes"
    label = "nodes"

    def ready(self):
        from . import signals
