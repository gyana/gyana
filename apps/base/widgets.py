import datetime as dt

from django.forms.widgets import Input, Select


class SelectWithDisable(Select):
    def __init__(
        self,
        disabled,
        attrs=None,
        choices=(),
    ) -> None:
        super().__init__(attrs=attrs, choices=choices)
        self.disabled = disabled

    def get_context(self, name, value, attrs):

        context = super().get_context(name, value, attrs)
        for _, optgroup, __ in context["widget"]["optgroups"]:
            for option in optgroup:
                if (value := option["value"]) in self.disabled:
                    option["attrs"]["disabled"] = True
                    option["attrs"]["title"] = self.disabled[value]
        return context


# Adding the html with input type="datetime-local" wasn't enoug
# Djangos DatetimeInput already formats the value to a string that is
# Hard to overwrite (basically we would need to hardcode the `T` into the string)
class DatetimeInput(Input):
    input_type = "datetime-local"
    template_name = "django/forms/widgets/input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["value"] = (
            value.isoformat() if isinstance(value, dt.datetime) else value
        )
        return context


class Datalist(Select):
    input_type = "text"
    template_name = "django/forms/widgets/datalist.html"
    option_template_name = "django/forms/widgets/datalist_option.html"
    add_id_index = False
    checked_attribute = {"selected": True}
    option_inherits_attrs = False

    def format_value(self, value):
        return value or ""
