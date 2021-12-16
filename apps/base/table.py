import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template

ICONS = {
    "success": "fa-check-circle text-green",
    "error": "fa-times-hexagon text-red",
    "warning": "fa-exclamation-triangle text-orange",
    "loading": "fa-circle-notch fa-spin",
    "info": "fa-info-circle text-blue",
    "pending": "fa-clock",
}


class NaturalDatetimeColumn(tables.Column):
    def render(self, record, table, value, **kwargs):
        context = getattr(table, "context", Context())
        context["datetime"] = value
        return get_template("columns/natural_datetime.html").render(context.flatten())


class NaturalDayColumn(tables.Column):
    def render(self, record, table, value, **kwargs):
        context = getattr(table, "context", Context())
        context["datetime"] = value
        return get_template("columns/natural_day.html").render(context.flatten())


class DuplicateColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object"] = record
        return get_template(self.template_name).render(context.flatten())
