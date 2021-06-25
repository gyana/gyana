import json

from apps.widgets.models import WIDGET_KIND_TO_WEB, Widget
from django.forms.widgets import ChoiceWidget


class VisualSelect(ChoiceWidget):
    class Media:
        js = ("js/templates-bundle.js",)

    template_name = "django/forms/widgets/select_visual.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["selected"] = value
        context["options"] = [
            {
                "id": choice.value,
                "name": choice.label,
                "icon": WIDGET_KIND_TO_WEB[choice.value],
            }
            for choice in Widget.Kind
        ]
        return context
