import django_tables2 as tables
from apps.integrations.models import Integration
from apps.integrations.tables import PendingStatusColumn
from django_tables2.utils import A

from .models import Template, TemplateInstance


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
        sequence = ('template', 'completed')

    template = tables.LinkColumn(
        "project_templateinstances:detail", args=(A("project__id"), A("id"))
    )


class TemplateInstanceSetupTable(tables.Table):
    class Meta:
        attrs = {"class": "table"}

    icon = tables.TemplateColumn(
        '{% load static %}<img class="h-12 w-12 mr-4" src="{% static record.icon %}" title="{{ record.name }}" />'
    )
    name = tables.Column()
    setup = tables.TemplateColumn(
        '<a class="link" href="{{ record.setup }}" data-turbo-frame="_top">Setup</a>'
    )
    # empty column
    state = tables.Column()


class TemplateInstanceIntegrationTable(tables.Table):
    class Meta:
        model = Integration
        fields = ()
        attrs = {"class": "table"}

    icon = tables.TemplateColumn(
        '{% load static %}<img class="h-12 w-12 mr-4" src="{% static record.icon %}" title="{{ record.name }}" />'
    )
    name = tables.Column(accessor="display_kind")
    kind = tables.TemplateColumn(
        '<a class="link" href="{{ record.get_absolute_url}}" data-turbo-frame="_top">View</a>'
    )
    state = PendingStatusColumn()
