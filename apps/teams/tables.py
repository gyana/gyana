from apps.users.models import CustomUser
from apps.projects.models import Project
from apps.utils.table import NaturalDatetimeColumn
from django_tables2 import Column, Table


class TeamMembersTable(Table):
    class Meta:
        model = CustomUser
        attrs = {"class": "table"}
        fields = (
            "email",
            "last_login",
            "date_joined",
        )

    email = Column(verbose_name="Email")
    last_login = NaturalDatetimeColumn()
    date_joined = NaturalDatetimeColumn()

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