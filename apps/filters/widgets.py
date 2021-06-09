from django.forms.widgets import Widget


class SelectAutocomplete(Widget):
    class Media:
        js = ("js/templates-bundle.js",)

    template_name = "django/forms/widgets/select_autocomplete.html"

    def __init__(self, attrs, instance, column) -> None:
        super().__init__(attrs=attrs)
        self.instance = instance
        self.column = column

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["filterId"] = self.instance.id
        context["selected"] = getattr(self.instance, name.split("-").pop()) or []
        context["column"] = self.column
        return context
