from django_tables2.tables import Table
from django_tables2.views import SingleTableMixin

from apps.base.core.bigquery import get_humanize_from_bigquery_type
from apps.base.core.table_data import RequestConfig, get_table
from apps.base.frames import TurboFrameDetailView, TurboFrameTemplateView
from apps.integrations.tables import StructureTable
from apps.projects.mixins import ProjectMixin
from apps.tables.bigquery import get_bq_table_schema_from_table, get_query_from_table

from .mixins import TableInstanceMixin
from .models import Integration


class IntegrationOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "integrations/overview.html"
    turbo_frame_dom_id = "integrations:overview"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        queryset = self.project.integration_set

        ready = queryset.ready().count()
        pending = queryset.pending().count()
        broken = queryset.broken().count()

        context_data["integrations"] = {
            "all": queryset.visible().order_by("-updated").all()[:5],
            "total": ready + pending,
            "ready": ready,
            "attention": queryset.needs_attention().count(),
            "loading": queryset.loading().count(),
            "broken": broken,
            "operational": broken == 0 and pending == 0,
            "connectors": queryset.connectors().all(),
            "sheet_count": queryset.sheets().count(),
            "upload_count": queryset.uploads().count(),
        }

        return context_data


class IntegrationGrid(TableInstanceMixin, SingleTableMixin, TurboFrameDetailView):
    template_name = "integrations/grid.html"
    model = Integration
    paginate_by = 15
    turbo_frame_dom_id = "integrations:grid"

    def get_table(self, **kwargs):
        if not self.table_instance:
            return type("DynamicTable", (Table,), {})(data=[])
        query = get_query_from_table(self.table_instance)
        table = get_table(query.schema(), query, None, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationSchema(TableInstanceMixin, SingleTableMixin, TurboFrameDetailView):
    template_name = "integrations/schema.html"
    model = Integration
    paginate_by = 15
    turbo_frame_dom_id = "integrations:schema"
    table_class = StructureTable

    def get_table_data(self, **kwargs):
        if not self.table_instance:
            return []
        return [
            {"type": get_humanize_from_bigquery_type(t.field_type), "name": str(t.name)}
            for t in get_bq_table_schema_from_table(self.table_instance)
        ]


class IntegrationTableDetail(TableInstanceMixin, TurboFrameDetailView):
    template_name = "integrations/table_detail.html"
    model = Integration
    turbo_frame_dom_id = "integrations:table_detail"
