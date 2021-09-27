from apps.widgets.widgets import ICONS
from django.forms.widgets import ChoiceWidget


class InputNode(ChoiceWidget):
    template_name = "django/forms/widgets/input_node.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {"icon": ICONS[option.source], "id": option.id, "label": option.owner_name}
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = value
        context["widget"]["name"] = name
        return context


class MultiSelect(ChoiceWidget):
    template_name = "django/forms/widgets/multiple_input.html"
    option_template_name = "django/forms/widgets/gyana_option.html"
    allow_multiple_selected = True

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False
