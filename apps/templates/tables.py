import django_tables2 as tables

from .models import Template


class TemplateTable(tables.Table):
    class Meta:
        model = Template
        attrs = {"class": "table"}
        fields = ("name", "description")

    # need access to team id
    name = tables.TemplateColumn(
        '<a href="{% url "team_templates:detail" team.id record.id %}">{{ record.name }}</a>'
    )
