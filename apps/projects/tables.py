from apps.dashboards.tables import DashboardTable
from apps.integrations.tables import IntegrationListTable
from apps.projects.models import ProjectMembership
from apps.workflows.tables import WorkflowTable
from django_tables2 import Table
from django_tables2.utils import A


class ProjectIntegrationTable(IntegrationListTable):
    class Meta(IntegrationListTable.Meta):
        exclude = ("num_rows",)
        sequence = (
            "name",
            "kind",
            "created_ready",
        )


class ProjectWorkflowTable(WorkflowTable):
    class Meta(WorkflowTable.Meta):
        exclude = ("last_run", "last_sync", "created", "duplicate")
        sequence = ("name", "status", "updated")


class ProjectDashboardTable(DashboardTable):
    class Meta(DashboardTable.Meta):
        sequence = (
            "name",
            "status",
            "updated",
        )
        exclude = ("created", "duplicate")
