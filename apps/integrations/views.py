import json

from apps.projects.mixins import ProjectMixin
from apps.utils.table_data import get_table
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView, Table
from django_tables2.config import RequestConfig
from django_tables2.views import SingleTableMixin
from turbo_response.views import TurboCreateView, TurboUpdateView

from .bigquery import query_integration
from .fivetran import FivetranClient, get_services
from .forms import CSVForm, FivetranForm, GoogleSheetsForm
from .models import Integration
from .tables import IntegrationTable, StructureTable
from .tasks import poll_fivetran_historical_sync

# CRUDL


class IntegrationList(ProjectMixin, SingleTableView):
    template_name = "integrations/list.html"
    model = Integration
    table_class = IntegrationTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["integration_count"] = Integration.objects.filter(
            project=self.project
        ).count()

        return context_data

    def get_queryset(self) -> QuerySet:
        return (
            Integration.objects.filter(project=self.project)
            .prefetch_related("table_set")
            .all()
        )


class IntegrationCreate(ProjectMixin, TurboCreateView):
    template_name = "integrations/create.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

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

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # after the model is saved by the super call, we start syncing it.
        form.instance.start_sync()
        return response

    def get_success_url(self) -> str:
        return reverse(
            "projects:integrations:detail", args=(self.project.id, self.object.id)
        )


class UsedInTable(Table):
    class Meta:
        model = Integration
        attrs = {"class": "table"}
        fields = (
            "name",
            "project",
            "kind",
            "created",
            "updated",
        )


class IntegrationDetail(ProjectMixin, DetailView):
    template_name = "integrations/detail.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table"] = UsedInTable(self.object.used_in)
        return context


class IntegrationUpdate(ProjectMixin, TurboUpdateView):
    template_name = "integrations/update.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

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
    table_class = StructureTable

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = []

        for table in self.object.table_set.all():
            table_data = [
                {"type": str(field_type), "name": field_name}
                for field_name, field_type in table.schema.items()
            ]
            context_data["tables"].append(
                {"title": table.bq_table, "table_struct": StructureTable(table_data)}
            )

        return context_data


class IntegrationData(ProjectMixin, DetailView):
    template_name = "integrations/data.html"
    model = Integration


class IntegrationSettings(ProjectMixin, TurboUpdateView):
    template_name = "integrations/settings.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_form_class(self):
        if self.object.kind == Integration.Kind.GOOGLE_SHEETS:
            return GoogleSheetsForm
        elif self.object.kind == Integration.Kind.CSV:
            return CSVForm

    def get_success_url(self) -> str:
        return reverse(
            "projects:integrations:settings", args=(self.project.id, self.object.id)
        )


# Turbo frames


class IntegrationGrid(SingleTableMixin, TemplateView):
    template_name = "integrations/grid.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        self.integration = Integration.objects.get(id=kwargs["pk"])
        return super().get_context_data(**kwargs)

    def get_table(self, **kwargs):
        query = query_integration(self.integration)
        table = get_table(query.schema(), query, **kwargs)
        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationSync(TurboUpdateView):
    template_name = "integrations/sync.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data[
            "external_table_sync_task_id"
        ] = self.object.external_table_sync_task_id

        return context_data

    def form_valid(self, form):
        self.object.start_sync()
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
