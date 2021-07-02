from apps.utils.table import NaturalDatetimeColumn
from apps.projects.models import Project
from django_tables2 import Column, Table

class TeamProjectsTable(Table):
    class Meta:
        model = Project
        attrs = {"class": "table"}
        fields = (
            "name",
            "integration_count",
            "workflow_count",
            "dashboard_count",
            "created",
            "updated",
        )

    name = Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    integration_count = Column(verbose_name="Integrations")
    workflow_count = Column(verbose_name="Workflows")
    dashboard_count = Column(verbose_name="Dashboards")