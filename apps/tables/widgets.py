from django.forms.widgets import ChoiceWidget


class TableSelect(ChoiceWidget):
    template_name = "django/forms/widgets/table_select.html"

    def __init__(self, attrs=None, choices=(), parent="workflow") -> None:
        super().__init__(attrs, choices)
        self.parent = parent
        self.parent_entity = None  # set in the form

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["parent_entity"] = self.parent_entity
        context["parent"] = self.parent
        return context
