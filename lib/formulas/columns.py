import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template


class DuplicateColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object"] = record
        return get_template(self.template_name).render(context.flatten())
