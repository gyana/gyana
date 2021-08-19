import analytics
from apps.base.clients import fivetran_client
from apps.base.frames import TurboFrameUpdateView
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from apps.base.turbo import TurboUpdateView
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from .config import get_service_categories, get_services
from .forms import ConnectorCreateForm, ConnectorUpdateForm
from .models import Connector
from .tasks import complete_connector_sync, run_connector_sync


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
            "project_integrations_connectors:authorize",
            args=(
                self.project.id,
                self.object.id,
            ),
        )

        return fivetran_client().authorize(
            self.object,
            f"{settings.EXTERNAL_URL}{internal_redirect}",
        )


class ConnectorAuthorize(ProjectMixin, DetailView):
    model = Connector

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.fivetran_authorized = True
        self.object.save()
        return redirect(
            reverse(
                "project_integrations_connectors:update",
                args=(
                    self.project.id,
                    self.object.id,
                ),
            )
        )


class ConnectorMock(TemplateView):
    template_name = "connectors/mock.html"


class ConnectorUpdate(ProjectMixin, TurboUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorUpdateForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration"] = self.object.integration
        return context_data

    def form_valid(self, form):
        run_connector_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_connectors:progress",
            args=(
                self.project.id,
                self.object.id,
            ),
        )


class ConnectorProgress(ProjectMixin, TurboUpdateView):
    template_name = "connectors/load.html"
    model = Connector
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.sync_task_id
        context_data["integration"] = self.object.integration

        if self.object.integration.state == Integration.State.LOAD:
            if fivetran_client().has_completed_sync(self.object):
                context_data["done"] = complete_connector_sync(self.object)

        return context_data

    def form_valid(self, form):
        run_connector_sync(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations_connectors:progress",
            args=(
                self.project.id,
                self.object.id,
            ),
        )
