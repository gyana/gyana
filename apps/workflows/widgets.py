import json

from django.forms.widgets import ChoiceWidget


class SourceSelect(ChoiceWidget):
    class Media:
        js = ("js/templates-bundle.js",)

    template_name = "django/forms/widgets/select_source.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {"type": option.source, "id": option.id, "label": option.owner_name}
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = value
        return context
