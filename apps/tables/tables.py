from apps.utils.table import NaturalDatetimeColumn
from django.template import loader
from django.urls import reverse
from django_tables2 import Column
from django_tables2 import Table as DjangoTable

from .models import Table


def get_integration_data_url(record):
    return f"{reverse('project_integrations:data', args=(record.project.id, record.integration.id) )}?table_id={record.id}"


class TableTable(DjangoTable):
    class Meta:
        model = Table
        fields = (
            "bq_table",
            "num_rows",
            "created",
            "updated",
        )
        attrs = {"class": "table"}

    bq_table = Column(
        verbose_name="Name",
        linkify=get_integration_data_url,
        attrs={"a": {"data-turbo-frame": "_top"}},
    )
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    delete = Column(verbose_name="", empty_values=(), orderable=False)

    def render_delete(self, value, record):
        template = loader.get_template("tables/_delete.html")
        return template.render(
            {"object": record, "integration": record.integration}, self.request
        )
