import django_tables2 as tables
from django.template import Context
from django.template.loader import get_template
from django.utils.html import escape, format_html
from django_tables2.utils import AttributeDict

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


class TemplateColumn(tables.TemplateColumn):
    def render(self, record, table, **kwargs):
        context = getattr(table, "context", Context())
        context["object"] = record
        context.update(self.extra_context)
        return get_template(self.template_name).render(context.flatten())


class FaBooleanColumn(tables.BooleanColumn):
    def __init__(
        self,
        null=False,
        yesno="fa-check-circle text-green,fa-times-hexagon text-black-50",
        **kwargs
    ):
        super().__init__(null, yesno, **kwargs)

    def render(self, value, record, bound_column):
        value = self._get_bool_value(record, value, bound_column)
        icon = self.yesno[int(not value)]
        attrs = {"class": str(value).lower()}
        attrs.update(self.attrs.get("span", {}))

        return format_html(
            "<span {}><i class='fas fa-fw {}'></i></span>",
            AttributeDict(attrs).as_html(),
            escape(icon),
        )
