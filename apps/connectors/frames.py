from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
from apps.integrations.models import Integration
from apps.integrations.tables import (
    INTEGRATION_STATE_TO_ICON,
    INTEGRATION_STATE_TO_MESSAGE,
)
from django.urls import reverse

from .forms import ConnectorUpdateForm
from .models import Connector
from .tasks import complete_connector_sync, run_connector_sync


class ConnectorUpdate(TurboFrameUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorUpdateForm
    turbo_frame_dom_id = "connectors:setup"

    def form_valid(self, form):
        run_connector_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return (
            reverse(
                "connectors:progress",
                args=(self.object.id,),
            )
            + "?refresh=true"
        )


class ConnectorProgress(TurboFrameUpdateView):
    template_name = "connectors/progress.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:setup"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id

        if self.object.integration.state == Integration.State.LOAD:
            if fivetran_client().has_completed_sync(self.object):
                context_data["done"] = complete_connector_sync(self.object)

        return context_data

    def form_valid(self, form):
        run_connector_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "connectors:progress",
            args=(self.object.id,),
        )


class ConnectorStatus(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:status"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if fivetran_client().has_completed_sync(self.object):
            complete_connector_sync(self.object)

        context_data["icon"] = INTEGRATION_STATE_TO_ICON[self.object.integration.state]
        context_data["text"] = INTEGRATION_STATE_TO_MESSAGE[
            self.object.integration.state
        ]

        return context_data
