from django.db import models
from django.template import loader
from django.template.loader import get_template
from django_tables2 import Column, LinkColumn, Table
from django_tables2.utils import A

from apps.base.tables import NaturalDatetimeColumn
from apps.projects.models import Project
from apps.teams.models import Membership


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

    def render_user__email(self, value, record):
        template = get_template("integrations/columns/name.html")
        return template.render(
            {"record": record, "value": value, "image": record.user.avatar_url}
        )


class TeamProjectsTable(Table):
    class Meta:
        model = Project
        attrs = {"class": "table"}
        template_name = "teams/tables/projects.html"
        fields = (
            "name",
            "num_rows",
            "integration_count",
            "workflow_count",
            "dashboard_count",
            "created",
            "updated",
            "access",
        )
        order_by = "-updated"

    name = Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn(verbose_name="Last updated")
    num_rows = Column(verbose_name="Rows")
    integration_count = Column(verbose_name="Integrations")
    workflow_count = Column(verbose_name="Workflows")
    dashboard_count = Column(verbose_name="Dashboards")

    def render_access(self, value, record):
        template = loader.get_template("projects/_project_access.html")
        return template.render({"value": record.access})

    def order_num_rows(self, queryset, is_descending):
        queryset = queryset.annotate(
            num_rows=models.Sum("integration__table__num_rows")
        ).order_by(("-" if is_descending else "") + "num_rows")
        return (queryset, True)

    def order_integration_count(self, queryset, is_descending):
        queryset = queryset.annotate(
            integration_count_=models.Count("integration")
        ).order_by(("-" if is_descending else "") + "integration_count_")
        return (queryset, True)

    def order_workflow_count(self, queryset, is_descending):
        queryset = queryset.annotate(workflow_count_=models.Count("workflow")).order_by(
            ("-" if is_descending else "") + "workflow_count_"
        )
        return (queryset, True)

    def order_dashboard_count(self, queryset, is_descending):
        queryset = queryset.annotate(
            dashboard_count_=models.Count("dashboard")
        ).order_by(("-" if is_descending else "") + "dashboard_count_")
        return (queryset, True)
