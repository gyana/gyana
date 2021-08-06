import uuid

import analytics
from apps.base.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.connectors.fivetran import FivetranClient
from apps.connectors.utils import get_service_categories, get_services
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query import QuerySet
from django.http.response import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import FORM_CLASS_MAP, FivetranForm, GoogleSheetsForm, IntegrationForm
from .models import Integration
from .tables import IntegrationTable, StructureTable

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

        context_data["integration_kinds"] = Integration.Kind.choices

        return context_data

    def get_queryset(self) -> QuerySet:
        queryset = Integration.objects.filter(project=self.project)
        # Add search query if it exists
        if query := self.request.GET.get("q"):
            queryset = (
                queryset.annotate(
                    similarity=TrigramSimilarity("name", query),
                )
                .filter(similarity__gt=0.05)
                .order_by("-similarity")
            )
        if (kind := self.request.GET.get("kind")) and kind in Integration.Kind.values:
            queryset = queryset.filter(kind=kind)

        return queryset.prefetch_related("table_set").all()


class IntegrationNew(ProjectMixin, TemplateView):
    template_name = "integrations/new.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()

        return context_data


class IntegrationCreate(ProjectMixin, TurboCreateView):
    template_name = "integrations/create.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = self.request.GET.get("kind")
        initial["service"] = self.request.GET.get("service")
        initial["project"] = self.project

        return initial

    def get_form_class(self):
        if (kind := self.request.GET.get("kind")) is not None:
            analytics.track(
                self.request.user.id, NEW_INTEGRATION_START_EVENT, {"type": kind}
            )

            if kind == Integration.Kind.GOOGLE_SHEETS:
                return GoogleSheetsForm
            elif kind == Integration.Kind.FIVETRAN:
                return FivetranForm

        return GoogleSheetsForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        if form.is_valid():
            instance_session_key = uuid.uuid4().hex

            analytics.track(
                self.request.user.id,
                INTEGRATION_CREATED_EVENT,
                {
                    "id": form.instance.id,
                    "type": form.instance.kind,
                    "name": form.instance.name,
                },
            )

            if form.instance.kind == Integration.Kind.FIVETRAN:
                client = FivetranClient()
                fivetran_config = client.create(
                    form.cleaned_data["service"], form.instance.project.team.id
                )

                self.request.session[instance_session_key] = {
                    **form.cleaned_data,
                    **fivetran_config,
                    "project": form.cleaned_data["project"].id,
                    "team_id": form.instance.project.team.id,
                    "fivetran_authorized": True,
                }

                internal_redirect = reverse(
                    "project_integrations_connectors:setup",
                    args=(form.instance.project.id, instance_session_key),
                )

                return client.authorize(
                    fivetran_config["fivetran_id"],
                    f"{settings.EXTERNAL_URL}{internal_redirect}",
                )

            if form.instance.kind == Integration.Kind.GOOGLE_SHEETS:
                response = super().form_valid(form)
                form.instance.start_sheets_sync()
                return response

        return HttpResponseBadRequest()

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationDetail(ProjectMixin, TurboUpdateView):
    template_name = "integrations/detail.html"
    model = Integration
    form_class = IntegrationForm

    def get_context_data(self, **kwargs):
        from .tables import UsedInTable

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
        return FORM_CLASS_MAP[self.object.kind]

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )


class IntegrationDelete(ProjectMixin, DeleteView):
    template_name = "integrations/delete.html"
    model = Integration

    def get_success_url(self) -> str:
        return reverse("project_integrations:list", args=(self.project.id,))


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

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.all()

        return context_data


class IntegrationSettings(ProjectMixin, TurboUpdateView):
    template_name = "integrations/settings.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_form_class(self):
        return FORM_CLASS_MAP[self.object.kind]

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )
