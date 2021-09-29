from django.template import loader
from django_tables2 import Column, LinkColumn, Table
from django_tables2.utils import A

from apps.base.table import NaturalDatetimeColumn
from apps.projects.models import Project
from apps.teams.models import Membership
from apps.users.models import CustomUser


class TeamMembershipTable(Table):
    class Meta:
        model = Membership
        attrs = {"class": "table"}
        fields = (
            A("user__email"),
            "role",
            A("user__last_login"),
            A("user__date_joined"),
        )

    user__email = LinkColumn(
        verbose_name="Email",
        viewname="team_members:update",
        args=(A("team__id"), A("id")),
    )
    user__last_login = NaturalDatetimeColumn(verbose_name="Last login")
    user__date_joined = NaturalDatetimeColumn(verbose_name="Date joined")


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
            "access",
        )

    name = Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    integration_count = Column(verbose_name="Integrations")
    workflow_count = Column(verbose_name="Workflows")
    dashboard_count = Column(verbose_name="Dashboards")

    def render_access(self, value, record):
        template = loader.get_template("projects/_project_access.html")
        return template.render({"value": record.access})
