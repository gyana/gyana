from apps.base.turbo import TurboUpdateView
from apps.connectors.forms import ConnectorUpdateForm
from apps.connectors.models import Connector
from apps.integrations.filters import IntegrationFilter
from apps.integrations.tasks import KIND_TO_SYNC_TASK
from apps.projects.mixins import ProjectMixin
from apps.sheets.forms import SheetUpdateForm
from apps.sheets.models import Sheet
from apps.uploads.forms import UploadUpdateForm
from apps.uploads.models import Upload
from django.conf import settings
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .forms import KIND_TO_FORM_CLASS, IntegrationForm
from .mixins import ReadyMixin
from .models import Integration
from .tables import IntegrationListTable, IntegrationPendingTable, UsedInTable

# Overview


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


# Tabs


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


# Setup


class IntegrationSetup(ProjectMixin, DetailView):
    template_name = "integrations/setup.html"
    model = Integration
    fields = []


class IntegrationConfigure(ProjectMixin, TurboUpdateView):
    template_name = "integrations/configure.html"
    model = Integration

    def get_form_class(self):
        return KIND_TO_FORM_CLASS[self.object.kind]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.object.source_obj})
        return kwargs

    def form_valid(self, form):
        KIND_TO_SYNC_TASK[self.object.kind](self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load",
            args=(self.project.id, self.object.id),
        )


class IntegrationLoad(ProjectMixin, TurboUpdateView):
    template_name = "integrations/load.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.source_obj.sync_task_id
        return context_data

    def form_valid(self, form):
        KIND_TO_SYNC_TASK[self.object.kind](self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load",
            args=(self.project.id, self.object.id),
        )


class IntegrationDone(ProjectMixin, TurboUpdateView):
    template_name = "integrations/done.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.order_by("_bq_table").all()
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
