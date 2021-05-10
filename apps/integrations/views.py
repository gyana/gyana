import json

from apps.integrations.tables import IntegrationTable
from apps.integrations.tasks import poll_fivetran_historical_sync
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from lib.bigquery import create_external_table, query_integration, sync_table
from lib.fivetran import FivetranClient, get_services
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import CSVForm, FivetranForm, GoogleSheetsForm
from .models import Integration

# CRUDL


class IntegrationList(ProjectMixin, SingleTableView):
    template_name = "integrations/list.html"
    model = Integration
    table_class = IntegrationTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Integration.objects.filter(project=self.project).all()


class IntegrationCreate(ProjectMixin, TurboCreateView):
    template_name = "integrations/create.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind

        if (
            self.request.GET.get("kind") == Integration.Kind.FIVETRAN
            and self.request.GET.get("service") is None
        ):
            context_data["services"] = get_services()
        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = self.request.GET.get("kind")
        initial["service"] = self.request.GET.get("service")
        initial["project"] = self.project
        return initial

    def get_form_class(self):
        if (kind := self.request.GET.get("kind")) is not None:
            if kind == Integration.Kind.GOOGLE_SHEETS:
                return GoogleSheetsForm
            elif kind == Integration.Kind.CSV:
                return CSVForm
            elif kind == Integration.Kind.FIVETRAN:
                return FivetranForm

        return CSVForm

    def get_success_url(self) -> str:
        return reverse(
            "projects:integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationDetail(ProjectMixin, DetailView):
    template_name = "integrations/detail.html"
    model = Integration


class IntegrationUpdate(ProjectMixin, TurboUpdateView):
    template_name = "integrations/update.html"
    model = Integration

    def get_form_class(self):
        if self.object.kind == Integration.Kind.GOOGLE_SHEETS:
            return GoogleSheetsForm
        elif self.object.kind == Integration.Kind.CSV:
            return CSVForm

    def get_success_url(self) -> str:
        return reverse(
            "projects:integrations:settings", args=(self.project.id, self.object.id)
        )


class IntegrationDelete(ProjectMixin, DeleteView):
    template_name = "integrations/delete.html"
    model = Integration

    def get_success_url(self) -> str:
        return reverse("projects:integrations:list", args=(self.project.id,))


class IntegrationStructure(ProjectMixin, DetailView):
    template_name = "integrations/structure.html"
    model = Integration


class IntegrationData(ProjectMixin, DetailView):
    template_name = "integrations/data.html"
    model = Integration


class IntegrationSettings(ProjectMixin, DetailView):
    template_name = "integrations/settings.html"
    model = Integration


# Turbo frames


class IntegrationGrid(DetailView):
    template_name = "integrations/grid.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        df = query_integration(self.object)

        context_data["columns"] = json.dumps([{"field": col} for col in df.columns])
        context_data["rows"] = df.to_json(orient="records")

        return context_data


class IntegrationSync(TurboUpdateView):
    template_name = "integrations/sync.html"
    model = Integration
    fields = []

    def form_valid(self, form):
        external_table_id = create_external_table(self.object)
        sync_table(self.object, external_table_id)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("integrations:sync", args=(self.object.id,))


# Turbo frames


class IntegrationAuthorize(DetailView):

    model = Integration
    template_name = "integrations/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = context["integration"]

        if integration.fivetran_id is None:
            FivetranClient(integration).create()

        return context


# Endpoints


def authorize_fivetran(request: HttpRequest, pk: int):

    integration = get_object_or_404(Integration, pk=pk)
    uri = reverse("integrations:authorize-fivetran-redirect", args=(pk,))
    redirect_uri = (
        f"{settings.EXTERNAL_URL}{uri}?original_uri={request.GET.get('original_uri')}"
    )

    return FivetranClient(integration).authorize(redirect_uri)


def authorize_fivetran_redirect(request: HttpRequest, pk: int):

    integration = get_object_or_404(Integration, pk=pk)
    integration.fivetran_authorized = True

    result = poll_fivetran_historical_sync.delay(integration.id)
    integration.fivetran_poll_historical_sync_task_id = result.task_id

    integration.save()

    return redirect(request.GET.get("original_uri"))
