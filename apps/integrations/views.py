import analytics
from apps.base import clients
from apps.base.analytics import INTEGRATION_SYNC_STARTED_EVENT
from apps.base.turbo import TurboUpdateView
from apps.connectors.sync import handle_syncing_connector
from apps.integrations.filters import IntegrationFilter
from apps.integrations.tasks import KIND_TO_SYNC_TASK
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.shortcuts import redirect
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
        queryset = self.project.integration_set

        context_data["integration_count"] = queryset.ready().count()
        context_data["pending_integration_count"] = queryset.pending().count()
        context_data["show_zero_state"] = queryset.visible().count() == 0
        context_data["integration_kinds"] = Integration.Kind.choices

        return context_data

    def get_queryset(self) -> QuerySet:
        return self.project.integration_set.ready().prefetch_related("table_set").all()


class IntegrationPending(ProjectMixin, SingleTableMixin, FilterView):
    template_name = "integrations/pending.html"
    model = Integration
    table_class = IntegrationPendingTable
    paginate_by = 20
    filterset_class = IntegrationFilter

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        queryset = self.project.integration_set
        context_data["pending_integration_count"] = queryset.pending().count()
        return context_data

    def get_queryset(self) -> QuerySet:
        return (
            self.project.integration_set.pending().prefetch_related("table_set").all()
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


class IntegrationData(ProjectMixin, DetailView):
    template_name = "integrations/data.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.order_by("bq_table").all()
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
    form_class = IntegrationForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT
        return context_data

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )


class IntegrationDelete(ProjectMixin, DeleteView):
    template_name = "integrations/delete.html"
    model = Integration

    def delete(self, request, *args, **kwargs):
        r = super().delete(request, *args, **kwargs)
        self.project.team.update_row_count()
        return r

    def get_success_url(self) -> str:
        return reverse("project_integrations:list", args=(self.project.id,))


# Setup


class IntegrationConfigure(ProjectMixin, TurboUpdateView):
    template_name = "integrations/configure.html"
    model = Integration

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.state == Integration.State.LOAD:
            return redirect(
                "project_integrations:load", self.project.id, self.object.id
            )
        return super().get(request, *args, **kwargs)

    def get_form_class(self):
        return KIND_TO_FORM_CLASS[self.object.kind]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.object.source_obj})
        return kwargs

    def form_valid(self, form):
        # don't assigned the result to self.object
        form.save()
        KIND_TO_SYNC_TASK[self.object.kind](self.object.source_obj)
        analytics.track(
            self.request.user.id,
            INTEGRATION_SYNC_STARTED_EVENT,
            {
                "id": self.object.id,
                "type": self.object.kind,
                "name": self.object.name,
            },
        )
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load", args=(self.project.id, self.object.id)
        )


class IntegrationLoad(ProjectMixin, TurboUpdateView):
    template_name = "integrations/load.html"
    model = Integration
    fields = []

    def get(self, request, *args, **kwargs):

        self.object = self.get_object()

        if self.object.kind == Integration.Kind.CONNECTOR:
            handle_syncing_connector(self.object.source_obj)
            self.object.refresh_from_db()

        if self.object.state not in [
            Integration.State.LOAD,
            Integration.State.ERROR,
        ]:
            return redirect(
                "project_integrations:done", self.project.id, self.object.id
            )

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["sync_task_id"] = self.object.source_obj.sync_task_id

        if (
            self.object.kind == Integration.Kind.CONNECTOR
            and self.object.state == Integration.State.ERROR
        ):
            fivetran_obj = clients.fivetran().get(self.object.source_obj)
            if fivetran_obj.status.setup_state != "connected":
                context_data["broken"] = True

        return context_data

    def form_valid(self, form):
        KIND_TO_SYNC_TASK[self.object.kind](self.object.source_obj)
        # don't assigned the result to self.object
        form.save()
        return redirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:load", args=(self.project.id, self.object.id)
        )


class IntegrationDone(ProjectMixin, TurboUpdateView):
    template_name = "integrations/done.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.order_by("bq_table").all()

        team = self.project.team
        team.update_row_count()

        context_data["exceeds_row_limit"] = team.check_new_rows(self.object.num_rows)
        context_data["projected_num_rows"] = team.add_new_rows(self.object.num_rows)

        return context_data

    def form_valid(self, form):
        if not self.object.ready:
            self.object.created_ready = timezone.now()
            self.object.ready = True
            self.object.save()

        r = super().form_valid(form)
        self.project.team.update_row_count()
        return r

    def get_success_url(self) -> str:
        if not self.project.ready:
            return reverse(
                "project_templateinstances:list",
                args=(self.project.id,),
            )
        return reverse(
            "project_integrations:detail",
            args=(self.project.id, self.object.id),
        )
