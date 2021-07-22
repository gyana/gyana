from apps.integrations.fivetran import FivetranClient
from apps.projects.mixins import ProjectMixin
from django.urls.base import reverse
from django.views.generic.edit import DeleteView
from django_tables2.views import SingleTableView

from .models import Table
from .tables import TableTable


class TableList(ProjectMixin, SingleTableView):
    template_name = "integrations/fivetran_tables/list.html"
    model = Table
    table_class = TableTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data

    def get_queryset(self):
        queryset = Table.objects.filter(project=self.project)

        return queryset


class TableDelete(ProjectMixin, DeleteView):
    template_name = "integrations/fivetran_tables/list.html"
    model = Table

    def delete(self, request, *args, **kwargs):
        """
        Handles deletion of data in third party places. BigQuery and Fivetran atm.

        If the table can't be unselected from the Fivetran schema it's important to
        keep the data around for the connector to function. So when it errors we also
        keep the BigQuery table, otherwise we throw it all away :).
        """
        table = self.get_object()
        # Stop syncing the table on the Fivetran connector
        client = FivetranClient(table.integration)
        # This call will return an error when the table being deleted
        # cannot be unselected in the Fivetran schema. This is fine and
        # we can ignore the error.
        res = client.update_table_config(table.bq_table, False)

        if res["code"] == "Success":
            # TODO: Delete the table in Big Query
            pass

        return super().delete(request, *args, **kwargs)

    def get_success_url(self) -> str:
        if self.request.GET.get("on-integration"):
            return reverse(
                "project_integrations:tables",
                args=(self.project.id, self.get_object().integration.id),
            )

        return reverse(
            "project_tables:list",
            args=(self.project.id,),
        )
