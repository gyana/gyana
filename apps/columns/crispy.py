from crispy_forms.layout import TEMPLATE_PACK, TemplateNameMixin
from django.template.loader import render_to_string


class ColumnFormatting(TemplateNameMixin):
    template = "%s/layout/column_formatting.html"

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.get_template_name(template_pack)
        context.update(
            {
                "name": form[self.name],
                "columns": [
                    (form[x], form[y])
                    for x, y in zip(self.fields[::2], self.fields[1::2])
                ],
            }
        )
        return render_to_string(template, context.flatten())
