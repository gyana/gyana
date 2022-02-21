import django_tables2 as tables
from django_tables2.utils import A

from apps.integrations.tables import PendingStatusColumn

from .models import Template, TemplateInstance, TemplateIntegration


class TemplateTable(tables.Table):
    class Meta:
        model = Template
        attrs = {"class": "table"}
        fields = ("name", "description")

    # need access to team id
    name = tables.TemplateColumn(
        '<a href="{% url "team_templates:create" team.id record.id %}">{{ record.name }}</a>'
    )


class TemplateInstanceTable(tables.Table):
    class Meta:
        model = TemplateInstance
        attrs = {"class": "table"}
        fields = ["completed"]
        sequence = ("template", "completed")

    template = tables.LinkColumn(
        "project_templateinstances:update", args=(A("project__id"), A("id"))
    )


class TemplateIntegrationTable(tables.Table):
    class Meta:
        model = TemplateIntegration
        attrs = {"class": "table"}
        fields = ()

    icon = tables.TemplateColumn(
        '{% load static %}<img class="h-12 w-12 mr-4" src="{% static record.source_integration.icon %}" title="{{ record.source_integration.name }}" />'
    )
    name = tables.Column(accessor="source_integration__display_kind")
    action = tables.TemplateColumn(
        """
        {% if record.target_integration is not None %}
            <a class="link" href="{{ record.target_integration.get_absolute_url }}" data-turbo-frame="_top"> Edit </a>
        {% else %}
             <a class="link" href="{% url 'project_integrations_connectors:create' table.project.id %}?service={{ record.source_integration.connector.service }}" data-turbo-frame="_top"> Connect </a>
        {% endif %}
        """,
        orderable=False,
    )
    state = PendingStatusColumn(accessor="target_integration")

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        super().__init__(*args, **kwargs)
