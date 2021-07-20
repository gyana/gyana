from apps.dashboards.tables import DashboardTable
from apps.integrations.tables import IntegrationTable
from apps.workflows.tables import WorkflowTable
from django_tables2 import Column, Table


class ProjectIntegrationTable(IntegrationTable):
    class Meta(IntegrationTable.Meta):
        exclude = (
            "num_rows",
            "last_synced",
            "created",
        )
        sequence = (
            "name",
            "status",
            "kind",
            "updated",
        )


class ProjectWorkflowTable(WorkflowTable):
    class Meta(WorkflowTable.Meta):
        exclude = ("last_run", "last_sync", "created", "duplicate")
        sequence = ("name", "status", "updated")


class ProjectDashboardTable(DashboardTable):
    class Meta(DashboardTable.Meta):
        sequence = ("name", "status", "updated")
        exclude = ("created",)
