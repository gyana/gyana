from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
from apps.integrations.models import Integration
from apps.integrations.tables import (
    INTEGRATION_STATE_TO_ICON,
    INTEGRATION_STATE_TO_MESSAGE,
)
from django.shortcuts import redirect
from django.urls import reverse

from .forms import ConnectorUpdateForm
from .models import Connector
from .tasks import run_connector_sync


class ConnectorUpdate(TurboFrameUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorUpdateForm
    turbo_frame_dom_id = "connectors:update"

    def form_valid(self, form):
        run_connector_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:setup",
            args=(
                self.object.integration.project.id,
                self.object.integration.id,
            ),
        )


class ConnectorProgress(TurboFrameUpdateView):
    template_name = "connectors/progress.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:progress"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id
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
        integration = self.object.integration
        if integration.state == Integration.State.LOAD:
            is_historical_synced = fivetran_client().is_historical_synced(
                self.object.fivetran_id
            )
            if is_historical_synced:
                integration.state = Integration.State.DONE
                integration.save()

        context_data["icon"] = INTEGRATION_STATE_TO_ICON[integration.state]
        context_data["text"] = INTEGRATION_STATE_TO_MESSAGE[integration.state]

        return context_data
