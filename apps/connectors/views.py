import analytics
from apps.base.clients import fivetran_client
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from .forms import ConnectorCreateForm
from .models import Connector
from .config import get_service_categories, get_services


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

        return fivetran_client().authorize(
            self.object.fivetran_id,
            f"{settings.EXTERNAL_URL}{internal_redirect}",
        )


class ConnectorMock(TemplateView):
    template_name = "connectors/mock.html"
