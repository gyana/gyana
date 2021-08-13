from apps.base.turbo import TurboUpdateView
from apps.integrations.filters import IntegrationFilter
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .forms import IntegrationForm
from .mixins import ReadyMixin
from .models import Integration
from .tables import (
    IntegrationListTable,
    IntegrationPendingTable,
    StructureTable,
    UsedInTable,
)

# CRUDL


class IntegrationList(ProjectMixin, SingleTableMixin, FilterView):
    template_name = "integrations/list.html"
    model = Integration
    table_class = IntegrationListTable
    paginate_by = 20
    filterset_class = IntegrationFilter

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        project_integrations = Integration.objects.filter(project=self.project)

        context_data["integration_count"] = project_integrations.count()
        context_data["pending_integration_count"] = (
            project_integrations.filter(ready=False)
            .exclude(connector__fivetran_authorized=False)
            .count()
        )

        context_data["integration_kinds"] = Integration.Kind.choices

        return context_data

    def get_queryset(self) -> QuerySet:
        return (
            Integration.objects.filter(project=self.project, ready=True)
            .prefetch_related("table_set")
            .all()
        )


class IntegrationPending(ProjectMixin, SingleTableMixin, FilterView):
    template_name = "integrations/pending.html"
    model = Integration
    table_class = IntegrationPendingTable
    paginate_by = 20
    filterset_class = IntegrationFilter

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["pending_integration_count"] = (
            Integration.objects.filter(project=self.project, ready=False)
            .exclude(connector__fivetran_authorized=False)
            .count()
        )
        return context_data

    def get_queryset(self) -> QuerySet:
        return (
            Integration.objects.filter(project=self.project, ready=False)
            .exclude(connector__fivetran_authorized=False)
            .prefetch_related("table_set")
            .all()
        )


class IntegrationSetup(ProjectMixin, TurboUpdateView):
    template_name = "integrations/setup.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.object.state == "done":
            context_data["tables"] = self.object.table_set.order_by("_bq_table").all()
        context_data["state"] = self.request.GET.get("state") or self.object.state
        return context_data

    def form_valid(self, form):
        if not self.object.ready:
            self.object.created_ready = timezone.now()
        self.object.ready = True
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail",
            args=(self.project.id, self.object.id),
        )


class IntegrationDetail(ReadyMixin, TurboUpdateView):
    template_name = "integrations/detail.html"
    model = Integration
    form_class = IntegrationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["table"] = UsedInTable(self.object.used_in)
        return context

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationUpdate(ProjectMixin, TurboUpdateView):
    template_name = "integrations/update.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_form_class(self):
        return IntegrationForm

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )


class IntegrationDelete(ProjectMixin, DeleteView):
    template_name = "integrations/delete.html"
    model = Integration

    def get_success_url(self) -> str:
        return reverse("project_integrations:list", args=(self.project.id,))


class IntegrationData(ReadyMixin, DetailView):
    template_name = "integrations/data.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.order_by("_bq_table").all()
        return context_data


class IntegrationSettings(ProjectMixin, TurboUpdateView):
    template_name = "integrations/settings.html"
    model = Integration
    form_class = IntegrationForm

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )
