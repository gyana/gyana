from django.forms.widgets import ChoiceWidget

from apps.widgets.formsets import FORMSETS
from apps.widgets.models import WIDGET_KIND_TO_WEB, Widget


class VisualSelect(ChoiceWidget):
    class Media:
        js = ("js/components-bundle.js",)

    template_name = "django/forms/widgets/select_visual.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        MAX_NUMS = {key: formsets[0].max_num for key, formsets in FORMSETS.items()}
        options = [
            {
                "id": choice.value,
                "name": choice.label,
                "icon": WIDGET_KIND_TO_WEB[choice.value][0],
                "maxMetrics": MAX_NUMS.get(choice.value) or -1,
            }
            for choice in Widget.Kind
            if choice.value != Widget.Kind.TEXT
        ]
        context["widget"]["selected"] = next(
            filter(lambda x: x["id"] == value, options)
        )

        context["options"] = options
        return context
