from crispy_forms.bootstrap import Tab as BaseTab
from crispy_forms.layout import TEMPLATE_PACK
from crispy_forms.layout import Layout as BaseLayout
from crispy_forms.layout import TemplateNameMixin
from django.template.loader import render_to_string


class Tab(BaseTab):
    template = "%s/layout/tab-body.html"


class CrispyFormset(TemplateNameMixin):
    template = "%s/layout/crispy_formset.html"

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def render(self, form, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.get_template_name(template_pack)
        context.update(
            {
                "name": self.name,
                "label": self.label,
                "formset": form.get_formset(self.name, form.formsets[self.name]),
            }
        )

        return render_to_string(template, context.flatten())
