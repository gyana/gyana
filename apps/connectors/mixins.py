from django.utils.functional import cached_property

from .models import Connector


class ConnectorMixin:
    @cached_property
    def connector(self):
        return Connector.objects.get(pk=self.kwargs["connector_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["connector"] = self.connector
        return context
