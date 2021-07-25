import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template import Context
from django.template.loader import get_template


class NaturalDatetimeColumn(tables.Column):
    def render(self, value):
        return naturaltime(value)


class DuplicateColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object"] = record
        return get_template(self.template_name).render(context.flatten())
