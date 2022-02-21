from django.forms.widgets import ChoiceWidget

from apps.widgets.formsets import FORMSETS
from apps.widgets.models import WIDGET_KIND_TO_WEB, Widget

ICONS = {"integration": "far fa-link", "workflow_node": "far fa-stream"}


class SourceSelect(ChoiceWidget):
    class Media:
        js = ("js/components-bundle.js",)

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
        js = ("js/components-bundle.js",)

    template_name = "django/forms/widgets/select_visual.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["selected"] = value

        MAX_NUMS = {key: formsets[0].max_num for key, formsets in FORMSETS.items()}

        context["options"] = [
            {
                "id": choice.value,
                "name": choice.label,
                "icon": WIDGET_KIND_TO_WEB[choice.value][0],
                "maxMetrics": MAX_NUMS.get(choice.value) or -1,
            }
            for choice in Widget.Kind
            if choice.value != Widget.Kind.TEXT
        ]
        return context
