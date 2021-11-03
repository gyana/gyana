from django.conf import settings
from django.urls import reverse

from apps.base import clients
from apps.base.frames import TurboFrameDetailView

from .models import Connector
from .sync_end import handle_syncing_connector


class ConnectorIcon(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:icon"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        handle_syncing_connector(self.object)

        context_data["icon"] = self.object.integration.state_icon
        context_data["text"] = self.object.integration.state_text

        return context_data


class ConnectorStatus(TurboFrameDetailView):
    template_name = "connectors/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:status"

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        fivetran_connector = clients.fivetran().get(self.object)
        if fivetran_connector.succeeded_at is not None:
            self.object.update_fivetran_succeeded_at(fivetran_connector.succeeded_at)

        broken = fivetran_connector.status.setup_state != "connected"
        if broken:
            internal_redirect = reverse(
                "project_integrations_connectors:authorize",
                args=(
                    self.object.integration.project.id,
                    self.object.id,
                ),
            )

            context_data["fivetran_url"] = clients.fivetran().get_authorize_url(
                self.object,
                f"{settings.EXTERNAL_URL}{internal_redirect}",
            )
        context_data["broken"] = broken
        return context_data
