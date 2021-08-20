from apps.base.clients import fivetran_client
from apps.base.turbo import TurboUpdateView
from apps.connectors.tasks import complete_connector_sync
from apps.integrations.filters import IntegrationFilter
from apps.integrations.tasks import KIND_TO_SYNC_TASK
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.http.response import HttpResponseRedirect
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


class IntegrationConfigure(ProjectMixin, TurboUpdateView):
    template_name = "integrations/configure.html"
    model = Integration

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.state == Integration.State.LOAD:
            return HttpResponseRedirect(
                reverse(
                    "project_integrations:load",
                    args=(self.project.id, self.object.id),
                )
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # connector task may have expired, need to check the source
        if self.object.kind == Integration.Kind.CONNECTOR:
            if fivetran_client().has_completed_sync(self.object.source_obj):
                context_data["done"] = complete_connector_sync(self.object.source_obj)

        return context_data

    def get_form_class(self):
        return KIND_TO_FORM_CLASS[self.object.kind]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.object.source_obj})
        return kwargs

    def form_valid(self, form):
        KIND_TO_SYNC_TASK[self.object.kind](self.object.source_obj)
        # don't assigned the result to self.object
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load",
            args=(self.project.id, self.object.id),
        )


class IntegrationLoad(ProjectMixin, TurboUpdateView):
    template_name = "integrations/load.html"
    model = Integration
    fields = []

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.state not in [
            Integration.State.LOAD,
            Integration.State.ERROR,
        ]:
            return HttpResponseRedirect(
                reverse(
                    "project_integrations:done",
                    args=(self.project.id, self.object.id),
                )
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.source_obj.sync_task_id
        return context_data

    def form_valid(self, form):
        KIND_TO_SYNC_TASK[self.object.kind](self.object.source_obj)
        # don't assigned the result to self.object
        form.save()
        return HttpResponseRedirect(self.get_success_url())

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

        team = self.project.team
        team.update_row_count()
        exceeds_row_limit = self.object.num_rows + team.row_count > team.row_limit
        context_data["exceeds_row_limit"] = exceeds_row_limit
        if exceeds_row_limit:
            context_data["projected_num_rows"] = self.object.num_rows + team.row_count

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
