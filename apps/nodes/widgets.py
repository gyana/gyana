from django.forms.widgets import ChoiceWidget

from apps.widgets.widgets import ICONS


class InputNode(ChoiceWidget):
    template_name = "django/forms/widgets/input_node.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {
                "icon": ICONS[option.source],
                "id": option.id,
                "image": option.integration.icon if option.integration else None,
                "label": option.owner_name,
                "usedInWorkflow": option.used_in_workflow,
            }
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = f"{value}"
        context["widget"]["name"] = name
        return context
