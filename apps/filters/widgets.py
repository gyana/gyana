from django.forms.widgets import Input, Widget


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
        context["parent_type"] = self.instance.parent_type
        context["parent"] = self.instance.parent.id
        context["selected"] = getattr(self.instance, name.split("-").pop()) or []
        context["column"] = self.column
        return context


# Adding the html with input type="datetime-local" wasn't enoug
# Djangos DatetimeInput already formats the value to a string that is
# Hard to overwrite (basically we would need to hardcode the `T` into the string)
class DatetimeInput(Input):
    input_type = "datetime-local"
    template_name = "django/forms/widgets/input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["value"] = value.isoformat() if value else None
        return context
