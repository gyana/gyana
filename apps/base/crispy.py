from crispy_forms.bootstrap import Tab as BaseTab, TabHolder as BaseTabHolder
from crispy_forms.layout import TEMPLATE_PACK
from crispy_forms.layout import TemplateNameMixin
from django.template.loader import render_to_string


class Tab(BaseTab):
    template = "%s/layout/tab-body.html"


class TabHolder(BaseTabHolder):
    def __init__(self, *args, **kwargs):
        self.tab = kwargs.pop("tab", None)
        super().__init__(*args, **kwargs)

    def open_target_group_for_form(self, form):
        """
        Makes sure that the first group that should be open is open.
        This is either the first group with errors or the first group
        in the container, unless that first group was originally set to
        active=False.
        """
        target = self.first_container_with_errors(form.errors.keys())
        if target is None:
            if self.tab:
                targets = [field for field in self.fields if field.css_id == self.tab]
                if not targets:
                    target = self.fields[0]
            else:
                target = targets[0]

            if not getattr(target, "_active_originally_included", None):
                target.active = True
            return target

        target.active = True
        return target


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
