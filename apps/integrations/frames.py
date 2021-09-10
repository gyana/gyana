from apps.base.bigquery import get_humanize_from_bigquery_type
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameListView,
    TurboFrameTemplateView,
)
from apps.base.table_data import RequestConfig, get_table
from apps.integrations.tables import StructureTable
from apps.projects.mixins import ProjectMixin
from apps.tables.bigquery import get_bq_table_schema_from_table, get_query_from_table
from apps.tables.models import Table
from apps.tables.tables import TableTable
from django.utils import timezone
from django_tables2.views import SingleTableMixin

from .models import Integration


class IntegrationOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "integrations/overview.html"
    turbo_frame_dom_id = "integrations:overview"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        total = self.project.integration_set
        ready = total.filter(ready=True)
        pending = total.filter(ready=False).exclude(
            connector__fivetran_authorized=False
        )
        broken = ready.filter(
            kind=Integration.Kind.CONNECTOR,
            connector__fivetran_succeeded_at__lt=timezone.now()
            - timezone.timedelta(hours=24),
        ).count()

        context_data["integrations"] = {
            "total": total.count(),
            "ready": ready.count(),
            "attention": pending.exclude(state=Integration.State.LOAD).count(),
            "loading": pending.filter(state=Integration.State.LOAD).count(),
            "broken": broken,
            "operational": broken == 0 and pending.count() == 0,
            "connectors": ready.filter(kind=Integration.Kind.CONNECTOR).all(),
            "sheet_count": ready.filter(kind=Integration.Kind.SHEET).count(),
            "upload_count": ready.filter(kind=Integration.Kind.UPLOAD).count(),
        }

        return context_data


class IntegrationGrid(SingleTableMixin, TurboFrameDetailView):
    template_name = "integrations/grid.html"
    model = Integration
    paginate_by = 15
    turbo_frame_dom_id = "integrations:grid"

    def get_table_kwargs(self):
        return {"attrs": {"class": "table-data"}}

    def get_context_data(self, **kwargs):
        table_id = self.request.GET.get("table_id")
        try:
            self.table_instance = (
                self.object.table_set.get(pk=table_id)
                if table_id
                else self.object.table_set.first()
            )
        except (Table.DoesNotExist, ValueError):
            self.table_instance = self.object.table_set.first()

        context_data = super().get_context_data(**kwargs)
        context_data["table_instance"] = self.table_instance
        return context_data

    def get_table(self, **kwargs):
        query = get_query_from_table(self.table_instance)
        table = get_table(query.schema(), query, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationSchema(SingleTableMixin, TurboFrameDetailView):
    template_name = "integrations/schema.html"
    model = Integration
    paginate_by = 15
    turbo_frame_dom_id = "integrations:schema"
    table_class = StructureTable

    def get_table_kwargs(self):
        return {"attrs": {"class": "table-data"}}

    def get_context_data(self, **kwargs):
        table_id = self.request.GET.get("table_id")
        try:
            self.table_instance = (
                self.object.table_set.get(pk=table_id)
                if table_id
                else self.object.table_set.first()
            )
        except (Table.DoesNotExist, ValueError):
            self.table_instance = self.object.table_set.first()

        context_data = super().get_context_data(**kwargs)
        context_data["table_instance"] = self.table_instance
        return context_data

    def get_table_data(self, **kwargs):

        return [
            {"type": get_humanize_from_bigquery_type(t.field_type), "name": str(t.name)}
            for t in get_bq_table_schema_from_table(self.table_instance)
        ]


class IntegrationTablesList(ProjectMixin, SingleTableMixin, TurboFrameListView):
    template_name = "tables/list.html"
    model = Integration
    table_class = TableTable
    paginate_by = 20
    turbo_frame_dom_id = "tables-list"

    def get_queryset(self):
        return Table.objects.filter(
            project=self.project, integration_id=self.kwargs["pk"]
        )
