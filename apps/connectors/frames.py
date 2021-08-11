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
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:setup",
            args=(
                self.object.integration.project.id,
                self.object.integration.id,
            ),
        )


class ConnectorSchema(ProjectMixin, DetailView):
    template_name = "connectors/schema.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["integration"] = self.get_object()
        context_data["schemas"] = FivetranClient().get_schema(
            self.object.connector.fivetran_id
        )

        return context_data

    def post(self, request, *args, **kwargs):
        integration = self.get_object()
        client = FivetranClient()
        client.update_schema(
            integration.connector.fivetran_id,
            [key for key in request.POST.keys() if key != "csrfmiddlewaretoken"],
        )

        return TurboStream(f"{integration.id}-schema-update-message").replace.response(
            f"""<p id="{ integration.id }-schema-update-message" class="ml-4 text-green">Successfully updated the schema</p>""",
            is_safe=True,
        )
