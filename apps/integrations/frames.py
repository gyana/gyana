from apps.projects.mixins import ProjectMixin
from apps.tables.bigquery import get_query_from_table
from apps.tables.models import Table
from apps.tables.tables import TableTable
from apps.utils.table_data import get_table
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.generic.base import TemplateView
from django_tables2 import SingleTableView
from django_tables2.config import RequestConfig
from django_tables2.views import SingleTableMixin
from turbo_response.views import TurboUpdateView

from .models import Integration


class IntegrationGrid(SingleTableMixin, TemplateView):
    template_name = "integrations/grid.html"
    paginate_by = 15

    def get_table_kwargs(self):
        return {"attrs": {"class": "table-data"}}

    def get_context_data(self, **kwargs):
        self.integration = Integration.objects.get(id=kwargs["pk"])

        table_id = self.request.GET.get("table_id")
        try:
            self.table_instance = (
                self.integration.table_set.get(pk=table_id)
                if table_id
                else self.integration.table_set.first()
            )
        except (Table.DoesNotExist, ValueError):
            self.table_instance = self.integration.table_set.first()

        context_data = super().get_context_data(**kwargs)
        context_data["table_instance"] = self.table_instance
        return context_data

    def get_table(self, **kwargs):
        query = get_query_from_table(self.table_instance)
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
        if self.object.kind == Integration.Kind.GOOGLE_SHEETS:
            self.object.start_sheets_sync()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("integrations:sync", args=(self.object.id,))


class IntegrationTablesList(ProjectMixin, SingleTableView):
    template_name = "tables/list.html"
    model = Integration
    table_class = TableTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Table.objects.filter(
            project=self.project, integration_id=self.kwargs["pk"]
        )
