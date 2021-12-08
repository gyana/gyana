from django.forms.widgets import Widget


class SelectAutocomplete(Widget):
    class Media:
        js = ("js/components-bundle.js",)

    template_name = "django/forms/widgets/select_autocomplete.html"

    def __init__(self, attrs, instance, column) -> None:
        super().__init__(attrs=attrs)
        self.instance = instance
        self.column = column

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["parent_type"] = self.instance.parent_type
        context["parent"] = self.instance.parent.id
        context["selected"] = getattr(self.instance, name.split("-").pop()) or []
        context["column"] = self.column
        return context
