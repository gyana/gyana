from django.urls.base import reverse
from django.views.generic import DetailView, TemplateView
from django_tables2.tables import Table
from django_tables2.views import SingleTableMixin

from apps.base.core.bigquery import get_humanize_from_bigquery_type
from apps.base.core.table_data import RequestConfig, get_table
from apps.base.views import UpdateView
from apps.integrations.forms import IntegrationNameForm
from apps.integrations.tables import StructureTable
from apps.projects.mixins import ProjectMixin
from apps.tables.bigquery import get_bq_table_schema_from_table, get_query_from_table

from .mixins import TableInstanceMixin
from .models import Integration


class IntegrationOverview(ProjectMixin, TemplateView):
    template_name = "integrations/overview.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        queryset = self.project.integration_set

        ready = queryset.ready().count()
        pending = queryset.pending().count()
        # todo: decide definition of broken for CSV, Sheet, API, etc
        broken = 0

        context_data["integrations"] = {
            "all": queryset.visible().order_by("-updated").all()[:5],
            "total": ready + pending,
            "ready": ready,
            "attention": queryset.needs_attention().count(),
            "loading": queryset.loading().count(),
            "broken": broken,
            "operational": broken == 0 and pending == 0,
            "sheet_count": queryset.sheets().count(),
            "upload_count": queryset.uploads().count(),
        }

        return context_data


class IntegrationGrid(TableInstanceMixin, SingleTableMixin, DetailView):
    template_name = "integrations/grid.html"
    model = Integration
    paginate_by = 15

    def get_table(self, **kwargs):
        if not self.table_instance:
            return type("DynamicTable", (Table,), {})(data=[])
        query = get_query_from_table(self.table_instance)
        table = get_table(query.schema(), query, None, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationPreview(TableInstanceMixin, SingleTableMixin, DetailView):
    template_name = "integrations/grid.html"
    model = Integration
    paginate_by = 5

    def get_table(self, **kwargs):
        query = get_query_from_table(self.table_instance)
        table = get_table(query.schema(), query.limit(15), None, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationSchema(TableInstanceMixin, SingleTableMixin, DetailView):
    template_name = "integrations/schema.html"
    model = Integration
    paginate_by = 15
    table_class = StructureTable

    def get_table_data(self, **kwargs):
        if not self.table_instance:
            return []
        return [
            {"type": get_humanize_from_bigquery_type(t.field_type), "name": str(t.name)}
            for t in get_bq_table_schema_from_table(self.table_instance)
        ]


class IntegrationName(UpdateView):
    template_name = "integrations/name.html"
    model = Integration
    form_class = IntegrationNameForm

    def get_success_url(self) -> str:
        return reverse("integrations:name", args=(self.object.id,))
