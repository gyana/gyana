import analytics
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, TemplateView, View
from django.views.generic.edit import CreateView
from turbo_response.stream import TurboStream

from .fivetran import FivetranClient
from .forms import ConnectorCreateForm
from .models import Connector
from .tasks import update_integration_fivetran_schema
from .utils import get_service_categories, get_services


class ConnectorCreate(ProjectMixin, CreateView):
    template_name = "connectors/create.html"
    model = Connector
    form_class = ConnectorCreateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()
        return context_data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        kwargs["created_by"] = self.request.user
        kwargs["service"] = self.request.GET.get("service")
        return kwargs

    def form_valid(self, form):

        client = FivetranClient()
        fivetran_config = client.create(
            self.request.GET["service"], self.project.team.id
        )
        form.instance.fivetran_id = fivetran_config["fivetran_id"]

        # create the connector and integration
        self.object = form.save()

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                "id": self.object.integration.id,
                "type": Integration.Kind.CONNECTOR,
                "name": self.object.integration.name,
            },
        )

        internal_redirect = reverse(
            "project_integrations:setup",
            args=(
                self.project.id,
                self.object.integration.id,
            ),
        )

        return client.authorize(
            self.object.fivetran_id,
            f"{settings.EXTERNAL_URL}{internal_redirect}",
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


class ConnectorMock(TemplateView):
    template_name = "connectors/mock.html"
