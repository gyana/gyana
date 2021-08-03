from apps.widgets.models import WIDGET_KIND_TO_WEB, Widget
from django.forms.widgets import ChoiceWidget

ICONS = {"integration": "far fa-link", "workflow_node": "far fa-stream"}


class SourceSelect(ChoiceWidget):
    class Media:
        js = ("js/templates-bundle.js",)

    template_name = "django/forms/widgets/select_source.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {"icon": ICONS[option.source], "id": option.id, "label": option.owner_name}
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = value
        context["widget"]["name"] = name
        return context

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
