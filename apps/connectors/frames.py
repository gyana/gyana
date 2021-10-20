from django.conf import settings
from django.urls import reverse

from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameDetailView

from .models import Connector
from .periodic import update_fivetran_succeeded_at
from .tasks import complete_connector_sync


class ConnectorIcon(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:icon"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if fivetran_client().has_completed_sync(self.object):
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
        data = fivetran_client().get(self.object)
        update_fivetran_succeeded_at(self.object, data["succeeded_at"])
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

            context_data["fivetran_url"] = fivetran_client().get_authorize_url(
                self.object,
                f"{settings.EXTERNAL_URL}{internal_redirect}",
            )
        context_data["broken"] = broken
        return context_data
