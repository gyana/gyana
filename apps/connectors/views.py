import analytics
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from apps.base.analytics import (
    INTEGRATION_AUTHORIZED_EVENT,
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.base.clients import fivetran_client
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin

from .config import get_service_categories, get_services
from .forms import ConnectorCreateForm
from .models import Connector


class ConnectorCreate(ProjectMixin, CreateView):
    template_name = "connectors/create.html"
    model = Connector
    form_class = ConnectorCreateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()
        return context_data

    def get(self, request, *args, **kwargs):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.CONNECTOR},
        )
        return super().get(request, *args, **kwargs)

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
            "project_integrations_connectors:authorize",
            args=(
                self.project.id,
                self.object.id,
            ),
        )

        return redirect(
            fivetran_client().authorize(
                self.object,
                f"{settings.EXTERNAL_URL}{internal_redirect}",
            )
        )


class ConnectorAuthorize(ProjectMixin, DetailView):
    model = Connector

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.fivetran_authorized = True
        self.object.save()

        analytics.track(
            self.request.user.id,
            INTEGRATION_AUTHORIZED_EVENT,
            {
                "id": self.object.integration.id,
                "type": Integration.Kind.CONNECTOR,
                "name": self.object.integration.name,
            },
        )

        return redirect(
            reverse(
                "project_integrations:configure",
                args=(self.project.id, self.object.integration.id),
            )
        )


class ConnectorMock(TemplateView):
    template_name = "connectors/mock.html"
