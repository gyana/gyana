from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, View
from turbo_response.stream import TurboStream

from .fivetran import FivetranClient
from .tasks import update_integration_fivetran_schema


class IntegrationSchema(ProjectMixin, DetailView):
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


class ConnectorSetup(ProjectMixin, TemplateResponseMixin, View):
    template_name = "connectors/setup.html"

    def get_context_data(self, project_id, session_key, **kwargs):
        integration_data = self.request.session[session_key]
        return {
            "service": integration_data["service"],
            "schemas": FivetranClient().get_schema(integration_data["fivetran_id"]),
            "project": self.project,
        }

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, session_key, **kwargs):
        integration_data = self.request.session[session_key]
        task_id = update_integration_fivetran_schema.delay(
            integration_data["fivetran_id"],
            [key for key in request.POST.keys() if key != "csrfmiddlewaretoken"],
        )

        return (
            TurboStream("integration-setup-container")
            .replace.template(
                "connectors/fivetran_setup/_flow.html",
                {
                    "table_select_task_id": task_id,
                    "turbo_url": reverse(
                        "connectors:start-fivetran-integration",
                        args=(session_key,),
                    ),
                },
            )
            .response(request)
        )
