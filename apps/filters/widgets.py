from django.forms.widgets import Widget


class SelectAutocomplete(Widget):
    class Media:
        js = ("js/components-bundle.js",)

    template_name = "django/forms/widgets/select_autocomplete.html"

    def __init__(self, attrs, parent_type, parent_id, selected) -> None:
        super().__init__(attrs=attrs)
        self.parent_type = parent_type
        self.parent_id = parent_id
        self.selected = selected

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["parent_type"] = self.parent_type
        context["parent"] = self.parent_id
        context["selected"] = self.selected
        return context
