from django.apps import AppConfig


class SubscriptionConfig(AppConfig):
    name = 'apps.subscriptions'
    label = 'subscriptions'

    def ready(self):
        from . import webhooks
