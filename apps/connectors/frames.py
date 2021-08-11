from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameUpdateView
from apps.connectors.forms import ConnectorUpdateForm
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.urls import reverse
from django.views.generic import DetailView
from turbo_response.stream import TurboStream

from .fivetran import FivetranClient
from .models import Connector


class ConnectorUpdate(TurboFrameUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorUpdateForm
    turbo_frame_dom_id = "connectors:update"

    def form_valid(self, form):
        fivetran_client().start(self.object)
        self.object.integration.state = Integration.State.LOAD
        self.object.integration.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:setup",
            args=(
                self.object.integration.project.id,
                self.object.integration.id,
            ),
        )
