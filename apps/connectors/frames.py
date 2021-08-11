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

    # def get_context_data(self, *args, **kwargs):
    #     context_data = super().get_context_data(*args, **kwargs)
    #     context_data["schemas"] = fivetran_client().get_schema(self.object.fivetran_id)
    #     return context_data

    # def form_valid(self, form):
    #     fivetran_client().start(self.object)
    #     return super().form_valid(form)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        schema = fivetran_client().get_schema(self.object.fivetran_id)

        name, config = list(schema.items())[0]
        form_kwargs["table_choices"] = [
            (t, t.replace("_", " ").title()) for t in config["tables"]
        ]
        return form_kwargs

    def get_initial(self):
        initial = super().get_initial()

        schema = fivetran_client().get_schema(self.object.fivetran_id)

        name, config = list(schema.items())[0]
        initial["schema"] = config["enabled"]
        initial["tables"] = [
            t for t in config["tables"] if config["tables"][t]["enabled"]
        ]

        return initial

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
