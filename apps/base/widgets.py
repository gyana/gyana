import datetime as dt

from django.forms.widgets import ChoiceWidget, Input, Select

ICONS = {"integration": "far fa-link", "workflow_node": "far fa-stream"}


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


class DatalistInput(Input):
    input_type = "text"
    template_name = "django/forms/widgets/datalist.html"

    def __init__(self, attrs=None, options=()) -> None:
        super().__init__(attrs=attrs)
        self.options = options

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["options"] = self.options
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

    def __init__(self, attrs=None, options=()) -> None:
        super().__init__(attrs=attrs)
        # self.options conflicts with Select methods.
        self.options_ = options

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["options"] = self.options_
        context["widget"]["type"] = self.input_type
        return context


class MultiSelect(ChoiceWidget):
    template_name = "django/forms/widgets/multiple_input.html"
    option_template_name = "django/forms/widgets/gyana_option.html"
    allow_multiple_selected = True

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False


class SourceSelect(ChoiceWidget):
    template_name = "django/forms/widgets/source_select.html"

    def __init__(self, attrs=None, choices=(), parent="workflow") -> None:
        super().__init__(attrs, choices)
        self.parent = parent

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {
                "icon": ICONS[option.source],
                "id": option.id,
                "image": option.integration.icon if option.integration else None,
                "outOfDate": option.out_of_date,
                "label": option.owner_name,
                "usedIn": option.is_used_in,
            }
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = value
        context["widget"]["name"] = name
        context["parent"] = self.parent
        return context
