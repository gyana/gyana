from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameDetailView
from apps.integrations.tables import (
    INTEGRATION_STATE_TO_ICON,
    INTEGRATION_STATE_TO_MESSAGE,
)

from .models import Connector
from .tasks import complete_connector_sync, update_fivetran_succeeded_at


class ConnectorIcon(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:icon"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if fivetran_client().has_completed_sync(self.object):
            complete_connector_sync(self.object, send_mail=False)

        context_data["icon"] = INTEGRATION_STATE_TO_ICON[self.object.integration.state]
        context_data["text"] = INTEGRATION_STATE_TO_MESSAGE[
            self.object.integration.state
        ]

        return context_data


class ConnectorStatus(TurboFrameDetailView):
    template_name = "connectors/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:status"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        update_fivetran_succeeded_at(self.object)
        return context_data
