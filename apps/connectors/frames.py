from django.conf import settings
from django.urls import reverse

from apps.base import clients
from apps.base.frames import TurboFrameDetailView

from .models import Connector
from .tasks import complete_connector_sync


class ConnectorIcon(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:icon"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if clients.fivetran().has_completed_sync(self.object):
            complete_connector_sync(self.object)

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
        data = clients.fivetran().get(self.object)
        succeeded_at = data.get("succeeded_at")
        if succeeded_at is not None:
            self.object.update_fivetran_succeeded_at(data["succeeded_at"])

        # {
        #     "setup_state": "broken" | "incomplete" | "connected",
        #     "tasks": [{"code": ..., "message": ...}],
        #     "warnings": [{"code": ..., "message": ...}]
        # }
        broken = data["status"]["setup_state"] != "connected"
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
